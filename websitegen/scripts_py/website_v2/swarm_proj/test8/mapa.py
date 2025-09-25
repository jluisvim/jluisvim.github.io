import numpy as np
import matplotlib.pyplot as plt

class Mapa:
    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.mapa_amenazas = np.zeros((alto, ancho))
        self.amenazas = {}
        self.fig, self.ax = plt.subplots(figsize=(6, 6))
        self.im = None
        self.scatter = None
        
    def actualizar_amenazas(self, amenazas):
        """Actualiza el mapa con las amenazas"""
        self.mapa_amenazas = np.zeros((self.alto, self.ancho))
        for (x, y), nivel in amenazas.items():
            if 0 <= x < self.ancho and 0 <= y < self.alto:
                self.mapa_amenazas[y, x] = nivel
        
        if self.im is None:
            self.im = self.ax.imshow(self.mapa_amenazas, cmap='Reds', 
                                   vmin=0, vmax=1, origin='lower')
        else:
            self.im.set_array(self.mapa_amenazas)
    
    def dibujar_agentes(self, agentes):
        """Dibuja los agentes en el mapa"""
        if self.scatter:
            self.scatter.remove()
            
        posiciones = []
        colores = []
        tamanos = []
        
        for agente in agentes.values():
            x, y = agente.posicion
            posiciones.append([x, y])
            colores.append(agente.color)
            tamanos.append(200)  # Tamaño fijo
            
        if posiciones:
            posiciones = np.array(posiciones)
            self.scatter = self.ax.scatter(
                posiciones[:, 0], posiciones[:, 1], 
                c=colores, s=tamanos, edgecolors='black', alpha=0.8
            )
    
    def mostrar(self, tiempo):
        """Muestra el mapa actualizado"""
        self.ax.set_title(f'Paso {tiempo} - Sistema de 3 Agentes')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-0.5, self.ancho - 0.5)
        self.ax.set_ylim(-0.5, self.alto - 0.5)
        
        # Añadir leyenda de colores
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', 
                      markersize=10, label='Guardian (Azul)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', 
                      markersize=10, label='Explorador (Rojo)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', 
                      markersize=10, label='Soporte (Verde)')
        ]
        self.ax.legend(handles=legend_elements, loc='upper right')
        
        plt.pause(0.1)
        plt.draw()
