import yaml
import random
import time
from agente import Agente
from mapa import Mapa
# Añadir al inicio:
from analizador import Analizador
from visualizador import VisualizadorProfesional

class Simulador:
    def __init__(self, config_file='config/config.yaml'):
        self.cargar_configuracion(config_file)
        self.analizador = Analizador()
        self.visualizador = VisualizadorProfesional(self.analizador)
        self.inicializar_simulacion()
        
    def cargar_configuracion(self, config_file):
        """Carga la configuración desde el archivo YAML"""
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
        except FileNotFoundError:
            print("Archivo de configuración no encontrado. Usando valores por defecto.")
            self.config = {
                'simulacion': {'ancho_mapa': 8, 'alto_mapa': 8, 'pasos_total': 15, 'delay_paso': 0.3, 'mostrar_mapa': True},
                'agentes': [
                    {'id': 1, 'perfil': 'guardian', 'posicion': [0, 0], 'color': 'blue'},
                    {'id': 2, 'perfil': 'explorador', 'posicion': [7, 0], 'color': 'red'},
                    {'id': 3, 'perfil': 'soporte', 'posicion': [0, 7], 'color': 'green'}
                ],
                'amenazas': {'probabilidad': 0.25, 'intensidad_maxima': 0.9}
            }
    
    def inicializar_simulacion(self):
        """Inicializa todos los componentes de la simulación"""
        sim_config = self.config['simulacion']
        self.mapa = Mapa(sim_config['ancho_mapa'], sim_config['alto_mapa'])
        
        # Crear agentes
        self.agentes = {}
        for agente_config in self.config['agentes']:
            agente = Agente(
                agente_config['id'],
                agente_config['perfil'],
                tuple(agente_config['posicion']),
                agente_config.get('color', 'gray')
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
    
    def ejecutar_paso(self):
        """Ejecuta un paso completo de simulación"""
        self.tiempo += 1
        print(f"\n=== Paso {self.tiempo} ===")
        
        # Generar nuevas amenazas
        self.generar_amenazas()
        
        # Actualizar mapa
        self.mapa.actualizar_amenazas(self.amenazas)
        self.mapa.amenazas = self.amenazas  # Pasar amenazas al mapa para acceso
        
        # Cada agente toma decisiones y actúa
        for agente_id, agente in self.agentes.items():
            # Tomar decisión (pasar las amenazas como parámetro)
            decision = agente.tomar_decision(self.amenazas)
            
            # Ejecutar acción
            nueva_pos = agente.ejecutar_accion(decision, self.mapa)
            
            # Mostrar resultado
            print(f"Agente {agente_id} ({agente.perfil}): {decision} -> {nueva_pos}")
            
            # Verificar si necesita ayuda
            if agente.necesita_ayuda():
                print(f"  ⚠️  Agente {agente_id} necesita ayuda!")
                
            # Registrar para análisis
            self.analizador.registrar_decision(agente_id, decision, {
                'posicion_actual': agente.posicion,
                'nivel_amenaza': self.amenazas.get(agente.posicion, 0.0)
            })
        
        # Registrar métricas para análisis
        self.analizador.registrar_paso(self.tiempo, self.agentes, self.amenazas)
        
        # Registrar métricas para análisis
        self.analizador.registrar_paso(self.tiempo, self.agentes, self.amenazas)
        
        # Actualizar dashboard en tiempo real
        if hasattr(self, 'dashboard_activo') and self.dashboard_activo:
            self.visualizador.actualizar_dashboard()

        # Dibujar estado actual
        if self.config['simulacion']['mostrar_mapa']:
            self.mapa.dibujar_agentes(self.agentes)
            self.mapa.mostrar(self.tiempo)
        
        # Pequeña pausa
        time.sleep(self.config['simulacion']['delay_paso'])
    
    def ejecutar_simulacion(self):
        """Ejecuta la simulación completa"""
        pasos_total = self.config['simulacion']['pasos_total']
        
        # Verificar si hay dashboard activo
        self.dashboard_activo = self.config['simulacion']['mostrar_mapa']
        
        print("Iniciando simulación de patrullaje")

        print("=== Sistema de 3 Agentes Móviles ===")
        print("Agentes:")
        for agente_id, agente in self.agentes.items():
            print(f"  {agente_id}: {agente.perfil} en {agente.posicion}")
        
        print(f"\nIniciando simulación por {pasos_total} pasos...")
        
        try:
            for paso in range(pasos_total):
                self.ejecutar_paso()
                
        except KeyboardInterrupt:
            print("\nSimulación interrumpida por el usuario")
        
        print("\n=== Simulación finalizada ===")
        
# En ejecutar_simulacion(), al final:
        # Generar reportes finales
        reporte = self.analizador.generar_reporte_final()
        print("\n=== REPORTE FINAL ===")
        print(f"Total pasos: {reporte['resumen_general']['total_pasos']}")
        print(f"Cobertura final: {reporte['resumen_general']['cobertura_final']['cobertura_porcentaje']:.1f}%")
        print(f"Eficiencia promedio: {reporte['resumen_general']['eficiencia_promedio']:.1f}%")
        
        # Generar visualizaciones
        # Al final del método ejecutar_simulacion():
        self.visualizador.generar_reporte_final()
