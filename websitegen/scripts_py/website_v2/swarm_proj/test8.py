import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import CubicSpline
from scipy.spatial.transform import Rotation as R
import time

# === CONFIGURACIÓN GENERAL ===
NUM_RUTAS_OBJETIVO = 5          # Cantidad de rutas válidas a generar
MAX_DELTA_ROLL  = 10.0          # Máximo giro por paso [°] (control dinámico)
MAX_DELTA_PITCH = 30.0
MAX_DELTA_YAW   = 45.0

MAX_ABS_ROLL    = 45.0          # Orientación extrema permitida
MAX_ABS_PITCH   = 60.0
MAX_ABS_YAW     = 90.0

n_fine = 400                    # Resolución de la trayectoria interpolada
max_attempts_per_scale = 200    # Intentos por nivel de escala
search_scale = 2.5              # Dispersión inicial de los puntos
min_scale = 0.8                 # Mínima dispersión antes de detenerse
reduction_factor = 0.9          # Factor de reducción de escala

print(f"🎯 Generando {NUM_RUTAS_OBJETIVO} rutas válidas...")
print(f"📏 Escala inicial: ±{search_scale:.1f} m")

# Paleta de colores para diferenciar rutas
colors = [
    'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple',
    'tab:brown', 'tab:pink', 'tab:gray', 'tab:olive', 'tab:cyan'
]


# === FUNCIONES AUXILIARES ===

def generar_puntos_cercanos(centro=None):
    """
    Genera 4 puntos aleatorios cercanos formando una curva natural.
    """
    if centro is None:
        centro = np.array([5.0, 5.0, 2.5])
    
    noise_scale = search_scale
    x = centro[0] + np.random.uniform(-noise_scale, noise_scale, 4)
    y = centro[1] + np.random.uniform(-noise_scale, noise_scale, 4)
    z = centro[2] + np.random.uniform(-noise_scale * 0.6, noise_scale * 0.6, 4)
    z = np.clip(z, 1.0, 6.0)  # Altura segura
    
    ruta = np.column_stack([x, y, z])
    # Pequeña perturbación para evitar simetrías
    ruta += np.random.normal(0, 0.1, ruta.shape)
    
    return ruta


def parallel_transport_frames(path, up_hint=np.array([0, 0, 1])):
    """
    Calcula marcos móviles estables usando transporte paralelo.
    Evita giros bruscos o volteos.
    """
    T_list, N_list, B_list = [], [], []

    # Primer vector tangente
    T = (path[1] - path[0]) / (np.linalg.norm(path[1] - path[0]) + 1e-10)
    T_list.append(T)

    # Inicializar binormal B (arriba) cerca de 'up_hint'
    B_init = up_hint - np.dot(up_hint, T) * T
    if np.linalg.norm(B_init) < 1e-10:
        B_init = np.cross(T, [1, 0, 0])
    B_init = B_init / (np.linalg.norm(B_init) + 1e-10)
    N_init = np.cross(B_init, T)
    N_init = N_init / (np.linalg.norm(N_init) + 1e-10)
    B_init = np.cross(T, N_init)  # re-ortogonalizar
    B_init = B_init / (np.linalg.norm(B_init) + 1e-10)

    N_list.append(N_init)
    B_list.append(B_init)

    for i in range(1, len(path)):
        dT = path[i] - path[i-1]
        T_new = dT / (np.linalg.norm(dT) + 1e-10)
        T_list.append(T_new)

        N_prev = N_list[-1]
        B_prev = B_list[-1]

        # Proyectar N_prev sobre plano perpendicular a T_new
        N_candidate = N_prev - np.dot(N_prev, T_new) * T_new
        norm_N = np.linalg.norm(N_candidate)
        if norm_N < 1e-10:
            aux = np.array([1, 0, 0]) if abs(T_new[0]) < 0.9 else np.array([0, 1, 0])
            N_candidate = np.cross(aux, T_new)
            N_candidate = N_candidate / (np.linalg.norm(N_candidate) + 1e-10)
        else:
            N_candidate = N_candidate / norm_N

        # Ajustar signo para continuidad
        if np.dot(N_candidate, N_prev) < 0:
            N_candidate = -N_candidate

        B_candidate = np.cross(T_new, N_candidate)
        B_candidate = B_candidate / (np.linalg.norm(B_candidate) + 1e-10)

        # Corrección suave hacia vertical
        alpha = 0.1
        desired_B = up_hint - np.dot(up_hint, T_new) * T_new
        desired_B = desired_B / (np.linalg.norm(desired_B) + 1e-10)
        B_corrected = (1 - alpha) * B_candidate + alpha * desired_B
        B_corrected = B_corrected / (np.linalg.norm(B_corrected) + 1e-10)
        N_corrected = np.cross(B_corrected, T_new)
        N_corrected = N_corrected / (np.linalg.norm(N_corrected) + 1e-10)

        N_list.append(N_corrected)
        B_list.append(B_corrected)

    # Retornar lista de tuplas (T, N, B)
    return [(T_list[i], N_list[i], B_list[i]) for i in range(len(T_list))]


