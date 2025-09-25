import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np
from scipy.spatial.transform import Rotation as R

def distancia(p1, p2):
    """Calcula la distancia euclidiana entre dos puntos."""
    return np.linalg.norm(np.array(p2) - np.array(p1))

# === Puntos iniciales en 3D ===
punto1 = (1, 2, 3)
punto2 = (2, 6, 1)

# Geometría del cilindro
xm = (punto1[0] + punto2[0]) / 2  # centro en XY
ym = (punto1[1] + punto2[1]) / 2
radio = distancia(punto1[:2], punto2[:2]) / 2  # radio basado en proyección XY

z_min = min(punto1[2], punto2[2])
z_max = max(punto1[2], punto2[2])

print(f"Punto 1: {punto1}")
print(f"Punto 2: {punto2}")
print(f"Centro del cilindro (X,Y): ({xm:.2f}, {ym:.2f})")
print(f"Radio del cilindro: {radio:.2f}")

# === Generar superficie lateral del cilindro ===
theta_circ = np.linspace(0, 2 * np.pi, 50)
x_inf = xm + radio * np.cos(theta_circ)
y_inf = ym + radio * np.sin(theta_circ)
z_inf = np.full_like(theta_circ, z_min)
x_sup = xm + radio * np.cos(theta_circ)
y_sup = ym + radio * np.sin(theta_circ)
z_sup = np.full_like(theta_circ, z_max)

verts = []
for i in range(len(theta_circ)):
    verts.append([
        [x_inf[i], y_inf[i], z_inf[i]],
        [x_inf[(i+1) % len(theta_circ)], y_inf[(i+1) % len(theta_circ)], z_inf[(i+1) % len(theta_circ)]],
        [x_sup[(i+1) % len(theta_circ)], y_sup[(i+1) % len(theta_circ)], z_sup[(i+1) % len(theta_circ)]],
        [x_sup[i], y_sup[i], z_sup[i]]
    ])
lateral = Poly3DCollection(verts, alpha=0.2, color='cyan', edgecolor='gray', linewidth=0.3)

# === Generar trayectoria sobre la superficie del cilindro ===
n_steps = 100
t = np.linspace(0, 1, n_steps)

# Ángulos azimutales de P1 y P2 respecto al centro
theta1 = np.arctan2(punto1[1] - ym, punto1[0] - xm)
theta2 = np.arctan2(punto2[1] - ym, punto2[0] - xm)

# Ajuste para evitar saltos de 2π
if theta2 - theta1 > np.pi:
    theta2 -= 2 * np.pi
elif theta1 - theta2 > np.pi:
    theta1 -= 2 * np.pi

# Interpolación suave
theta_t = theta1 + t * (theta2 - theta1)
z_t = punto1[2] + t * (punto2[2] - punto1[2])
x_t = xm + radio * np.cos(theta_t)
y_t = ym + radio * np.sin(theta_t)

# === Calcular marcos de referencia (T, N, B) en cada paso ===
frames = []  # Lista de matrices de rotación: [T, N, B]

for i in range(n_steps):
    x = x_t[i]
    y = y_t[i]
    z = z_t[i]

    # Tangente T: dirección del movimiento (diferencia centrada)
    if i == 0:
        dt = np.array([x_t[1] - x_t[0], y_t[1] - y_t[0], z_t[1] - z_t[0]])
    elif i == n_steps - 1:
        dt = np.array([x_t[-1] - x_t[-2], y_t[-1] - y_t[-2], z_t[-1] - z_t[-2]])
    else:
        dt = np.array([x_t[i+1] - x_t[i-1], y_t[i+1] - y_t[i-1], z_t[i+1] - z_t[i-1]])
    T = dt / (np.linalg.norm(dt) + 1e-8)

    # Normal N: radial en XY (fuera del cilindro)
    dn = np.array([x - xm, y - ym, 0])
    N = dn / (np.linalg.norm(dn) + 1e-8)

    # Binormal B = T × N (completa sistema derecho)
    B = np.cross(T, N)
    B = B / (np.linalg.norm(B) + 1e-8)

    # Reajustar N para asegurar ortogonalidad exacta
    N = np.cross(B, T)
    N = N / (np.linalg.norm(N) + 1e-8)

    # Matriz de rotación: columnas son ejes locales: X=T, Y=N, Z=B
    R_local_to_global = np.column_stack([T, N, B])
    frames.append(R_local_to_global)

