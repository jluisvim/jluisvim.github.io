#!/usr/bin/env python3
"""
Simulador de Sistema de Patrullaje Multi-Robot con Abstractización
Soporta: terrestres, aéreos, acuáticos y robots especializados
"""

import random
import time
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon
import yaml
import logging
from dataclasses import dataclass

# Configuración de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SimuladorMultiRobot")

# ==================== ENUMS Y ESTRUCTURAS ====================

class TipoMovimiento(Enum):
    TERRESTRE = "terrestre"
    AEREO = "aereo" 
    ACUATICO = "acuatico"
    ANFIBIO = "anfibio"

class TipoPropulsion(Enum):
    RUEDAS = "ruedas"
    ORUGAS = "orugas"
    PATAS = "patas"
    ROTORES = "rotores"
    HELICES = "helices"
    ALAS_FIJAS = "alas_fijas"

class EstadoRobot(Enum):
    ACTIVO = "activo"
    INACTIVO = "inactivo"
    DANADO = "danado"
    CARGANDO = "cargando"
    MANTENIMIENTO = "mantenimiento"

@dataclass
class Decision:
    accion: str
    prioridad: int
    explicacion: str
    timestamp: float

# ==================== INTERFAZ ABSTRACTA ====================

class InterfazRobot(ABC):
    """Interfaz abstracta para todos los tipos de robots"""
    
    @abstractmethod
    def mover(self, destino: Tuple[float, float, float]) -> bool:
        pass
    
    @abstractmethod
    def obtener_posicion(self) -> Tuple[float, float, float]:
        pass
    
    @abstractmethod
    def obtener_estado(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def obtener_capacidades(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def esta_operativo(self) -> bool:
        pass
    
    @abstractmethod
    def actualizar_bateria(self, consumo: float):
        pass
    
    @abstractmethod
    def tomar_decision_local(self, contexto: Dict) -> Optional[Decision]:
        pass

# ==================== IMPLEMENTACIONES CONCRETAS ====================

class RobotBase(InterfazRobot):
    """Clase base con funcionalidad común para todos los robots"""
    
    def __init__(self, id: str, tipo_movimiento: TipoMovimiento, 
                 propulsion: TipoPropulsion, config: Dict):
        self.id = id
        self.tipo_movimiento = tipo_movimiento
        self.propulsion = propulsion
        self.config = config
        self.posicion = config.get('posicion_inicial', (0.0, 0.0, 0.0))
        self.estado = EstadoRobot.ACTIVO
        self.bateria = 100.0
        self.velocidad = config.get('velocidad_maxima', 1.0)
        self.autonomia = config.get('autonomia', 8.0)
        self.historial_posiciones = [self.posicion]
        self.rol = config.get('rol', 'patrullero')
        
    def obtener_posicion(self) -> Tuple[float, float, float]:
        return self.posicion
    
    def obtener_estado(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'tipo_movimiento': self.tipo_movimiento.value,
            'propulsion': self.propulsion.value,
            'estado': self.estado.value,
            'bateria': self.bateria,
            'posicion': self.posicion,
            'rol': self.rol
        }
    
    def obtener_capacidades(self) -> Dict[str, Any]:
        return self.config
    
    def esta_operativo(self) -> bool:
        return (self.estado == EstadoRobot.ACTIVO and 
                self.bateria > 10.0 and 
                self.config.get('operativo', True))
    
    def actualizar_bateria(self, consumo: float):
        self.bateria = max(0.0, self.bateria - consumo)
        if self.bateria <= 10.0:
            self.estado = EstadoRobot.CARGANDO
    
    def tomar_decision_local(self, contexto: Dict) -> Optional[Decision]:
        """Decisión local basada en el tipo de robot"""
        if not self.esta_operativo():
            return Decision(accion="esperar", prioridad=0, 
                          explicacion="Robot no operativo", timestamp=time.time())
        
        # Lógica básica de decisión según tipo de robot
        if self.tipo_movimiento == TipoMovimiento.TERRESTRE:
            return self._decision_terrestre(contexto)
        elif self.tipo_movimiento == TipoMovimiento.AEREO:
            return self._decision_aereo(contexto)
        elif self.tipo_movimiento == TipoMovimiento.ACUATICO:
            return self._decision_acuatico(contexto)
        else:
            return self._decision_general(contexto)
    
    def _decision_terrestre(self, contexto: Dict) -> Decision:
        amenazas = contexto.get('amenazas', [])
        if amenazas and random.random() < 0.7:
            return Decision(accion="investigar_amenaza", prioridad=3, 
                          explicacion="Amenaza detectada en zona terrestre", timestamp=time.time())
        return Decision(accion="patrullar_ruta", prioridad=1, 
                      explicacion="Patrulla rutinaria terrestre", timestamp=time.time())
    
    def _decision_aereo(self, contexto: Dict) -> Decision:
        return Decision(accion="vigilancia_aerea", prioridad=2, 
                      explicacion="Vigilancia aérea en curso", timestamp=time.time())
    
    def _decision_acuatico(self, contexto: Dict) -> Decision:
        return Decision(accion="patrulla_subacuatica", prioridad=2, 
                      explicacion="Patrulla subacuática en curso", timestamp=time.time())
    
    def _decision_general(self, contexto: Dict) -> Decision:
        return Decision(accion="patrullar", prioridad=1, 
                      explicacion="Patrulla general en curso", timestamp=time.time())

class RobotRuedas(RobotBase):
    """Robot terrestre con ruedas para patrullaje en superficies planas"""
    
    def __init__(self, id: str, config: Dict):
        super().__init__(id, TipoMovimiento.TERRESTRE, TipoPropulsion.RUEDAS, config)
        self.radio_giro = config.get('radio_giro', 0.5)
        self.traccion = config.get('traccion', 0.8)
        
    def mover(self, destino: Tuple[float, float, float]) -> bool:
        if not self.esta_operativo():
            return False
            
        # Simular movimiento con ruedas (solo en plano XY)
        x, y, z = destino
        nueva_pos = (x, y, 0.0)  # Robots terrestres se mantienen en z=0
        
        distancia = np.sqrt((nueva_pos[0] - self.posicion[0])**2 + 
                           (nueva_pos[1] - self.posicion[1])**2)
        
        consumo = distancia * 0.5 / self.traccion
        self.actualizar_bateria(consumo)
        
        self.posicion = nueva_pos
        self.historial_posiciones.append(nueva_pos)
        return True

class DroneQuadcopter(RobotBase):
    """Drone cuadricóptero para vigilancia aérea"""
    
    def __init__(self, id: str, config: Dict):
        super().__init__(id, TipoMovimiento.AEREO, TipoPropulsion.ROTORES, config)
        self.altura_maxima = config.get('altura_maxima', 120.0)
        self.estabilidad_viento = config.get('estabilidad_viento', 5.0)
        
    def mover(self, destino: Tuple[float, float, float]) -> bool:
        if not self.esta_operativo():
            return False
            
        # Los drones pueden moverse en 3D
        distancia = np.sqrt((destino[0] - self.posicion[0])**2 +
                           (destino[1] - self.posicion[1])**2 +
                           (destino[2] - self.posicion[2])**2)
        
        consumo = distancia * 1.2  # Mayor consumo por vuelo
        self.actualizar_bateria(consumo)
        
        self.posicion = destino
        self.historial_posiciones.append(destino)
        return True

class ROVSubmarino(RobotBase):
    """Robot submarino operado remotamente"""
    
    def __init__(self, id: str, config: Dict):
        super().__init__(id, TipoMovimiento.ACUATICO, TipoPropulsion.HELICES, config)
        self.profundidad_maxima = config.get('profundidad_maxima', 100.0)
        self.flotabilidad = config.get('flotabilidad', 'neutra')
        
    def mover(self, destino: Tuple[float, float, float]) -> bool:
        if not self.esta_operativo():
            return False
            
        x, y, z = destino
        # Limitar profundidad
        z = max(-self.profundidad_maxima, min(z, 0))
        destino_limitado = (x, y, z)
        
        distancia = np.sqrt((destino_limitado[0] - self.posicion[0])**2 +
                           (destino_limitado[1] - self.posicion[1])**2 +
                           (destino_limitado[2] - self.posicion[2])**2)
        
        consumo = distancia * 0.8  # Menor consumo en agua
        self.actualizar_bateria(consumo)
        
        self.posicion = destino_limitado
        self.historial_posiciones.append(destino_limitado)
        return True

class RobotAnfibio(RobotBase):
    """Robot capaz de operar en tierra y agua"""
    
    def __init__(self, id: str, config: Dict):
        super().__init__(id, TipoMovimiento.ANFIBIO, TipoPropulsion.HELICES, config)
        self.modo_actual = "tierra"
        self.velocidad_tierra = config.get('velocidad_tierra', 1.5)
        self.velocidad_agua = config.get('velocidad_agua', 2.0)
        
    def mover(self, destino: Tuple[float, float, float]) -> bool:
        if not self.esta_operativo():
            return False
            
        x, y, z = destino
        
        # Determinar modo actual
        if z < -0.5:  # Bajo agua
            self.modo_actual = "agua"
            consumo_base = 0.7
        else:  # En tierra
            self.modo_actual = "tierra"
            consumo_base = 1.0
        
        distancia = np.sqrt((x - self.posicion[0])**2 +
                           (y - self.posicion[1])**2 +
                           (abs(z) - abs(self.posicion[2]))**2)
        
        consumo = distancia * consumo_base
        self.actualizar_bateria(consumo)
        
        self.posicion = destino
        self.historial_posiciones.append(destino)
        return True

# ==================== FÁBRICA DE ROBOTS ====================

class FabricaRobots:
    """Factory pattern para crear diferentes tipos de robots"""
    
    @staticmethod
    def crear_robot(tipo_robot: str, id: str, config: Dict) -> InterfazRobot:
        tipo_robot = tipo_robot.lower()
        
        if tipo_robot in ["ruedas", "terrestre"]:
            return RobotRuedas(id, config)
        elif tipo_robot in ["quadcopter", "drone", "aereo"]:
            return DroneQuadcopter(id, config)
        elif tipo_robot in ["submarino", "acuatico"]:
            return ROVSubmarino(id, config)
        elif tipo_robot in ["anfibio", "hibrido"]:
            return RobotAnfibio(id, config)
        else:
            raise ValueError(f"Tipo de robot no soportado: {tipo_robot}")

# ==================== SISTEMA DE COORDINACIÓN ====================

class SistemaCoordinacion:
    """Sistema que coordina múltiples robots"""
    
    def __init__(self):
        self.robots: Dict[str, InterfazRobot] = {}
        self.zonas_patrullaje = []
        self.amenazas_detectadas = []
        self.misiones_activas = []
        
    def agregar_robot(self, robot: InterfazRobot):
        self.robots[robot.id] = robot
        logger.info(f"Robot {robot.id} agregado al sistema")
    
    def asignar_mision(self, robot_id: str, mision: Dict):
        """Asigna una misión específica a un robot"""
        if robot_id in self.robots:
            # En un sistema real, aquí se implementaría lógica compleja
            logger.info(f"Misión asignada a robot {robot_id}: {mision}")
    
    def coordinar_patrullaje(self):
        """Coordina el patrullaje entre todos los robots"""
        decisiones = {}
        
        for robot_id, robot in self.robots.items():
            if robot.esta_operativo():
                contexto = self._obtener_contexto_robot(robot)
                decision = robot.tomar_decision_local(contexto)
                decisiones[robot_id] = decision
                
                # Ejecutar la decisión
                self._ejecutar_decision(robot, decision)
        
        return decisiones
    
    def _obtener_contexto_robot(self, robot: InterfazRobot) -> Dict:
        """Proporciona contexto relevante para la decisión del robot"""
        return {
            'amenazas': self.amenazas_detectadas,
            'otros_robots': [r.obtener_estado() for r in self.robots.values() if r.id != robot.id],
            'hora': time.time(),
            'bateria': robot.bateria
        }
    
    def _ejecutar_decision(self, robot: InterfazRobot, decision: Decision):
        """Ejecuta la decisión tomada por el robot"""
        if decision.accion == "patrullar_ruta":
            destino = self._generar_destino_patrulla(robot)
            robot.mover(destino)
        elif decision.accion == "investigar_amenaza" and self.amenazas_detectadas:
            amenaza = random.choice(self.amenazas_detectadas)
            robot.mover(amenaza['posicion'])
        elif decision.accion == "vigilancia_aerea":
            destino = self._generar_destino_aereo(robot)
            robot.mover(destino)
        # Otras acciones...
    
    def _generar_destino_patrulla(self, robot: InterfazRobot) -> Tuple[float, float, float]:
        """Genera un destino de patrulla apropiado para el tipo de robot"""
        pos_actual = robot.obtener_posicion()
        
        if isinstance(robot, DroneQuadcopter):
            # Drones patrullan en 3D
            return (pos_actual[0] + random.uniform(-20, 20),
                    pos_actual[1] + random.uniform(-20, 20),
                    random.uniform(50, 100))
        elif isinstance(robot, ROVSubmarino):
            # Submarinos patrullan bajo agua
            return (pos_actual[0] + random.uniform(-10, 10),
                    pos_actual[1] + random.uniform(-10, 10),
                    random.uniform(-30, -5))
        else:
            # Robots terrestres y anfibios patrullan en superficie
            return (pos_actual[0] + random.uniform(-15, 15),
                    pos_actual[1] + random.uniform(-15, 15),
                    0.0)
    
    def _generar_destino_aereo(self, robot: InterfazRobot) -> Tuple[float, float, float]:
        """Genera destino para vigilancia aérea"""
        return (random.uniform(0, 200), random.uniform(0, 200), random.uniform(80, 120))

# ==================== SIMULADOR PRINCIPAL ====================

class SimuladorMultiRobot:
    """Simulador principal del sistema multi-robot"""
    
    def __init__(self, config_file: str = None):
        self.config = self._cargar_configuracion(config_file)
        self.coordinador = SistemaCoordinacion()
        self.fabrica = FabricaRobots()
        self.tiempo_simulacion = 0
        self.inicializar_robots()
        self.inicializar_visualizacion()
        
    def _cargar_configuracion(self, config_file: str) -> Dict:
        """Carga configuración desde archivo YAML o usa valores por defecto"""
        if config_file:
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            except:
                logger.warning("No se pudo cargar archivo de configuración, usando valores por defecto")
        
        # Configuración por defecto
        return {
            'robots': [
                {
                    'id': 'terrestre_1',
                    'tipo': 'ruedas',
                    'config': {
                        'velocidad_maxima': 2.0,
                        'autonomia': 8.0,
                        'posicion_inicial': (50, 50, 0),
                        'rol': 'patrullero'
                    }
                },
                {
                    'id': 'aereo_1', 
                    'tipo': 'quadcopter',
                    'config': {
                        'velocidad_maxima': 15.0,
                        'autonomia': 0.5,
                        'altura_maxima': 120,
                        'posicion_inicial': (100, 100, 80),
                        'rol': 'vigilancia'
                    }
                },
                {
                    'id': 'acuatico_1',
                    'tipo': 'submarino',
                    'config': {
                        'velocidad_maxima': 3.0,
                        'autonomia': 6.0,
                        'profundidad_maxima': 50,
                        'posicion_inicial': (150, 150, -20),
                        'rol': 'monitoreo'
                    }
                },
                {
                    'id': 'anfibio_1',
                    'tipo': 'anfibio',
                    'config': {
                        'velocidad_tierra': 1.5,
                        'velocidad_agua': 2.5,
                        'autonomia': 10.0,
                        'posicion_inicial': (180, 180, 0),
                        'rol': 'respuesta_rapida'
                    }
                }
            ],
            'simulacion': {
                'duracion_paso': 1.0,
                'pasos_totales': 100,
                'probabilidad_amenaza': 0.2
            }
        }
    
    def inicializar_robots(self):
        """Inicializa todos los robots según configuración"""
        for robot_config in self.config['robots']:
            try:
                robot = self.fabrica.crear_robot(
                    robot_config['tipo'],
                    robot_config['id'],
                    robot_config['config']
                )
                self.coordinador.agregar_robot(robot)
            except Exception as e:
                logger.error(f"Error creando robot {robot_config['id']}: {e}")
    
    def inicializar_visualizacion(self):
        """Inicializa el sistema de visualización"""
        self.fig, self.ax = plt.subplots(1, 2, figsize=(15, 7))
        self.fig.suptitle('Simulador Multi-Robot de Patrullaje', fontsize=16)
        
    def generar_amenazas(self):
        """Genera amenazas aleatorias en la zona de patrullaje"""
        if random.random() < self.config['simulacion'].get('probabilidad_amenaza', 0.2):
            tipo_amenaza = random.choice(['intruso', 'incendio', 'contaminacion', 'accidente'])
            posicion = (random.uniform(0, 200), random.uniform(0, 200), random.uniform(-30, 100))
            
            amenaza = {
                'tipo': tipo_amenaza,
                'posicion': posicion,
                'timestamp': time.time(),
                'severidad': random.uniform(0.1, 1.0)
            }
            
            self.coordinador.amenazas_detectadas.append(amenaza)
            logger.info(f"Nueva amenaza detectada: {tipo_amenaza} en {posicion}")
    
    def actualizar_visualizacion(self):
        """Actualiza la visualización del estado del sistema"""
        self.ax[0].clear()
        self.ax[1].clear()
        
        # Visualización 2D (vista superior)
        self.ax[0].set_title('Vista Superior (X-Y)')
        self.ax[0].set_xlim(0, 200)
        self.ax[0].set_ylim(0, 200)
        self.ax[0].grid(True)
        
        # Visualización 3D (vista lateral)
        self.ax[1].set_title('Vista Lateral (X-Z)')
        self.ax[1].set_xlim(0, 200)
        self.ax[1].set_ylim(-50, 150)
        self.ax[1].grid(True)
        
        # Dibujar superficie de agua
        self.ax[1].axhline(y=0, color='blue', linestyle='-', alpha=0.3, label='Superficie agua')
        
        # Dibujar robots
        colores = {'terrestre': 'green', 'aereo': 'red', 'acuatico': 'blue', 'anfibio': 'purple'}
        formas = {'ruedas': 'o', 'rotores': '^', 'helices': 's', 'patas': 'D'}
        
        for robot_id, robot in self.coordinador.robots.items():
            estado = robot.obtener_estado()
            pos = estado['posicion']
            tipo = estado['tipo_movimiento']
            propulsion = estado['propulsion']
            
            color = colores.get(tipo, 'black')
            forma = formas.get(propulsion, 'o')
            
            # Vista superior
            self.ax[0].scatter(pos[0], pos[1], c=color, marker=forma, s=100, label=robot_id)
            self.ax[0].text(pos[0], pos[1], robot_id, fontsize=8)
            
            # Vista lateral
            self.ax[1].scatter(pos[0], pos[2], c=color, marker=forma, s=100)
            self.ax[1].text(pos[0], pos[2], robot_id, fontsize=8)
        
        # Dibujar amenazas
        for amenaza in self.coordinador.amenazas_detectadas:
            pos = amenaza['posicion']
            self.ax[0].scatter(pos[0], pos[1], c='orange', marker='*', s=200)
            self.ax[1].scatter(pos[0], pos[2], c='orange', marker='*', s=200)
        
        self.ax[0].legend()
        self.ax[1].legend()
        plt.pause(0.01)
    
    def ejecutar_paso(self):
        """Ejecuta un paso completo de simulación"""
        self.tiempo_simulacion += 1
        logger.info(f"=== Paso {self.tiempo_simulacion} ===")
        
        # Generar amenazas aleatorias
        self.generar_amenazas()
        
        # Coordinar patrullaje
        decisiones = self.coordinador.coordinar_patrullaje()
        
        # Mostrar decisiones
        for robot_id, decision in decisiones.items():
            logger.info(f"Robot {robot_id}: {decision.accion} (Prioridad: {decision.prioridad})")
        
        # Actualizar visualización
        self.actualizar_visualizacion()
        
        # Pausa entre pasos
        time.sleep(self.config['simulacion'].get('duracion_paso', 1.0))
    
    def ejecutar_simulacion(self, pasos: int = None):
        """Ejecuta la simulación completa"""
        pasos = pasos or self.config['simulacion'].get('pasos_totales', 100)
        
        logger.info(f"Iniciando simulación de {pasos} pasos")
        
        try:
            for paso in range(pasos):
                self.ejecutar_paso()
                
        except KeyboardInterrupt:
            logger.info("Simulación interrumpida por el usuario")
        finally:
            logger.info("Simulación finalizada")
            plt.show()

# ==================== EJECUCIÓN PRINCIPAL ====================

def main():
    """Función principal de ejecución"""
    print("🚀 Simulador Multi-Robot de Patrullaje Inteligente")
    print("=" * 50)
    print("Tipos de robots soportados:")
    print("  • Terrestres (ruedas, orugas, patas)")
    print("  • Aéreos (drones quadcopter, ala fija)") 
    print("  • Acuáticos (submarinos, ROVs)")
    print("  • Anfibios (tierra + agua)")
    print("=" * 50)
    
    # Crear y ejecutar simulador
    simulador = SimuladorMultiRobot()
    simulador.ejecutar_simulacion(pasos=50)
    
    print("Simulación completada. ¡Gracias por usar el sistema!")

if __name__ == "__main__":
    main()
