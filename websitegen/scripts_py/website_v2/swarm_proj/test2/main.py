#!/usr/bin/env python3
"""
Simulador Básico de Sistema de Patrullaje con Agentes Inteligentes
"""
from simulador import Simulador

def main():
    """Función principal"""
    print("=== Simulador de Sistema de Patrullaje ===")
    print("Creando 5 agentes con diferentes perfiles...")
    
    try:
        # Crear y ejecutar simulador
        simulador = Simulador('config/config.yaml')
        simulador.ejecutar_simulacion()
        
    except Exception as e:
        print(f"Error en la simulación: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