# === Calcular ángulos de rotación RELATIVA entre pasos consecutivos ===
angles_x = [0.0]  # delta_roll  (rotación en X)
angles_y = [0.0]  # delta_pitch (rotación en Y)
angles_z = [0.0]  # delta_yaw   (rotación en Z)

for i in range(1, n_steps):
    R_prev = frames[i-1]
    R_curr = frames[i]

    # Rotación relativa: R_rel tal que R_curr = R_rel @ R_prev
    R_rel_matrix = R_curr @ R_prev.T

    # Convertir a ángulos de Euler (orden: rotación local X → Y → Z)
    r = R.from_matrix(R_rel_matrix)
    euler_deg = r.as_euler('xyz', degrees=True)  # [roll, pitch, yaw] en grados

    angles_x.append(euler_deg[0])
    angles_y.append(euler_deg[1])
    angles_z.append(euler_deg[2])

angles_x = np.array(angles_x)
angles_y = np.array(angles_y)
angles_z = np.array(angles_z)

# === Calcular orientación ABSOLUTA en cada paso ===
abs_yaw = []   # Dirección horizontal (respecto al eje X global)
abs_pitch = [] # Inclinación vertical del vector avance
abs_roll = []  # Inclinación lateral estimada

for i in range(n_steps):
    T, N, B = frames[i][:, 0], frames[i][:, 1], frames[i][:, 2]

    # Yaw absoluto: ángulo del vector T en el plano XY
    yaw = np.degrees(np.arctan2(T[1], T[0]))
    
    # Pitch absoluto: inclinación hacia arriba/abajo
    pitch = np.degrees(np.arctan2(T[2], np.hypot(T[0], T[1])))
    
    # Roll absoluto: basado en componente vertical del binormal B
    roll = np.degrees(np.arctan2(-T[0]*B[1] + T[1]*B[0], np.hypot(T[0], T[1])))  # simplificado

    abs_yaw.append(yaw)
    abs_pitch.append(pitch)
    abs_roll.append(roll)

abs_yaw = np.array(abs_yaw)
abs_pitch = np.array(abs_pitch)
abs_roll = np.array(abs_roll)

# === Validación de restricciones máximas entre pasos ===
max_roll  = np.max(np.abs(angles_x))
max_pitch = np.max(np.abs(angles_y))
max_yaw   = np.max(np.abs(angles_z))

print(f"\n🔍 Máxima rotación entre pasos:")
print(f"  ΔRoll  (X): {max_roll:.2f}° ≤ 10° → {'✅' if max_roll <= 10 else '❌'}")
print(f"  ΔPitch (Y): {max_pitch:.2f}° ≤ 30° → {'✅' if max_pitch <= 30 else '❌'}")
print(f"  ΔYaw   (Z): {max_yaw:.2f}° ≤ 45° → {'✅' if max_yaw <= 45 else '❌'}")

# === Gráfico 1: 3D con trayectoria y marcos de referencia ===
fig1 = plt.figure(figsize=(16, 9))

ax1 = fig1.add_subplot(221, projection='3d')
ax1.add_collection3d(lateral)
ax1.plot(x_t, y_t, z_t, color='magenta', linewidth=2, label='Trayectoria')

# Puntos inicial y final
ax1.scatter(punto1[0], punto1[1], punto1[2], color='blue', s=100, label='P1')
ax1.scatter(punto2[0], punto2[1], punto2[2], color='red', s=100, label='P2')
ax1.text(punto1[0], punto1[1], punto1[2], "  P1", color='blue', fontsize=9)
ax1.text(punto2[0], punto2[1], punto2[2], "  P2", color='red', fontsize=9)

# Marcos de referencia en puntos clave
frame_indices = [0, 25, 50, 75, 99]
scale_arrow = 0.7

for i in frame_indices:
    x, y, z = x_t[i], y_t[i], z_t[i]
    T, N, B = frames[i][:, 0], frames[i][:, 1], frames[i][:, 2]
    
    ax1.quiver(x, y, z, T[0], T[1], T[2], color='red',   length=scale_arrow, arrow_length_ratio=0.3,
               label='X (avance)' if i == 0 else "")
    ax1.quiver(x, y, z, N[0], N[1], N[2], color='green', length=scale_arrow, arrow_length_ratio=0.3,
               label='Y (radial)' if i == 0 else "")
    ax1.quiver(x, y, z, B[0], B[1], B[2], color='blue',  length=scale_arrow, arrow_length_ratio=0.3,
               label='Z (binormal)' if i == 0 else "")

ax1.set_title('Trayectoria sobre cilindro + Marcos de referencia')
ax1.set_xlabel('X'); ax1.set_ylabel('Y'); ax1.set_zlabel('Z')
ax1.legend()

