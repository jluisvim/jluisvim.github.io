import yaml
import random
import time
from agente import Agente
from mapa import Mapa

class Simulador:
    def __init__(self, config_file='config/config.yaml'):
        self.cargar_configuracion(config_file)
        self.inicializar_simulacion()
        
    def cargar_configuracion(self, config_file):
        """Carga la configuración desde el archivo YAML"""
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Archivo de configuración {config_file} no encontrado. Usando configuración por defecto.")
            self.config = {
                'simulacion': {
                    'ancho_mapa': 10,
                    'alto_mapa': 10,
                    'pasos_total': 20,
                    'delay_paso': 0.5,
                    'mostrar_mapa': True
                },
                'agentes': [
                    {'id': 1, 'perfil': 'guardian_perimetro', 'posicion': [0, 0]},
                    {'id': 2, 'perfil': 'explorador_riesgo', 'posicion': [9, 0]},
                    {'id': 3, 'perfil': 'coordinador', 'posicion': [5, 5]},
                    {'id': 4, 'perfil': 'soporte_rapido', 'posicion': [0, 9]},
                    {'id': 5, 'perfil': 'observador', 'posicion': [9, 9]}
                ],
                'amenazas': {
                    'probabilidad': 0.3,
                    'intensidad_maxima': 1.0
                }
            }
    
    def inicializar_simulacion(self):
        """Inicializa todos los componentes de la simulación"""
        # Crear mapa
        sim_config = self.config['simulacion']
        self.mapa = Mapa(sim_config['ancho_mapa'], sim_config['alto_mapa'])
        
        # Crear agentes
        self.agentes = {}
        for agente_config in self.config['agentes']:
            agente = Agente(
                agente_config['id'],
                agente_config['perfil'],
                tuple(agente_config['posicion'])
            )
            self.agentes[agente_config['id']] = agente
        
        self.tiempo = 0
        self.amenazas = {}
        
    def generar_amenazas(self):
        """Genera amenazas aleatorias en el mapa"""
        self.amenazas = {}
        prob_amenaza = self.config['amenazas']['probabilidad']
        max_intensidad = self.config['amenazas']['intensidad_maxima']
        
        for x in range(self.mapa.ancho):
            for y in range(self.mapa.alto):
                if random.random() < prob_amenaza:
                    nivel = random.uniform(0.1, max_intensidad)
                    self.amenazas[(x, y)] = nivel
    
    def obtener_info_agentes(self):
        """Obtiene información de todos los agentes"""
        info = {}
        for agente_id, agente in self.agentes.items():
            info[agente_id] = (agente.posicion, agente.perfil_actual)
        return info
    
    def ejecutar_paso(self):
        """Ejecuta un paso completo de simulación"""
        self.tiempo += 1
        print(f"\n=== Paso {self.tiempo} ===")
        
        # Generar nuevas amenazas
        self.generar_amenazas()
        
        # Actualizar mapa
        self.mapa.actualizar_amenazas(self.amenazas)
        
        # Obtener información de agentes para contexto
        info_agentes = self.obtener_info_agentes()
        
        # Cada agente toma decisiones
        for agente_id, agente in self.agentes.items():
            # Preparar contexto
            otros_agentes = {aid: info for aid, info in info_agentes.items() if aid != agente_id}
            agente.actualizar_contexto(self.amenazas, otros_agentes)
            
            # Tomar decisión
            decision = agente.tomar_decision()
            
            # Ejecutar acción
            nueva_pos = agente.ejecutar_accion(decision, self.mapa)
            
            # Mostrar resultado
            print(f"Agente {agente_id} ({agente.perfil_actual}): {decision} -> {nueva_pos}")
        
        # Dibujar estado actual
        if self.config['simulacion']['mostrar_mapa']:
            try:
                self.mapa.dibujar_agentes(self.agentes)
                self.mapa.mostrar(self.tiempo)
            except Exception as e:
                print(f"Error mostrando mapa: {e}")
        
        # Pequeña pausa
        time.sleep(self.config['simulacion']['delay_paso'])
    
    def ejecutar_simulacion(self):
        """Ejecuta la simulación completa"""
        pasos_total = self.config['simulacion']['pasos_total']
        
        print("Iniciando simulación de patrullaje")
        agentes_info = [f"{aid}({a.perfil_actual})" for aid, a in self.agentes.items()]
        print(f"Agentes: {', '.join(agentes_info)}")
        
        try:
            for paso in range(pasos_total):
                self.ejecutar_paso()
                if paso >= pasos_total - 1:
                    print("\n=== Simulación completada ===")
                
        except KeyboardInterrupt:
            print("\nSimulación interrumpida por el usuario")
        
        print("Simulación finalizada")

    
