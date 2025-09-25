import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import CubicSpline
from scipy.spatial.transform import Rotation as R
import time

# === CONFIGURACIÓN DE RESTRICCIONES ===
MAX_DELTA_ROLL  = 10.0   # Máximo giro por paso (control dinámico)
MAX_DELTA_PITCH = 30.0
MAX_DELTA_YAW   = 45.0

MAX_ABS_ROLL    = 45.0   # Orientación extrema permitida
MAX_ABS_PITCH   = 60.0
MAX_ABS_YAW     = 90.0

# Parámetros
n_fine = 400           # puntos en la trayectoria interpolada
max_attempts = 300     # intentos antes de reducir escala
search_scale = 2.5     # dispersión inicial de puntos
min_scale = 0.8        # mínima dispersión
reduction_factor = 0.9 # reducción si no encuentra solución

print("🔧 Generador automático de 4 puntos con trayectoria física válida")
print(f"📏 Escala inicial: ±{search_scale:.1f} m")

def generar_puntos_cercanos(centro=None):
    """Genera 4 puntos cercanos formando una curva suave."""
    if centro is None:
        centro = np.array([5.0, 5.0, 2.5])
    
    # Generar desplazamientos pequeños
    noise_scale = search_scale
    x = centro[0] + np.random.uniform(-noise_scale, noise_scale, 4)
    y = centro[1] + np.random.uniform(-noise_scale, noise_scale, 4)
    z = centro[2] + np.random.uniform(-noise_scale * 0.6, noise_scale * 0.6, 4)
    z = np.clip(z, 1.0, 6.0)  # altura segura
    
    # Asegurar que no sean colineales
    ruta = np.column_stack([x, y, z])
    
    # Pequeña perturbación adicional para evitar planos perfectos
    ruta += np.random.normal(0, 0.1, ruta.shape)
    
    return ruta

def parallel_transport_frames(path, up_hint=np.array([0, 0, 1])):
    """Calcula marcos móviles estables sin giros bruscos."""
    T_list, N_list, B_list = [], [], []

    # Primer tangente
    T = path[1] - path[0]
    T = T / (np.linalg.norm(T) + 1e-10)
    T_list.append(T)

    # Inicializar B (arriba) cerca de 'up_hint'
    B_init = up_hint - np.dot(up_hint, T) * T
    if np.linalg.norm(B_init) < 1e-10:
        B_init = np.cross(T, [1, 0, 0])
    B_init = B_init / (np.linalg.norm(B_init) + 1e-10)
    N_init = np.cross(B_init, T)
    N_init = N_init / (np.linalg.norm(N_init) + 1e-10)
    B_init = np.cross(T, N_init)
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
            aux = [1,0,0] if abs(T_new[0]) < 0.9 else [0,1,0]
            N_candidate = np.cross(aux, T_new)
            N_candidate = N_candidate / (np.linalg.norm(N_candidate) + 1e-10)
        else:
            N_candidate = N_candidate / norm_N

        if np.dot(N_candidate, N_prev) < 0:
            N_candidate = -N_candidate

        B_candidate = np.cross(T_new, N_candidate)
        B_candidate = B_candidate / (np.linalg.norm(B_candidate) + 1e-10)

        # Corrección suave hacia arriba
        alpha = 0.1
        desired_B = up_hint - np.dot(up_hint, T_new) * T_new
        desired_B = desired_B / (np.linalg.norm(desired_B) + 1e-10)
        B_corrected = (1-alpha)*B_candidate + alpha*desired_B
        B_corrected = B_corrected / (np.linalg.norm(B_corrected) + 1e-10)
        N_corrected = np.cross(B_corrected, T_new)
        N_corrected = N_corrected / (np.linalg.norm(N_corrected) + 1e-10)

        N_list.append(N_corrected)
        B_list.append(B_corrected)

    return [(T_list[i], N_list[i], B_list[i]) for i in range(len(T_list))]

