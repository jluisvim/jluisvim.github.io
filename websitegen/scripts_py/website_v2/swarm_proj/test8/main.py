#!/usr/bin/env python3
"""
Sistema de 3 Agentes Móviles con Análisis y Visualización Profesional
"""
from simulador import Simulador
import matplotlib.pyplot as plt

def main():
    """Función principal"""
    print("Iniciando simulador de 3 agentes móviles con análisis...")
    
    try:
        simulador = Simulador('config/config.yaml')
        
        # Preguntar si mostrar dashboard
        mostrar_dashboard = input("¿Mostrar dashboard en tiempo real? (s/n): ").lower() == 's'
        
        if mostrar_dashboard:
            print("Creando dashboard profesional...")
            # Crear dashboard
            dashboard = simulador.visualizador.crear_dashboard_completo()
            plt.ion()  # Modo interactivo
            plt.show(block=False)
            
            print("Dashboard listo. Iniciando simulación...")
            print("El dashboard se actualizará automáticamente durante la simulación")
            
        print("\nIniciando simulación...")
        simulador.ejecutar_simulacion()
        
        if mostrar_dashboard:
            print("\nSimulación completada. Cerrando dashboard...")
            plt.ioff()  # Desactivar modo interactivo
            
        # Mostrar reporte final
        print("\nMostrando reporte final...")
        plt.show()  # Mostrar reporte final
            
    except Exception as e:
        print(f"Error en la simulación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Asegurarse de cerrar todas las figuras
        plt.close('all')

if __name__ == "__main__":
    main()
