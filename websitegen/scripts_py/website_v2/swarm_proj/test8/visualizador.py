import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.gridspec import GridSpec
import pandas as pd
import matplotlib.patches as patches

class VisualizadorProfesional:
    def __init__(self, analizador):
        self.analizador = analizador
        self.fig = None
        self.axs = None
        self.lines = {}
        self.bars = {}
        self.setup_estilo_profesional()
        
    def setup_estilo_profesional(self):
        """Configura estilo visual profesional"""
        plt.style.use('default')
        sns.set_style("whitegrid")
        plt.rcParams.update({
            'font.size': 10,
            'font.family': 'DejaVu Sans',
            'figure.titlesize': 16,
            'axes.titlesize': 14,
            'axes.labelsize': 12,
            'xtick.labelsize': 10,
            'ytick.labelsize': 10,
            'legend.fontsize': 10,
            'figure.dpi': 100,
        })
        
        # Paleta de colores profesional
        self.colores_agentes = {
            1: '#2E86AB',  # Azul profesional
            2: '#A23B72',  # Magenta
            3: '#F18F01'   # Naranja
        }

    def crear_dashboard_completo(self):
        """Crea dashboard profesional completo"""
        self.fig, self.axs = plt.subplots(2, 2, figsize=(15, 10))
        
        # Inicializar gráficas
        self.inicializar_grafica_cobertura(self.axs[0, 0])
        self.inicializar_grafica_eficiencia(self.axs[0, 1])
        self.inicializar_grafica_decisiones(self.axs[1, 0])
        self.inicializar_grafica_movimientos(self.axs[1, 1])
        
        self.fig.suptitle('DASHBOARD DE MONITOREO - SISTEMA DE 3 AGENTES\n', 
                         fontsize=16, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        return self.fig

    def inicializar_grafica_cobertura(self, ax):
        """Inicializa gráfica de cobertura"""
        ax.set_title('COBERTURA DEL MAPA', fontweight='bold', pad=10)
        ax.set_xlabel('Paso de Simulación')
        ax.set_ylabel('Porcentaje de Cobertura (%)')
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        
        self.lines['cobertura'], = ax.plot([], [], color='#2E86AB', linewidth=2.5, 
                                         marker='o', markersize=4, markevery=5,
                                         label='Cobertura Total')
        ax.legend()

    def inicializar_grafica_eficiencia(self, ax):
        """Inicializa gráfica de eficiencia"""
        ax.set_title('EFICIENCIA DE PATRULLAJE', fontweight='bold', pad=10)
        ax.set_xlabel('Paso de Simulación')
        ax.set_ylabel('Eficiencia (%)')
        ax.set_ylim(0, 105)
        ax.grid(True, alpha=0.3)
        
        self.lines['eficiencia'], = ax.plot([], [], color='#F18F01', linewidth=2.5,
                                          marker='s', markersize=4, markevery=5,
                                          label='Eficiencia')
        ax.legend()

    def inicializar_grafica_decisiones(self, ax):
        """Inicializa gráfica de decisiones"""
        ax.set_title('DISTRIBUCIÓN DE DECISIONES', fontweight='bold', pad=10)
        ax.set_xlabel('Agente')
        ax.set_ylabel('Cantidad de Decisiones')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Inicializar con datos vacíos
        agentes = ['Agente 1', 'Agente 2', 'Agente 3']
        self.bars['decisiones'] = ax.bar(agentes, [0, 0, 0], 
                                       color=[self.colores_agentes[1], self.colores_agentes[2], self.colores_agentes[3]],
                                       alpha=0.8)

    def inicializar_grafica_movimientos(self, ax):
        """Inicializa gráfica de movimientos"""
        ax.set_title('DISTANCIA RECORRIDA', fontweight='bold', pad=10)
        ax.set_xlabel('Agente')
        ax.set_ylabel('Distancia Total')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Inicializar con datos vacíos
        agentes = ['Agente 1', 'Agente 2', 'Agente 3']
        self.bars['movimientos'] = ax.bar(agentes, [0, 0, 0],
                                        color=[self.colores_agentes[1], self.colores_agentes[2], self.colores_agentes[3]],
                                        alpha=0.8)

    def actualizar_dashboard(self):
        """Actualiza todo el dashboard con datos actuales"""
        if not self.analizador.metricas['cobertura_mapa']:
            return
        
        try:
            # 1. Actualizar cobertura
            self._actualizar_grafica_cobertura()
            
            # 2. Actualizar eficiencia
            self._actualizar_grafica_eficiencia()
            
            # 3. Actualizar decisiones
            self._actualizar_grafica_decisiones()
            
            # 4. Actualizar movimientos
            self._actualizar_grafica_movimientos()
            
            # Redibujar la figura
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
            
        except Exception as e:
            print(f"Error actualizando dashboard: {e}")

    def _actualizar_grafica_cobertura(self):
        """Actualiza gráfica de cobertura"""
        ax = self.axs[0, 0]
        cobertura_data = self.analizador.metricas['cobertura_mapa']
        
        if cobertura_data:
            pasos = [m['paso'] for m in cobertura_data]
            valores = [m['cobertura_porcentaje'] for m in cobertura_data]
            
            self.lines['cobertura'].set_data(pasos, valores)
            ax.set_xlim(0, max(pasos) + 1 if pasos else 10)
            ax.set_ylim(0, max(valores) * 1.1 if valores else 100)

    def _actualizar_grafica_eficiencia(self):
        """Actualiza gráfica de eficiencia"""
        ax = self.axs[0, 1]
        eficiencia_data = self.analizador.metricas['eficiencia_patrullaje']
        
        if eficiencia_data:
            pasos = [m['paso'] for m in eficiencia_data]
            valores = [m['eficiencia_porcentaje'] for m in eficiencia_data]
            
            self.lines['eficiencia'].set_data(pasos, valores)
            ax.set_xlim(0, max(pasos) + 1 if pasos else 10)
            ax.set_ylim(0, max(valores) * 1.1 if valores else 100)

    def _actualizar_grafica_decisiones(self):
        """Actualiza gráfica de decisiones"""
        ax = self.axs[1, 0]
        
        # Contar decisiones por agente
        decisiones_count = {1: 0, 2: 0, 3: 0}
        for registro in self.analizador.metricas['historial_decisiones']:
            decisiones_count[registro['agente']] += 1
        
        # Actualizar barras
        for i, (bar, agente_id) in enumerate(zip(self.bars['decisiones'], [1, 2, 3])):
            bar.set_height(decisiones_count[agente_id])
            
            # Actualizar etiqueta
            if hasattr(bar, 'label_text'):
                bar.label_text.remove()
            
            bar.label_text = ax.text(bar.get_x() + bar.get_width()/2, 
                                   decisiones_count[agente_id] + 0.1,
                                   f'{decisiones_count[agente_id]}', 
                                   ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylim(0, max(decisiones_count.values()) * 1.2 + 1 if decisiones_count.values() else 5)

    def _actualizar_grafica_movimientos(self):
        """Actualiza gráfica de movimientos"""
        ax = self.axs[1, 1]
        
        # Calcular distancias totales
        distancias = []
        for agente_id in [1, 2, 3]:
            movimientos = self.analizador.estados_agentes[agente_id]['movimientos']
            distancia = 0
            for i in range(1, len(movimientos)):
                distancia += self._calcular_distancia(movimientos[i-1], movimientos[i])
            distancias.append(distancia)
        
        # Actualizar barras
        for i, (bar, distancia) in enumerate(zip(self.bars['movimientos'], distancias)):
            bar.set_height(distancia)
            
            # Actualizar etiqueta
            if hasattr(bar, 'label_text'):
                bar.label_text.remove()
            
            bar.label_text = ax.text(bar.get_x() + bar.get_width()/2, 
                                   distancia + 0.1,
                                   f'{distancia:.1f}', 
                                   ha='center', va='bottom', fontweight='bold')
        
        ax.set_ylim(0, max(distancias) * 1.2 if distancias else 10)

    def _calcular_distancia(self, pos1, pos2):
        """Calcula distancia Manhattan"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def generar_reporte_final(self):
        """Genera reporte final"""
        print("\nGenerando reporte final...")
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('REPORTE FINAL - SISTEMA DE 3 AGENTES', fontweight='bold')
        
        # Gráfica 1: Evolución
        self._graficar_evolucion(ax1)
        
        # Gráfica 2: Decisiones
        self._graficar_decisiones_final(ax2)
        
        # Gráfica 3: Movimientos
        self._graficar_movimientos_final(ax3)
        
        # Gráfica 4: Resumen
        self._graficar_resumen(ax4)
        
        plt.tight_layout()
        plt.savefig('data/reporte_final.png', dpi=150, bbox_inches='tight')
        plt.show()

    def _graficar_evolucion(self, ax):
        """Grafica evolución de cobertura y eficiencia"""
        cobertura_data = self.analizador.metricas['cobertura_mapa']
        eficiencia_data = self.analizador.metricas['eficiencia_patrullaje']
        
        if cobertura_data and eficiencia_data:
            pasos = [m['paso'] for m in cobertura_data]
            cobertura = [m['cobertura_porcentaje'] for m in cobertura_data]
            eficiencia = [m['eficiencia_porcentaje'] for m in eficiencia_data]
            
            ax.plot(pasos, cobertura, 'b-', label='Cobertura', linewidth=2, marker='o', markersize=3)
            ax.plot(pasos, eficiencia, 'r-', label='Eficiencia', linewidth=2, marker='s', markersize=3)
            
            ax.set_xlabel('Paso')
            ax.set_ylabel('Porcentaje (%)')
            ax.set_title('Evolución de Métricas')
            ax.legend()
            ax.grid(True)
            ax.set_ylim(0, 100)

    def _graficar_decisiones_final(self, ax):
        """Grafica decisiones finales"""
        decisiones_count = {1: 0, 2: 0, 3: 0}
        for registro in self.analizador.metricas['historial_decisiones']:
            decisiones_count[registro['agente']] += 1
        
        agentes = ['Agente 1\n(Guardian)', 'Agente 2\n(Explorador)', 'Agente 3\n(Soporte)']
        valores = [decisiones_count[1], decisiones_count[2], decisiones_count[3]]
        colores = [self.colores_agentes[1], self.colores_agentes[2], self.colores_agentes[3]]
        
        bars = ax.bar(agentes, valores, color=colores, alpha=0.8)
        ax.set_title('Decisiones por Agente')
        ax.set_ylabel('Cantidad de Decisiones')
        ax.grid(True, axis='y')
        
        for bar, valor in zip(bars, valores):
            ax.text(bar.get_x() + bar.get_width()/2, valor + 0.1,
                   f'{valor}', ha='center', va='bottom', fontweight='bold')

    def _graficar_movimientos_final(self, ax):
        """Grafica movimientos finales"""
        distancias = []
        for agente_id in [1, 2, 3]:
            movimientos = self.analizador.estados_agentes[agente_id]['movimientos']
            distancia = 0
            for i in range(1, len(movimientos)):
                distancia += self._calcular_distancia(movimientos[i-1], movimientos[i])
            distancias.append(distancia)
        
        agentes = ['Agente 1\n(Guardian)', 'Agente 2\n(Explorador)', 'Agente 3\n(Soporte)']
        colores = [self.colores_agentes[1], self.colores_agentes[2], self.colores_agentes[3]]
        
        bars = ax.bar(agentes, distancias, color=colores, alpha=0.8)
        ax.set_title('Distancia Recorrida')
        ax.set_ylabel('Distancia Total')
        ax.grid(True, axis='y')
        
        for bar, distancia in zip(bars, distancias):
            ax.text(bar.get_x() + bar.get_width()/2, distancia + 0.1,
                   f'{distancia:.1f}', ha='center', va='bottom', fontweight='bold')

    def _graficar_resumen(self, ax):
        """Grafica resumen numérico"""
        ax.axis('off')
        
        # Calcular métricas resumen
        cobertura_final = self.analizador.metricas['cobertura_mapa'][-1]['cobertura_porcentaje'] if self.analizador.metricas['cobertura_mapa'] else 0
        eficiencia_promedio = np.mean([m['eficiencia_porcentaje'] for m in self.analizador.metricas['eficiencia_patrullaje']]) if self.analizador.metricas['eficiencia_patrullaje'] else 0
        
        total_decisiones = len(self.analizador.metricas['historial_decisiones'])
        total_pasos = len(self.analizador.metricas['cobertura_mapa'])
        
        texto = f"""
        RESUMEN FINAL
        
        • Cobertura Final: {cobertura_final:.1f}%
        • Eficiencia Promedio: {eficiencia_promedio:.1f}%
        • Total de Decisiones: {total_decisiones}
        • Pasos Simulados: {total_pasos}
        
        Últimas decisiones:
        • Agente 1: {self.analizador.estados_agentes[1]['decisiones'][-3:] if len(self.analizador.estados_agentes[1]['decisiones']) >= 3 else self.analizador.estados_agentes[1]['decisiones']}
        • Agente 2: {self.analizador.estados_agentes[2]['decisiones'][-3:] if len(self.analizador.estados_agentes[2]['decisiones']) >= 3 else self.analizador.estados_agentes[2]['decisiones']}
        • Agente 3: {self.analizador.estados_agentes[3]['decisiones'][-3:] if len(self.analizador.estados_agentes[3]['decisiones']) >= 3 else self.analizador.estados_agentes[3]['decisiones']}
        """
        
        ax.text(0.1, 0.9, texto, transform=ax.transAxes, fontsize=11,
               verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
