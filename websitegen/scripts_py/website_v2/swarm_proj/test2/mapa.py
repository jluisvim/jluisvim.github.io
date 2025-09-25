import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.mapa = np.zeros((alto, ancho))
        self.fig, self.ax = plt.subplots(figsize=(8, 8))
        self.im = self.ax.imshow(self.mapa, cmap='Reds', vmin=0, vmax=1)
        self.scatter = None
        
    def actualizar_amenazas(self, amenazas):
        """Actualiza el mapa con las amenazas"""
        self.mapa = np.zeros((self.alto, self.ancho))
        for (x, y), nivel in amenazas.items():
            if 0 <= x < self.ancho and 0 <= y < self.alto:
                self.mapa[y, x] = nivel
        self.im.set_array(self.mapa)
    
    def dibujar_agentes(self, agentes):
        """Dibuja los agentes en el mapa"""
        if self.scatter:
            self.scatter.remove()
            
        posiciones = []
        colores = []
        for agente in agentes.values():
            x, y = agente.posicion
            posiciones.append([x, y])
            colores.append(self._color_por_perfil(agente.perfil_actual))
            
        if posiciones:
            posiciones = np.array(posiciones)
            self.scatter = self.ax.scatter(
                posiciones[:, 0], posiciones[:, 1], 
                c=colores, s=200, edgecolors='black'
            )
    
    def _color_por_perfil(self, perfil):
        """Asigna colores por perfil"""
        colores = {
            'guardian_perimetro': 'blue',
            'explorador_riesgo': 'red',
            'coordinador': 'green',
            'soporte_rapido': 'orange',
            'observador': 'purple'
        }
        return colores.get(perfil, 'gray')
    
    def mostrar(self, tiempo):
        """Muestra el mapa actualizado"""
        self.ax.set_title(f'Simulación - Paso {tiempo}')
        self.ax.grid(True)
        plt.pause(0.1)
