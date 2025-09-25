import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import CubicSpline
from matplotlib.animation import FuncAnimation

# === Puntos de la ruta 3D ===
ruta = np.array([
    [1, 2, 3],   # P1
    [8, 8, 1],   # P2
    [2, 8, 5],   # P3
    [0, 5, 2]    # P4
])

print("🎯 Puntos objetivo:")
for i, p in enumerate(ruta):
    print(f"   P{i+1} = ({p[0]}, {p[1]}, {p[2]})")

# === Interpolación cúbica suave ===
t_points = np.linspace(0, 1, len(ruta))
t_fine = np.linspace(0, 1, 500)  # alta resolución

cs_x = CubicSpline(t_points, ruta[:, 0], bc_type='natural')
cs_y = CubicSpline(t_points, ruta[:, 1], bc_type='natural')
cs_z = CubicSpline(t_points, ruta[:, 2], bc_type='natural')

x_traj = cs_x(t_fine)
y_traj = cs_y(t_fine)
z_traj = cs_z(t_fine)
trayectoria = np.column_stack([x_traj, y_traj, z_traj])
n_steps = len(trayectoria)

print(f"\n📐 Trayectoria generada: {n_steps} puntos.")

# === Control Inteligente de Estabilidad: Parallel Transport + Up Vector ===
def stable_orientation_frames(path, up_hint=np.array([0, 0, 1])):
    """
    Genera marcos (T, N, B) donde:
      - T: tangente (avance)
      - N: normal principal (lateral/inclinación)
      - B: binormal ≈ 'up' (vertical, como gravedad)
    
    Usa transporte paralelo con corrección suave para mantener B cerca de 'up_hint'.
    """
    T_list = []  # Tangentes
    N_list = []  # Normales (laterales)
    B_list = []  # Binormales ('arriba', casi vertical)

    # Primer vector tangente
    T = path[1] - path[0]
    T = T / (np.linalg.norm(T) + 1e-10)
    T_list.append(T)

    # Inicializar B (arriba) cercano a up_hint, pero perpendicular a T
    B_init = up_hint - np.dot(up_hint, T) * T
    if np.linalg.norm(B_init) < 1e-10:
        aux = np.array([1, 0, 0]) if abs(T[2]) < 0.9 else np.array([0, 1, 0])
        B_init = np.cross(aux, T)
    B_init = B_init / (np.linalg.norm(B_init) + 1e-10)

    # N = B × T (para sistema derecho)
    N_init = np.cross(B_init, T)
    N_init = N_init / (np.linalg.norm(N_init) + 1e-10)

    # Reajustar B para ortogonalidad perfecta
    B_init = np.cross(T, N_init)
    B_init = B_init / (np.linalg.norm(B_init) + 1e-10)

    N_list.append(N_init)
    B_list.append(B_init)

    # Iterar por el resto del camino
    for i in range(1, len(path)):
        dT = path[i] - path[i-1]
        T_new = dT / (np.linalg.norm(dT) + 1e-10)
        T_list.append(T_new)

        # Usar marco anterior para inicializar
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

        # Ajustar signo para continuidad (evitar flips)
        if np.dot(N_candidate, N_prev) < 0:
            N_candidate = -N_candidate

        # Calcular B_candidate = T × N
        B_candidate = np.cross(T_new, N_candidate)
        B_candidate = B_candidate / (np.linalg.norm(B_candidate) + 1e-10)

        # 🔧 CORRECCIÓN DE ESTABILIDAD: mezclar con dirección vertical deseada
        desired_B = up_hint - np.dot(up_hint, T_new) * T_new
        if np.linalg.norm(desired_B) < 1e-10:
            desired_B = np.cross(T_new, np.array([1, 0, 0]))
        desired_B = desired_B / (np.linalg.norm(desired_B) + 1e-10)

        alpha = 0.1  # factor de corrección: 10% hacia arriba
        B_corrected = (1 - alpha) * B_candidate + alpha * desired_B
        B_corrected = B_corrected / (np.linalg.norm(B_corrected) + 1e-10)

        # Recalcular N usando B corregido
        N_corrected = np.cross(B_corrected, T_new)
        N_corrected = N_corrected / (np.linalg.norm(N_corrected) + 1e-10)

        N_list.append(N_corrected)
        B_list.append(B_corrected)

    return T_list, N_list, B_list

# === Generar marcos con estabilidad reforzada ===
T_list, N_list, B_list = stable_orientation_frames(trayectoria)
frames = list(zip(T_list, N_list, B_list))

# === Validación: ángulo entre B y vertical (0,0,1) ===
up_vector = np.array([0, 0, 1])
angles_with_vertical = []
for B in B_list:
    cos_angle = np.clip(np.dot(B, up_vector), -1.0, 1.0)
    angle_deg = np.degrees(np.arccos(cos_angle))
    angles_with_vertical.append(angle_deg)

max_tilt = np.max(angles_with_vertical)
mean_tilt = np.mean(angles_with_vertical)
print(f"\n📈 Orientación del eje 'arriba' (B):")
print(f"  Máxima inclinación respecto a vertical: {max_tilt:.2f}°")
print(f"  Promedio: {mean_tilt:.2f}°")
if max_tilt < 15:
    print("🟢 Excelente estabilidad: nunca se inclina mucho.")