def calcular_angulos_absolutos(frames):
    """
    Calcula yaw, pitch, roll absolutos para cada orientación.
    """
    yaw_angles = []
    pitch_angles = []
    roll_angles = []

    for T, N, B in frames:
        # Yaw: dirección horizontal
        yaw = np.arctan2(T[1], T[0])
        yaw_deg = np.degrees(yaw)

        # Pitch: inclinación vertical
        pitch = np.arctan2(T[2], np.hypot(T[0], T[1]))
        pitch_deg = np.degrees(pitch)

        # Roll: inclinación lateral respecto al horizonte local
        up_proj = np.array([0, 0, 1]) - np.dot(np.array([0, 0, 1]), T) * T
        if np.linalg.norm(up_proj) > 1e-10:
            up_proj = up_proj / np.linalg.norm(up_proj)
            cos_roll = np.clip(np.dot(N, up_proj), -1.0, 1.0)
            sign = np.sign(np.dot(np.cross(N, up_proj), T))
            roll_rad = np.arccos(cos_roll) * sign
            roll_deg = np.degrees(roll_rad)
        else:
            roll_deg = 0.0

        yaw_angles.append(yaw_deg)
        pitch_angles.append(pitch_deg)
        roll_angles.append(roll_deg)

    return np.array(yaw_angles), np.array(pitch_angles), np.array(roll_angles)


def validar_trayectoria(ruta):
    """
    Valida si una ruta cumple con todas las restricciones.
    Retorna True + métricas si es válida.
    """
    t_points = np.linspace(0, 1, len(ruta))
    t_fine = np.linspace(0, 1, n_fine)

    try:
        cs_x = CubicSpline(t_points, ruta[:, 0], bc_type='natural')
        cs_y = CubicSpline(t_points, ruta[:, 1], bc_type='natural')
        cs_z = CubicSpline(t_points, ruta[:, 2], bc_type='natural')

        trayectoria = np.column_stack([cs_x(t_fine), cs_y(t_fine), cs_z(t_fine)])
    except:
        return False, None, None

    # Calcular marcos estables
    try:
        frames = parallel_transport_frames(trayectoria)
    except Exception as e:
        return False, None, None

    # Ángulos absolutos
    yaw_abs, pitch_abs, roll_abs = calcular_angulos_absolutos(frames)

    max_abs_roll = np.max(np.abs(roll_abs))
    max_abs_pitch = np.max(np.abs(pitch_abs))
    max_abs_yaw = np.max(np.abs(yaw_abs))

    # Ángulos relativos entre pasos consecutivos
    delta_roll = [0.0]
    delta_pitch = [0.0]
    delta_yaw = [0.0]

    for i in range(1, len(frames)):
        T_prev, N_prev, B_prev = frames[i-1]
        T_curr, N_curr, B_curr = frames[i]

        R_prev = np.column_stack([T_prev, N_prev, B_prev])
        R_curr = np.column_stack([T_curr, N_curr, B_curr])
        R_rel = R_curr @ R_prev.T

        euler_rel = R.from_matrix(R_rel).as_euler('xyz', degrees=True)
        delta_roll.append(euler_rel[0])
        delta_pitch.append(euler_rel[1])
        delta_yaw.append(euler_rel[2])

    delta_roll = np.array(delta_roll)
    delta_pitch = np.array(delta_pitch)
    delta_yaw = np.array(delta_yaw)

    max_delta_roll = np.max(np.abs(delta_roll))
    max_delta_pitch = np.max(np.abs(delta_pitch))
    max_delta_yaw = np.max(np.abs(delta_yaw))

    # Verificar todas las condiciones
    cumple_delta = (
        max_delta_roll <= MAX_DELTA_ROLL and
        max_delta_pitch <= MAX_DELTA_PITCH and
        max_delta_yaw <= MAX_DELTA_YAW
    )
    cumple_abs = (
        max_abs_roll <= MAX_ABS_ROLL and
        max_abs_pitch <= MAX_ABS_PITCH and
        max_abs_yaw <= MAX_ABS_YAW
    )

    if cumple_delta and cumple_abs:
        metrics = {
            'delta': (max_delta_roll, max_delta_pitch, max_delta_yaw),
            'abs': (max_abs_roll, max_abs_pitch, max_abs_yaw),
            'trayectoria': trayectoria,
            'frames': frames,
            'ruta': ruta.copy()
        }
        return True, ruta, metrics
    else:
        return False, None, None


