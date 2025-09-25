# test9_fixed.py - Robots se mueven tras 'i', regresan con 'f'
import matplotlib.pyplot as plt
from pyswip import Prolog
import time
import random

# Inicializar Prolog
prolog = Prolog()
prolog.assertz("battery_ok(B) :- B > 20")
prolog.assertz("near(X, Y, Tx, Ty, Thresh) :- abs(X - Tx) < Thresh, abs(Y - Ty) < Thresh")
prolog.assertz("should_collect(B, X, Y, Tx, Ty) :- battery_ok(B), near(X, Y, Tx, Ty, 5)")

# Estado global
system_mode = "idle"

# Clase Robot
class Robot:
    def __init__(self, name, x, y, battery):
        self.name = name
        self.x = x
        self.y = y
        self.battery = battery
        self.home_x, self.home_y = x, y
        self.target = None
        self.color = [random.random() for _ in range(3)]
        self.intent = "idle"

    def decide(self, objects):
        global system_mode
        if system_mode == "returning":
            self.target = (self.home_x, self.home_y)
            self.intent = "going home"
            return

        if system_mode != "active":
            self.target = None
            self.intent = "waiting"
            return

        # Buscar objeto cercano no tomado
        for obj_name, ox, oy in objects:
            if self.target == (ox, oy):  # Ya lo está haciendo
                continue
            # Simular consulta lógica: ¿batería OK y cerca?
            if self.battery > 20 and abs(self.x - ox) < 10 and abs(self.y - oy) < 10:
                # Evitar duplicados (simulación simple)
                if not any(r.target == (ox, oy) and r.name != self.name for r in robots):
                    self.target = (ox, oy)
                    self.intent = f"going to {obj_name}"
                    return

        self.target = None
        self.intent = "idle"

    def move(self, objects):
        if not self.target:
            return

        tx, ty = self.target
        dx = tx - self.x
        dy = ty - self.y
        dist = (dx**2 + dy**2)**0.5
        if dist < 1.0:
            # Llegó al objetivo
            print(f"✅ {self.name} llegó a ({tx:.1f}, {ty:.1f})")
            self.target = None
            self.intent = "idle"
            # Remover objeto si es muestra
            objects[:] = [(n, x, y) for n, x, y in objects if not (abs(x - tx) < 1 and abs(y - ty) < 1)]
        else:
            step = min(2.0, dist)
            self.x += dx / dist * step
            self.y += dy / dist * step
            self.battery -= 0.5

# --- Crear robots y objetos ---
robots = [
    Robot("R1", 0, 0, 80),
    Robot("R2", 5, 5, 70),
]

objects = [
    ("sample_A", 15, 15),
    ("sample_B", 25, 25),
    ("sample_C", 10, 30),
]

# --- Configuración de gráficos ---
fig, ax = plt.subplots(figsize=(10, 10))
plt.ion()

def on_key(event):
    global system_mode
    if event.key == 'i':
        system_mode = "active"
        print("▶️ INICIO: robots activados.")
    elif event.key == 'f':
        system_mode = "returning"
        print("⏹️ FIN: todos regresan a casa.")

fig.canvas.mpl_connect('key_press_event', on_key)

def draw():
    ax.clear()
    ax.set_xlim(-5, 40)
    ax.set_ylim(-5, 40)
    ax.grid(True, alpha=0.3)

    mode_text = {
        "idle": "Esperando comando 'i'",
        "active": "MODO ACTIVO - buscando muestras",
        "returning": "REGRESANDO A CASA"
    }
    ax.set_title(f"Sistema Multi-Robot\nEstado: {mode_text[system_mode]}", fontsize=14)

    # Dibujar objetos
    for name, x, y in objects:
        ax.plot(x, y, 'ro', markersize=10)
        ax.text(x + 1, y + 1, name, fontsize=10)

    # Dibujar robots y sus objetivos
    for robot in robots:
        ax.plot(robot.x, robot.y, 's', color=robot.color, markersize=12, label=robot.name)
        ax.text(robot.x + 0.5, robot.y + 1, f"{robot.name}\n{robot.intent}", fontsize=9)

        # Flecha al objetivo
        if robot.target:
            ax.arrow(robot.x, robot.y, robot.target[0]-robot.x, robot.target[1]-robot.y,
                     head_width=0.8, head_length=1.0, fc='gray', alpha=0.5, length_includes_head=True)

        # Punto de inicio
        ax.plot(robot.home_x, robot.home_y, 'ks', markersize=6)
        ax.text(robot.home_x + 0.5, robot.home_y - 1.5, "Home", fontsize=8, color='purple')

    plt.tight_layout()
    plt.pause(0.01)

# --- Bucle principal ---
print("\n🎮 Controles:")
print("   Presiona 'i' para INICIO")
print("   Presiona 'f' para FIN\n")

try:
    while True:
        for robot in robots:
            robot.decide(objects)   # Replanificar en cada paso
            robot.move(objects)     # Mover según objetivo

        draw()
        time.sleep(0.3)  # Control de velocidad

except KeyboardInterrupt:
    print("\n👋 Simulación terminada.")
finally:
    plt.ioff()
    plt.show()