# --- Subplots 2, 3, 4: rotaciones relativas ---
steps = np.arange(n_steps)

plt.subplot(2, 2, 2)
plt.plot(steps, angles_z, 'purple', linewidth=2, label='ΔYaw (Z)')
plt.axhline(45, color='r', ls='--', alpha=0.7); plt.axhline(-45, color='r', ls='--', alpha=0.7)
plt.fill_between(steps, -45, 45, color='lightcoral', alpha=0.2)
plt.title('Rotación entre pasos: Yaw (Z)')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True); plt.legend()

plt.subplot(2, 2, 3)
plt.plot(steps, angles_y, 'orange', linewidth=2, label='ΔPitch (Y)')
plt.axhline(30, color='r', ls='--', alpha=0.7); plt.axhline(-30, color='r', ls='--', alpha=0.7)
plt.fill_between(steps, -30, 30, color='lightcoral', alpha=0.2)
plt.title('Rotación entre pasos: Pitch (Y)')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True); plt.legend()

plt.subplot(2, 2, 4)
plt.plot(steps, angles_x, 'brown', linewidth=2, label='ΔRoll (X)')
plt.axhline(10, color='r', ls='--', alpha=0.7); plt.axhline(-10, color='r', ls='--', alpha=0.7)
plt.fill_between(steps, -10, 10, color='lightcoral', alpha=0.2)
plt.title('Rotación entre pasos: Roll (X)')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True); plt.legend()

plt.tight_layout()
plt.show()

# === Gráfico 2: Orientación absoluta ===
fig2 = plt.figure(figsize=(14, 8))

plt.subplot(2, 2, 1)
plt.plot(steps, abs_yaw, 'purple', linewidth=2)
plt.title('Orientación Absoluta: Yaw (dirección)')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True)

plt.subplot(2, 2, 2)
plt.plot(steps, abs_pitch, 'orange', linewidth=2)
plt.title('Orientación Absoluta: Pitch (inclinación)')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True)

plt.subplot(2, 2, 3)
plt.plot(steps, abs_roll, 'brown', linewidth=2)
plt.title('Orientación Absoluta: Roll estimado')
plt.xlabel('Paso'); plt.ylabel('Ángulo (°)'); plt.grid(True)

# Resumen comparativo
plt.subplot(2, 2, 4)
labels = ['Roll (X)', 'Pitch (Y)', 'Yaw (Z)']
achieved = [max_roll, max_pitch, max_yaw]
limits = [10, 30, 45]
colors = ['red' if a > l else 'green' for a, l in zip(achieved, limits)]
bars = plt.bar(labels, achieved, color=colors, alpha=0.7, edgecolor='black', capsize=5)
plt.axhline(10, color='r', ls='--', alpha=0.5); plt.axhline(30, ls='--', alpha=0.5); plt.axhline(45, ls='--', alpha=0.5)
plt.title('Rotación máxima entre pasos vs Límites')
plt.ylabel('Ángulo (°)')
plt.ylim(0, max(limits)*1.2)

# Etiquetas en barras
for bar, val in zip(bars, achieved):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}°',
             ha='center', va='bottom', fontsize=9)

plt.tight_layout()
plt.show()

# === Impresión detallada por pasos clave ===
print(f"\n📊 Resumen de orientación y rotación (valores seleccionados):")
print(f"{'Paso':<5} {'Yaw':<8} {'Pitch':<8} {'Roll':<8} {'ΔZ':<8} {'ΔY':<8} {'ΔX':<8}")
for step in [0, 25, 50, 75, 99]:
    print(f"{step:<5} {abs_yaw[step]:<+8.1f} {abs_pitch[step]:<+8.1f} {abs_roll[step]:<+8.1f} "
          f"{angles_z[step]:<+8.1f} {angles_y[step]:<+8.1f} {angles_x[step]:<+8.1f}")

# === Opcional: Exportar a CSV ===
export_csv = False  # Cambia a True si quieres guardar
if export_csv:
    import pandas as pd
    df = pd.DataFrame({
        'paso': np.arange(n_steps),
        'x': x_t, 'y': y_t, 'z': z_t,
        'yaw_abs': abs_yaw, 'pitch_abs': abs_pitch, 'roll_abs': abs_roll,
        'delta_yaw': angles_z, 'delta_pitch': angles_y, 'delta_roll': angles_x
    })
    df.to_csv('trayectoria_movil.csv', index=False)
    print("\n💾 Datos exportados a 'trayectoria_movil.csv'")