# === BUCLE PRINCIPAL: GENERAR MÚLTIPLES RUTAS VÁLIDAS ===
rutas_validas = []  # Almacena métricas completas
intentos_totales = 0
start_time = time.time()

print(f"\n🚀 Iniciando búsqueda de {NUM_RUTAS_OBJETIVO} rutas válidas...\n")

while len(rutas_validas) < NUM_RUTAS_OBJETIVO:
    print(f"🔍 Buscando ruta #{len(rutas_validas)+1}/{NUM_RUTAS_OBJETIVO}")
    scale = search_scale
    encontrado = False

    while scale >= min_scale and not encontrado:
        print(f"  ⚙️  Probando con dispersión ±{scale:.2f} m", end="")

        intentos_escalado = 0
        while intentos_escalado < max_attempts_per_scale and not encontrado:
            intentos_totales += 1
            intentos_escalado += 1

            ruta_propuesta = generar_puntos_cercanos()
            valido, _, metrics = validar_trayectoria(ruta_propuesta)

            if valido:
                rutas_validas.append(metrics)
                encontrado = True
                print(f" → ✅ Encontrada!")
        
        if not encontrado:
            scale *= reduction_factor
            print(f" → 🔁 Reduciendo a ±{scale:.2f} m")

    if not encontrado:
        print(f"❌ No se encontró más rutas tras reducir escala.")
        break

end_time = time.time()


# === RESUMEN FINAL ===
print("\n" + "="*60)
print("✅ RESULTADO FINAL")
print("="*60)
print(f"Rutas generadas: {len(rutas_validas)} / {NUM_RUTAS_OBJETIVO}")
print(f"Intentos totales: {intentos_totales}")
print(f"Tiempo total: {end_time - start_time:.2f} segundos")

if len(rutas_validas) == 0:
    print("❌ No se encontró ninguna ruta válida.")
    exit()

# Detalles por ruta
for idx, r in enumerate(rutas_validas):
    dr, dp, dy = r['delta']
    ar, ap, ay = r['abs']
    print(f"\n--- Ruta {idx+1} ---")
    print(f"  Rotaciones entre pasos:")
    print(f"    ΔRoll={dr:6.2f}° ≤ 10° → ✅")
    print(f"    ΔPitch={dp:6.2f}° ≤ 30° → ✅")
    print(f"    ΔYaw={dy:6.2f}° ≤ 45° → ✅")
    print(f"  Orientación máxima absoluta:")
    print(f"    Roll={ar:6.2f}° ≤ 45° → {'✅' if ar <= 45 else '⚠️'}")
    print(f"    Pitch={ap:6.2f}° ≤ 60° → {'✅' if ap <= 60 else '⚠️'}")
    print(f"    Yaw={ay:6.2f}° ≤ 90° → {'✅' if ay <= 90 else '⚠️'}")
    print("  Puntos (x, y, z):")
    for i, p in enumerate(r['ruta']):
        print(f"    P{i+1}: ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})")


# === GRÁFICO 3D: TODAS LAS RUTAS ===
fig = plt.figure(figsize=(14, 10))
ax = fig.add_subplot(111, projection='3d')

for i, ruta_data in enumerate(rutas_validas):
    trayectoria = ruta_data['trayectoria']
    puntos = ruta_data['ruta']
    color = colors[i % len(colors)]

    # Dibujar trayectoria
    ax.plot(trayectoria[:, 0], trayectoria[:, 1], trayectoria[:, 2],
            color=color, linewidth=2.5, label=f'Ruta {i+1}')

    # Dibujar puntos
    ax.scatter(puntos[:, 0], puntos[:, 1], puntos[:, 2],
               color=color, s=100, edgecolor='k', zorder=10)

    # Etiquetas
    for j, p in enumerate(puntos):
        ax.text(p[0], p[1], p[2], f'  {i+1}.{j+1}', fontsize=9,
                color=color, weight='bold')

ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
ax.set_title(f'Múltiples rutas válidas generadas\n({len(rutas_validas)} rutas cumplen todas las restricciones)')
ax.legend()
plt.tight_layout()
plt.show()


# === EXPORTAR A CSV (OPCIONAL) ===
export_csv = True  # Cambia a False si no quieres guardar

if export_csv:
    import pandas as pd
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"rutas_validas_{timestamp}.csv"

    rows = []
    for idx, r in enumerate(rutas_validas):
        for step, point in enumerate(r['trayectoria']):
            rows.append({
                'ruta_id': idx + 1,
                'paso': step,
                'x': point[0],
                'y': point[1],
                'z': point[2],
                'distancia_acum': np.linalg.norm(point) if step == 0 else 0  # placeholder
            })
    df = pd.DataFrame(rows)
    df.to_csv(filename, index=False)
    print(f"\n💾 Datos exportados a '{filename}'")

print("\n🎉 ¡Proceso completado!")
