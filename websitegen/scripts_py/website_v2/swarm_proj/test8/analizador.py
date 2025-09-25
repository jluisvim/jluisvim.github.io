import csv
import json
import time
import numpy as np
from datetime import datetime

class Analizador:
    def __init__(self):
        self.metricas = {
            'tiempo_real': [],
            'historial_decisiones': [],
            'estados_agentes': {},
            'cobertura_mapa': [],
            'eficiencia_patrullaje': []
        }
        
        # Inicializar estructura para cada agente
        self.estados_agentes = {
            1: {'movimientos': [], 'decisiones': [], 'amenazas_detectadas': 0},
            2: {'movimientos': [], 'decisiones': [], 'amenazas_detectadas': 0},
            3: {'movimientos': [], 'decisiones': [], 'amenazas_detectadas': 0}
        }
        
        self.archivo_metricas = 'data/metricas_tiempo_real.csv'
        self.archivo_historial = 'data/historial_decisiones.json'
        
        # Crear archivos si no existen
        self._inicializar_archivos()
    
    def _inicializar_archivos(self):
        """Inicializa los archivos de datos"""
        # Crear directorio data si no existe
        import os
        os.makedirs('data', exist_ok=True)
        
        # Inicializar CSV de métricas
        with open(self.archivo_metricas, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp', 'paso', 'agente', 'perfil', 'pos_x', 'pos_y',
                'decision', 'nivel_amenaza', 'necesita_ayuda', 'velocidad'
            ])
    
    def registrar_paso(self, paso, agentes, amenazas):
        """Registra métricas de cada paso de simulación"""
        timestamp = datetime.now().isoformat()
        
        for agente_id, agente in agentes.items():
            # Calcular nivel de amenaza en la posición actual
            nivel_amenaza = amenazas.get(agente.posicion, 0.0)
            
            # Calcular velocidad (distancia desde último movimiento)
            velocidad = 0
            if self.estados_agentes[agente_id]['movimientos']:
                ultima_pos = self.estados_agentes[agente_id]['movimientos'][-1]
                velocidad = self._calcular_distancia(ultima_pos, agente.posicion)
            
            # Registrar en tiempo real
            metricas_paso = {
                'timestamp': timestamp,
                'paso': paso,
                'agente': agente_id,
                'perfil': agente.perfil,
                'pos_x': agente.posicion[0],
                'pos_y': agente.posicion[1],
                'decision': agente.ultima_decision if hasattr(agente, 'ultima_decision') else 'esperar',
                'nivel_amenaza': nivel_amenaza,
                'necesita_ayuda': agente.necesita_ayuda(),
                'velocidad': velocidad
            }
            
            self.metricas['tiempo_real'].append(metricas_paso)
            
            # Actualizar estados de agentes
            self.estados_agentes[agente_id]['movimientos'].append(agente.posicion)
            if hasattr(agente, 'ultima_decision'):
                self.estados_agentes[agente_id]['decisiones'].append(agente.ultima_decision)
            
            # Guardar en CSV
            self._guardar_metricas_csv(metricas_paso)
        
        # Calcular métricas de cobertura
        self._calcular_cobertura_mapa(agentes, paso)
        self._calcular_eficiencia_patrullaje(paso)
    
    def _calcular_distancia(self, pos1, pos2):
        """Calcula distancia Manhattan entre dos puntos"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def _guardar_metricas_csv(self, metricas):
        """Guarda métricas en archivo CSV"""
        with open(self.archivo_metricas, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                metricas['timestamp'],
                metricas['paso'],
                metricas['agente'],
                metricas['perfil'],
                metricas['pos_x'],
                metricas['pos_y'],
                metricas['decision'],
                metricas['nivel_amenaza'],
                metricas['necesita_ayuda'],
                metricas['velocidad']
            ])
    
    def _calcular_cobertura_mapa(self, agentes, paso):
        """Calcula cobertura del mapa por los agentes"""
        posiciones_visitadas = set()
        for agente_id, datos in self.estados_agentes.items():
            for pos in datos['movimientos']:
                posiciones_visitadas.add(pos)
        
        total_celdas = 8 * 8  # Para mapa 8x8
        cobertura = len(posiciones_visitadas) / total_celdas * 100
        
        self.metricas['cobertura_mapa'].append({
            'paso': paso,
            'cobertura_porcentaje': cobertura,
            'celdas_visitadas': len(posiciones_visitadas),
            'celdas_totales': total_celdas
        })
    
    def _calcular_eficiencia_patrullaje(self, paso):
        """Calcula eficiencia del patrullaje"""
        # Métrica simple: agentes moviéndose vs estáticos
        agentes_activos = 0
        for agente_id, datos in self.estados_agentes.items():
            if len(datos['movimientos']) > 1:
                # Verificar si se está moviendo
                ultima_pos = datos['movimientos'][-1]
                penultima_pos = datos['movimientos'][-2] if len(datos['movimientos']) > 1 else ultima_pos
                if ultima_pos != penultima_pos:
                    agentes_activos += 1
        
        eficiencia = (agentes_activos / 3) * 100  # 3 agentes total
        
        self.metricas['eficiencia_patrullaje'].append({
            'paso': paso,
            'eficiencia_porcentaje': eficiencia,
            'agentes_activos': agentes_activos,
            'agentes_totales': 3
        })
    
    def registrar_decision(self, agente_id, decision, contexto):
        """Registra una decisión tomada por un agente"""
        registro_decision = {
            'timestamp': datetime.now().isoformat(),
            'agente': agente_id,
            'decision': decision,
            'contexto': contexto,
            'posicion': contexto.get('posicion_actual', (0, 0)),
            'nivel_amenaza': contexto.get('nivel_amenaza', 0.0)
        }
        
        self.metricas['historial_decisiones'].append(registro_decision)
        self.estados_agentes[agente_id]['decisiones'].append(decision)
    
    def generar_reporte_final(self):
        """Genera un reporte final de la simulación"""
        reporte = {
            'resumen_general': self._generar_resumen_general(),
            'metricas_agentes': self._generar_metricas_agentes(),
            'analisis_comportamiento': self._analizar_comportamiento(),
            'estadisticas_temporales': self._generar_estadisticas_temporales()
        }
        
        # Guardar reporte en JSON
        with open(self.archivo_historial, 'w') as f:
            json.dump(reporte, f, indent=2)
        
        return reporte
    
    def _generar_resumen_general(self):
        """Genera resumen general de la simulación"""
        total_pasos = len(self.metricas['tiempo_real']) / 3  # 3 agentes
        return {
            'total_pasos': total_pasos,
            'total_decisiones': len(self.metricas['historial_decisiones']),
            'cobertura_final': self.metricas['cobertura_mapa'][-1] if self.metricas['cobertura_mapa'] else {},
            'eficiencia_promedio': np.mean([m['eficiencia_porcentaje'] for m in self.metricas['eficiencia_patrullaje']]) if self.metricas['eficiencia_patrullaje'] else 0
        }
    
    def _generar_metricas_agentes(self):
        """Genera métricas individuales por agente"""
        metricas_agentes = {}
        
        for agente_id in [1, 2, 3]:
            movimientos = self.estados_agentes[agente_id]['movimientos']
            decisiones = self.estados_agentes[agente_id]['decisiones']
            
            if movimientos:
                # Calcular distancia total recorrida
                distancia_total = 0
                for i in range(1, len(movimientos)):
                    distancia_total += self._calcular_distancia(movimientos[i-1], movimientos[i])
                
                metricas_agentes[agente_id] = {
                    'total_movimientos': len(movimientos),
                    'distancia_total': distancia_total,
                    'decisiones_totales': len(decisiones),
                    'decision_mas_comun': max(set(decisiones), key=decisiones.count) if decisiones else 'ninguna',
                    'posiciones_unicas': len(set(movimientos)),
                    'velocidad_promedio': distancia_total / len(movimientos) if movimientos else 0
                }
        
        return metricas_agentes
    
    def _analizar_comportamiento(self):
        """Analiza patrones de comportamiento"""
        analisis = {
            'patrones_decisiones': {},
            'correlaciones': {},
            'tendencias_temporales': {}
        }
        
        # Análisis de patrones de decisiones por agente
        for agente_id in [1, 2, 3]:
            decisiones = self.estados_agentes[agente_id]['decisiones']
            if decisiones:
                conteo_decisiones = {}
                for decision in decisiones:
                    conteo_decisiones[decision] = conteo_decisiones.get(decision, 0) + 1
                
                analisis['patrones_decisiones'][agente_id] = conteo_decisiones
        
        return analisis
    
    def _generar_estadisticas_temporales(self):
        """Genera estadísticas temporales"""
        return {
            'cobertura_evolucion': self.metricas['cobertura_mapa'],
            'eficiencia_evolucion': self.metricas['eficiencia_patrullaje'],
            'series_temporales': self._preparar_series_temporales()
        }
    
    def _preparar_series_temporales(self):
        """Prepara datos para series temporales"""
        series = {
            'pasos': list(range(1, len(self.metricas['cobertura_mapa']) + 1)),
            'cobertura': [m['cobertura_porcentaje'] for m in self.metricas['cobertura_mapa']],
            'eficiencia': [m['eficiencia_porcentaje'] for m in self.metricas['eficiencia_patrullaje']]
        }
        return series

    def registrar_decision(self, agente_id, decision, contexto):
        """Registra una decisión tomada por un agente"""
        registro_decision = {
            'timestamp': time.time(),
            'agente': agente_id,
            'decision': decision,
            'contexto': contexto,
            'posicion': contexto.get('posicion_actual', (0, 0)),
            'nivel_amenaza': contexto.get('nivel_amenaza', 0.0)
        }
        
        self.metricas['historial_decisiones'].append(registro_decision)
        self.estados_agentes[agente_id]['decisiones'].append(decision)
