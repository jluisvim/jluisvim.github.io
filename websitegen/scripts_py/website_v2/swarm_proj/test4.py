import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from scipy.spatial.transform import Rotation as R
from matplotlib.animation import FuncAnimation

def distancia(p1, p2):
    return np.linalg.norm(np.array(p2) - np.array(p1))

# === Definir la ruta: lista de puntos en 3D ===
ruta = [
    (1, 2, 3),   # P1
    (4, 6, 4),   # P2
    (2, 8, 5),   # P3
    (0, 5, 2)    # P4
]

print(f"Ruta definida con {len(ruta)} puntos:")
for i, p in enumerate(ruta):
    print(f"  P{i+1} = {p}")

# === Generar trayectorias y marcos para cada segmento ===
trayectorias = []        # Lista de arrays [x, y, z] por paso
marcos_referencia = []   # Marcos T, N, B por paso
n_steps_per_segment = 100

for seg in range(len(ruta) - 1):
    p1 = np.array(ruta[seg])
    p2 = np.array(ruta[seg + 1])

    # Centro y radio del cilindro
    xm = (p1[0] + p2[0]) / 2
    ym = (p1[1] + p2[1]) / 2
    radio = distancia(p1[:2], p2[:2]) / 2

    # Ángulos azimutales
    theta1 = np.arctan2(p1[1] - ym, p1[0] - xm)
    theta2 = np.arctan2(p2[1] - ym, p2[0] - xm)

    # Ajuste de ángulo
    if theta2 - theta1 > np.pi:
        theta2 -= 2 * np.pi
    elif theta1 - theta2 > np.pi:
        theta1 -= 2 * np.pi

    t = np.linspace(0, 1, n_steps_per_segment)
    theta_t = theta1 + t * (theta2 - theta1)
    z_t = p1[2] + t * (p2[2] - p1[2])
    x_t = xm + radio * np.cos(theta_t)
    y_t = ym + radio * np.sin(theta_t)

    trayectoria = np.column_stack([x_t, y_t, z_t])
    trayectorias.append(trayectoria)

    # Calcular marcos de referencia
    frames = []
    for i in range(n_steps_per_segment):
        x, y, z = trayectoria[i]

        # Tangente
        if i == 0:
            dt = trayectoria[1] - trayectoria[0]
        elif i == n_steps_per_segment - 1:
            dt = trayectoria[-1] - trayectoria[-2]
        else:
            dt = trayectoria[i+1] - trayectoria[i-1]
        T = dt / (np.linalg.norm(dt) + 1e-8)

        # Normal radial
        dn = np.array([x - xm, y - ym, 0])
        N = dn / (np.linalg.norm(dn) + 1e-8)

        # Binormal
        B = np.cross(T, N)
        B = B / (np.linalg.norm(B) + 1e-8)
        N = np.cross(B, T)
        N = N / (np.linalg.norm(N) + 1e-8)

        frames.append(np.column_stack([T, N, B]))
    marcos_referencia.append(frames)

# Concatenar todas las trayectorias
trayectoria_total = np.concatenate(trayectorias)
marcos_total = []
for frames in marcos_referencia:
    marcos_total.extend(frames)
total_steps = len(trayectoria_total)

# === Configurar figura para animación ===
fig = plt.figure(figsize=(12, 9))
ax = fig.add_subplot(111, projection='3d')

# Dibujar cilindros
colors_cyl = ['cyan', 'yellow', 'lightgreen']
for seg in range(len(ruta) - 1):
    p1 = np.array(ruta[seg])
    p2 = np.array(ruta[seg + 1])
    xm = (p1[0] + p2[0]) / 2
    ym = (p1[1] + p2[1]) / 2
    radio = distancia(p1[:2], p2[:2]) / 2
    z_min = min(p1[2], p2[2])
    z_max = max(p1[2], p2[2])

    theta_circ = np.linspace(0, 2 * np.pi, 50)
    x_inf = xm + radio * np.cos(theta_circ)
    y_inf = ym + radio * np.sin(theta_circ)
    z_inf = np.full_like(theta_circ, z_min)
    x_sup = xm + radio * np.cos(theta_circ)
    y_sup = ym + radio * np.sin(theta_circ)
    z_sup = np.full_like(theta_circ, z_max)

    verts = [[
        [x_inf[i], y_inf[i], z_inf[i]],
        [x_inf[(i+1)%50], y_inf[(i+1)%50], z_inf[(i+1)%50]],
        [x_sup[(i+1)%50], y_sup[(i+1)%50], z_sup[(i+1)%50]],
        [x_sup[i], y_sup[i], z_sup[i]]
    ] for i in range(50)]

    cyl = Poly3DCollection(verts, alpha=0.1, facecolor=colors_cyl[seg % len(colors_cyl)],
                           edgecolor='gray', linewidth=0.5)
    ax.add_collection3d(cyl)

# Dibujar puntos fijos
for i, p in enumerate(ruta):
    ax.scatter(p[0], p[1], p[2], color='black', s=100)
    ax.text(p[0], p[1], p[2], f'  P{i+1}', fontsize=10)

# Inicializar elementos móviles
mobile_point, = ax.plot([], [], [], 'o', color='red', ms=10)
trail_line, = ax.plot([], [], [], color='magenta', linewidth=2, alpha=0.8)
frame_x = ax.quiver(0, 0, 0, 0, 0, 0, color='red',   length=0.8, label='X (avance)')
frame_y = ax.quiver(0, 0, 0, 0, 0, 0, color='green', length=0.8, label='Y (radial)')
frame_z = ax.quiver(0, 0, 0, 0, 0, 0, color='blue',  length=0.8, label='Z (binormal)')

# Límites
all_points = np.array(ruta)
ax.set_xlim(all_points[:,0].min() - 2, all_points[:,0].max() + 2)
ax.set_ylim(all_points[:,1].min() - 2, all_points[:,1].max() + 2)
ax.set_zlim(all_points[:,2].min() - 1, all_points[:,2].max() + 1)
ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
ax.set_title('Animación: Movil sobre superficie de cilindros')
ax.legend()

# === Función de animación ===
def animate(frame_idx):
    # Posición actual
    pos = trayectoria_total[frame_idx]
    frame_local = marcos_total[frame_idx]

    # Actualizar punto móvil
    mobile_point.set_data([pos[0]], [pos[1]])
    mobile_point.set_3d_properties([pos[2]])

    # Actualizar estela (trayectoria recorrida)
    trail = trayectoria_total[:frame_idx+1]
    trail_line.set_data(trail[:,0], trail[:,1])
    trail_line.set_3d_properties(trail[:,2])

    # Actualizar marco de referencia
    global frame_x, frame_y, frame_z
    frame_x.remove(); frame_y.remove(); frame_z.remove()

    T, N, B = frame_local[:,0], frame_local[:,1], frame_local[:,2]
    frame_x = ax.quiver(pos[0], pos[1], pos[2], T[0], T[1], T[2], color='red',   length=0.8)
    frame_y = ax.quiver(pos[0], pos[1], pos[2], N[0], N[1], N[2], color='green', length=0.8)
    frame_z = ax.quiver(pos[0], pos[1], pos[2], B[0], B[1], B[2], color='blue',  length=0.8)

    return mobile_point, trail_line, frame_x, frame_y, frame_z

# === Crear animación ===
ani = FuncAnimation(
    fig, animate, frames=total_steps,
    interval=50,  # ms entre frames
    repeat=True,
    blit=False  # necesario por cómo se actualizan quivers
)

plt.tight_layout()
plt.show()