def calcular_angulos_absolutos(frames):
    """Devuelve yaw, pitch, roll absolutos en grados."""
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

        # Roll: inclinación lateral respecto al plano horizontal
        up_proj = np.array([0, 0, 1]) - np.dot([0, 0, 1], T) * T
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
    """Valida que la trayectoria cumpla todas las restricciones."""
    t_points = np.linspace(0, 1, len(ruta))
    t_fine = np.linspace(0, 1, n_fine)

    cs_x = CubicSpline(t_points, ruta[:, 0], bc_type='natural')
    cs_y = CubicSpline(t_points, ruta[:, 1], bc_type='natural')
    cs_z = CubicSpline(t_points, ruta[:, 2], bc_type='natural')

    trayectoria = np.column_stack([cs_x(t_fine), cs_y(t_fine), cs_z(t_fine)])

    # Calcular marcos estables
    try:
        frames = parallel_transport_frames(trayectoria)
    except:
        return False, None, None

    # Ángulos absolutos
    yaw_abs, pitch_abs, roll_abs = calcular_angulos_absolutos(frames)

    max_abs_roll = np.max(np.abs(roll_abs))
    max_abs_pitch = np.max(np.abs(pitch_abs))
    max_abs_yaw = np.max(np.abs(yaw_abs))

    # Ángulos relativos (entre pasos)
    delta_roll = [0.0]
    delta_pitch = [0.0]
    delta_yaw = [0.0]

    for i in range(1, len(frames)):
        T_prev, N_prev, B_prev = frames[i-1]
        T_curr, N_curr, B_curr = frames[i]

        R_prev = np.column_stack([T_prev, N_prev, B_prev])
        R_curr = np.column_stack([T_curr, N_curr, B_curr])
        R_rel = R_curr @ R_prev.T

        euler = R.from_matrix(R_rel).as_euler('xyz', degrees=True)
        delta_roll.append(euler[0])
        delta_pitch.append(euler[1])
        delta_yaw.append(euler[2])

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
            'frames': frames
        }
        return True, ruta, metrics
    else:
        return False, None, None

# === Bucle principal: encontrar ruta válida ===
ruta_encontrada = None
intentos_totales = 0
start_time = time.time()

while search_scale >= min_scale and ruta_encontrada is None:
    print(f"\n🔍 Buscando con dispersión ±{search_scale:.2f} m...")

    for attempt in range(max_attempts):
        intentos_totales += 1
        ruta_propuesta = generar_puntos_cercanos()
        
        valido, ruta_ok, metrics = validar_trayectoria(ruta_propuesta)
        
        if valido:
            ruta_encontrada = ruta_propuesta
            break
    
    if ruta_encontrada is None:
        search_scale *= reduction_factor
        print(f"🔁 Reduciendo escala a ±{search_scale:.2f} m")

end_time = time.time()

if ruta_encontrada is not None:
    print(f"\n✅ ¡Éxito! Ruta válida encontrada después de {intentos_totales} intentos.")
    print(f"⏱️  Tiempo total: {end_time - start_time:.2f} segundos\n")
    
    # Mostrar resultados
    _, _, metrics = validar_trayectoria(ruta_encontrada)
    dr, dp, dy = metrics['delta']
    ar, ap, ay = metrics['abs']
    
    print("📊 Rotaciones máximas entre pasos:")
    print(f"  ΔRoll  (X): {dr:6.2f}° ≤ {MAX_DELTA_ROLL}° → {'✅'}")
    print(f"  ΔPitch (Y): {dp:6.2f}° ≤ {MAX_DELTA_PITCH}° → {'✅'}")
    print(f"  ΔYaw   (Z): {dy:6.2f}° ≤ {MAX_DELTA_YAW}° → {'✅'}")
    
    print("\n📈 Orientación máxima absoluta:")
    print(f"  Roll  (X): {ar:6.2f}° ≤ {MAX_ABS_ROLL}° → {'✅' if ar <= MAX_ABS_ROLL else '⚠️'}")
    print(f"  Pitch (Y): {ap:6.2f}° ≤ {MAX_ABS_PITCH}° → {'✅' if ap <= MAX_ABS_PITCH else '⚠️'}")
    print(f"  Yaw   (Z): {ay:6.2f}° ≤ {MAX_ABS_YAW}° → {'✅' if ay <= MAX_ABS_YAW else '⚠️'}")
    
    print("\n📌 Puntos generados:")
    for i, p in enumerate(ruta_encontrada):
        print(f"   P{i+1} = ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})")
    
    # Gráfico
    trayectoria = metrics['trayectoria']
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(trayectoria[:,0], trayectoria[:,1], trayectoria[:,2], 'm-', lw=2, label='Trayectoria')
    ax.scatter(ruta_encontrada[:,0], ruta_encontrada[:,1], ruta_encontrada[:,2], c='blue', s=100, label='Waypoints')
    for i, p in enumerate(ruta_encontrada):
        ax.text(p[0], p[1], p[2], f'  P{i+1}', fontsize=10)
    ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
    ax.set_title('Ruta válida generada automáticamente')
    ax.legend()
    plt.tight_layout()
    plt.show()
else:
    print(f"\n❌ No se encontró ninguna ruta válida incluso con escala mínima ({min_scale}).")
    print("💡 Sugerencia: relaja ligeramente las restricciones o aumenta max_attempts.")
