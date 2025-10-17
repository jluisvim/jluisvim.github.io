# test9_fixed.py - Sistema multi-robot descentralizado con INICIO/FIN y movimiento correcto

from pyswip import Prolog
import matplotlib.pyplot as plt
import time
import random

# Inicializar Prolog
prolog = Prolog()
prolog.assertz("battery_ok(B) :- B > 20")
prolog.assertz("near(X, Y, Tx, Ty, Thresh) :- abs(X - Tx) < Thresh, abs(Y - Ty) < Thresh")
prolog.assertz("should_collect(B, X, Y, Tx, Ty) :- battery_ok(B), near(X, Y, Tx, Ty, 5)")

# Estado global
system_mode = "idle"  # 'idle', 'active', 'returning'

# Clase Robot
class Robot:
    def __init__(self, name, x, y, battery):
        self.name = name
        self.x = x
        self.y = y
        self.battery = battery
        self.home_x = x
        self.home_y = y
        self.target = None
        self.color = [random.random() for _ in range(3)]
        self.intent = "idle"
        self.mode = "idle"

    def update_beliefs(self):
        # Limpiar hechos anteriores
        try:
            list(prolog.query(f"retractall(at({self.name}, _, _, _))"))
            list(prolog.query(f"retractall(battery({self.name}, _))"))
        except:
            pass
        # Añadir nuevos
        prolog.assertz(f"at({self.name}, {self.x}, {self.y}, 0)")
        prolog.assertz(f"battery({self.name}, {self.battery})")

    def decide(self, objects):
        self.update_beliefs()

        # Modo global
        if system_mode == "returning":
            self.target = (self.home_x, self.home_y)
            self.intent = "returning home"
            self.mode = "going_home"
            return

        if system_mode != "active":
            self.intent = "waiting"
            self.target = None
            self.mode = "idle"
            return

        # Buscar objeto cercano NO reclamado
        claimed_targets = [(r.target, r.name) for r in robots if r.target and r.name != self.name]

        for obj_name, ox, oy in objects:
            # Verificar si ya está siendo recogido
            if any(t == (ox, oy) for t, rn in claimed_targets):
                continue

            # Consultar si debería recogerlo
            query_str = f"should_collect({self.battery}, {self.x}, {self.y}, {ox}, {oy})"
            try:
                if list(prolog.query(query_str)):
                    self.target = (ox, oy)
                    self.intent = f"collecting ({ox},{oy})"
                    self.mode = "collecting"
                    return
            except Exception as e:
                print(f"Error en Prolog para {self.name}: {e}")

        # Si no hay objetivos válidos
        self.target = None
        self.intent = "idle"
        self.mode = "idle"

    def move(self, objects):
        target_x, target_y = None, None

        if self.mode == "going_home":
            target_x, target_y = self.home_x, self.home_y
        elif self.mode == "collecting" and self.target:
            target_x, target_y = self.target

        if target_x is not None:
            dx = target_x - self.x
            dy = target_y - self.y
            dist = (dx**2 + dy**2)**0.5
            if dist > 1.0:
                step = min(2.0, dist)
                self.x += dx / dist * step
                self.y += dy / dist * step
                self.battery -= 0.6
                if self.battery < 0:
                    self.battery = 0
            else:
                # Llegó al objetivo
                if self.mode == "collecting":
                    print(f"✅ {self.name} ha llegado al objeto en ({target_x:.1f}, {target_y:.1f})")
                    objects[:] = [(n, x, y) for n, x, y in objects if not (abs(x - target_x) < 1 and abs(y - target_y) < 1)]
                    self.target = None
                    self.mode = "idle"
                    self.intent = "idle"
                elif self.mode == "going_home":
                    print(f"🏠 {self.name} ha regresado a casa ({target_x:.1f}, {target_y:.1f})")
                    self.target = None
                    self.mode = "idle"
                    self.intent = "at home"

# --- Inicialización ---
robots = [
    Robot("R1", 0, 0, 80),
    Robot("R2", 5, 5, 70),
]

objects = [
    ("A", 15, 15),
    ("B", 25, 25),
    ("C", 10, 30),
]

# --- Visualización ---
fig, ax = plt.subplots(figsize=(10, 10))
plt.ion()

def draw():
    ax.clear()
    ax.set_xlim(-2, 35)
    ax.set_ylim(-2, 35)
    ax.grid(True, alpha=0.3)

    mode_text = {
        "idle": "Esperando comando 'i' (INICIO)",
        "active": "MODO ACTIVO - Robots buscando objetos",
        "returning": "FIN ACTIVADO - Regresando a casa"
    }
    ax.set_title(f"Sistema Multi-Robot Descentralizado\nEstado: {mode_text[system_mode]}", fontsize=12)

    # Objetos
    for name, x, y in objects:
        ax.scatter(x, y, c='red', s=100, marker='o', label="Objetivo" if name=="A" else "")
        ax.text(x + 0.5, y + 0.5, name, color='darkred', fontsize=10)

    # Robots
    for robot in robots:
        ax.scatter(robot.x, robot.y, c=[robot.color], s=150, marker='s', edgecolor='black')
        ax.text(robot.x + 0.5, robot.y + 0.5, f"{robot.name}\n{robot.intent[:10]}", fontsize=9, color='blue')

        if robot.target:
            tx, ty = robot.target
            ax.annotate("", xy=(tx, ty), xytext=(robot.x, robot.y),
                        arrowprops=dict(arrowstyle="->", color='gray', lw=1))

        # Punto de inicio
        ax.plot(robot.home_x, robot.home_y, 'ks', markersize=6)
        ax.text(robot.home_x + 0.5, robot.home_y - 1, "Home", fontsize=8, color='purple')

    plt.tight_layout()
    plt.pause(0.01)

# --- Control por teclado ---
def on_key(event):
    global system_mode
    if event.key == 'i':
        system_mode = "active"
        print("▶️ INICIO: Robots activados y comenzando a operar.")
    elif event.key == 'f':
        system_mode = "returning"
        print("⏹️ FIN: Todos los robots regresan a casa.")

fig.canvas.mpl_connect('key_press_event', on_key)

print("\n🎮 Controles:")
print("   Presiona 'i' para INICIO")
print("   Presiona 'f' para FIN")
print("   Cierra la ventana para salir\n")

# --- Bucle principal ---
try:
    while plt.fignum_exists(fig.number):  # Detecta si la ventana está abierta
        for robot in robots:
            robot.decide(objects)  # ← ¡Clave! Decide en cada iteración
            robot.move(objects)     # ← ¡Clave! Mueve según decisión
        draw()
        time.sleep(0.3)
except KeyboardInterrupt:
    print("\n👋 Simulación terminada.")
finally:
    plt.ioff()
    plt.show()