elif max_tilt < 30:
    print("🟡 Aceptable, algo inclinado pero no volcado.")
else:
    print("🔴 Cuidado: riesgo de volteo en algunas curvas.")

# === Gráfico 3D estático con marcos estables ===
fig1 = plt.figure(figsize=(14, 10))
ax = fig1.add_subplot(111, projection='3d')

# Trayectoria
ax.plot(trayectoria[:, 0], trayectoria[:, 1], trayectoria[:, 2], color='magenta', linewidth=2, label='Trayectoria')

# Puntos originales
ax.scatter(ruta[:, 0], ruta[:, 1], ruta[:, 2], color='black', s=120, label='Puntos objetivo')
for i, p in enumerate(ruta):
    ax.text(p[0], p[1], p[2], f'  P{i+1}', fontsize=10, weight='bold')

# Marcos de referencia en puntos clave
step_indices = np.linspace(0, n_steps - 1, 6, dtype=int)
scale_arrow = 0.8

for i in step_indices:
    x, y, z = trayectoria[i]
    T, N, B = frames[i]

    ax.quiver(x, y, z, T[0], T[1], T[2], color='red',   length=scale_arrow, label='X (avance)' if i == step_indices[0] else "")
    ax.quiver(x, y, z, N[0], N[1], N[2], color='green', length=scale_arrow, label='Y (normal)' if i == step_indices[0] else "")
    ax.quiver(x, y, z, B[0], B[1], B[2], color='blue',  length=scale_arrow, label='Z (arriba)' if i == step_indices[0] else "")

ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
ax.set_title('Control Inteligente de Estabilidad\n(B ≈ Vertical | N Lateral)')
ax.legend()
plt.tight_layout()
plt.show()

# === Animación del móvil con estabilidad ===
fig2 = plt.figure(figsize=(12, 9))
ax_anim = fig2.add_subplot(111, projection='3d')

mobile_point, = ax_anim.plot([], [], [], 'o', color='red', ms=10, label='Móvil')
trail_line, = ax_anim.plot([], [], [], color='magenta', linewidth=3, alpha=0.9, label='Estela')
frame_x = frame_y = frame_z = None  # Se crearán dinámicamente

# Fondo: trayectoria débil y puntos
ax_anim.plot(trayectoria[:, 0], trayectoria[:, 1], trayectoria[:, 2], '--', color='gray', alpha=0.4)
ax_anim.scatter(ruta[:, 0], ruta[:, 1], ruta[:, 2], color='black', s=100)
for i, p in enumerate(ruta):
    ax_anim.text(p[0], p[1], p[2], f'  P{i+1}', fontsize=10)

# Configuración del gráfico
ax_anim.set_xlim(trayectoria[:, 0].min() - 1, trayectoria[:, 0].max() + 1)
ax_anim.set_ylim(trayectoria[:, 1].min() - 1, trayectoria[:, 1].max() + 1)
ax_anim.set_zlim(trayectoria[:, 2].min() - 1, trayectoria[:, 2].max() + 1)
ax_anim.set_xlabel('X'); ax_anim.set_ylabel('Y'); ax_anim.set_zlabel('Z')
ax_anim.set_title('Animación: Movimiento con Estabilidad Inercial')
ax_anim.legend()

# Función de animación
def animate(frame_idx):
    global frame_x, frame_y, frame_z
    pos = trayectoria[frame_idx]
    T, N, B = frames[frame_idx]

    # Actualizar posición del móvil
    mobile_point.set_data([pos[0]], [pos[1]])
    mobile_point.set_3d_properties([pos[2]])

    # Actualizar estela
    trail = trayectoria[:frame_idx + 1]
    trail_line.set_data(trail[:, 0], trail[:, 1])
    trail_line.set_3d_properties(trail[:, 2])

    # Eliminar y redibujar flechas del marco
    if frame_x:
        frame_x.remove(); frame_y.remove(); frame_z.remove()

    frame_x = ax_anim.quiver(pos[0], pos[1], pos[2], T[0], T[1], T[2], color='red',   length=scale_arrow)
    frame_y = ax_anim.quiver(pos[0], pos[1], pos[2], N[0], N[1], N[2], color='green', length=scale_arrow)
    frame_z = ax_anim.quiver(pos[0], pos[1], pos[2], B[0], B[1], B[2], color='blue',  length=scale_arrow)

    return mobile_point, trail_line, frame_x, frame_y, frame_z

# Crear animación
ani = FuncAnimation(
    fig2,
    animate,
    frames=n_steps,
    interval=40,           # ~25 fps
    repeat=True,
    blit=False             # quiver no soporta bien blit
)

plt.tight_layout()
plt.show()

# === Opcional: guardar como GIF ===
# Descomenta si quieres guardarlo
# ani.save('movil_estable.gif', writer='pillow', fps=25)
# print("💾 Animación guardada como 'movil_estable.gif'")
