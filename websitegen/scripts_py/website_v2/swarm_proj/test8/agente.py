from pyswip import Prolog
import random
import time

class Agente:
    def __init__(self, id, perfil, posicion_inicial, color='gray'):
        self.id = id
        self.perfil = perfil
        self.posicion = posicion_inicial
        self.color = color
        self.ultima_decision = "inicial"
        self.decisiones_tomadas = 0
        self.prolog = Prolog()
        self._cargar_conocimiento()
        self._inicializar_hechos()
        
    def _cargar_conocimiento(self):
        """Carga la base de conocimiento Prolog"""
        archivos = [
            'knowledge_base/comportamientos.pl',
            'knowledge_base/reglas_decision.pl', 
            'knowledge_base/coordinacion.pl',
            'knowledge_base/personalidades.pl'
        ]
        for archivo in archivos:
            try:
                self.prolog.consult(archivo)
                print(f"✓ Agente {self.id} cargó: {archivo}")
            except Exception as e:
                print(f"✗ Error cargando {archivo}: {e}")
    
    def _inicializar_hechos(self):
        """Inicializa los hechos del agente en Prolog"""
        try:
            self.prolog.assertz(f"agente({self.id})")
            self.prolog.assertz(f"tiene_perfil({self.id}, {self.perfil})")
            self.prolog.assertz(f"posicion_actual({self.id}, {self.posicion})")
            print(f"✓ Hechos inicializados para agente {self.id}")
        except Exception as e:
            print(f"✗ Error inicializando hechos agente {self.id}: {e}")
    
    def _limpiar_hechos_temporales(self):
        """Limpia hechos temporales antes de cada consulta"""
        try:
            self.prolog.retractall("nivel_amenaza(_, _)")
        except:
            pass
    
    def actualizar_contexto(self, amenazas):
        """Actualiza el contexto del agente"""
        self._limpiar_hechos_temporales()
        
        for pos, nivel in amenazas.items():
            try:
                self.prolog.assertz(f"nivel_amenaza({pos}, {nivel})")
            except:
                pass
    
    def tomar_decision_simplificada(self, amenazas):
        """Toma decisión simplificada si Prolog falla"""
        x, y = self.posicion
        nivel_amenaza_actual = amenazas.get(self.posicion, 0.0)
        
        # Decisiones basadas en perfil y amenaza actual
        if self.perfil == 'guardian':
            if nivel_amenaza_actual > 0.6:
                return "pedir_ayuda"
            elif nivel_amenaza_actual > 0.3:
                return "investigar_cauteloso"
            else:
                return "patrullar_conservador"
                
        elif self.perfil == 'explorador':
            if nivel_amenaza_actual > 0.5:
                return "enfrentar_directo"
            elif nivel_amenaza_actual > 0.2:
                return "acercarse_amenaza"
            else:
                return "explorar_activo"
                
        elif self.perfil == 'soporte':
            # Buscar amenazas cercanas para ayudar
            for pos, nivel in amenazas.items():
                if nivel > 0.4 and self._calcular_distancia(pos, self.posicion) < 4:
                    return "moverse_apoyar"
            return "esperar_central"
        
        return "esperar"
    
    def tomar_decision(self, amenazas):
        """Intenta tomar decisión con Prolog, fallback a método simplificado"""
        try:
            # Actualizar contexto primero
            self.actualizar_contexto(amenazas)
            
            # Intentar consulta Prolog
            query = f"decision_agente({self.id}, Accion)"
            resultados = list(self.prolog.query(query))
            
            if resultados:
                decision = resultados[0]["Accion"]
                self.ultima_decision = decision
                self.decisiones_tomadas += 1
                print(f"Agente {self.id} decidió (Prolog): {decision}")
                return decision
                
        except Exception as e:
            print(f"Error en Prolog agente {self.id}, usando fallback: {e}")
        
        # Fallback a método simplificado
        decision = self.tomar_decision_simplificada(amenazas)
        self.ultima_decision = decision
        self.decisiones_tomadas += 1
        print(f"Agente {self.id} decidió (Fallback): {decision}")
        return decision
    
    def ejecutar_accion(self, accion, mapa):
        """Ejecuta la acción decidida"""
        if accion == "patrullar_conservador":
            return self._mover_conservador(mapa)
        elif accion == "explorar_activo":
            return self._mover_explorador(mapa)
        elif accion == "investigar_cauteloso":
            return self._mover_cauteloso(mapa)
        elif accion == "acercarse_amenaza":
            return self._mover_hacia_amenaza(mapa, mapa.amenazas)
        elif accion == "enfrentar_directo":
            return self._mover_hacia_amenaza(mapa, mapa.amenazas)
        elif accion == "moverse_apoyar":
            return self._mover_apoyo(mapa)
        elif accion == "pedir_ayuda":
            return self._mover_conservador(mapa)  # Se queda cerca
        elif accion == "esperar_central":
            return self.posicion
        else:
            return self._mover_aleatorio(mapa)
    
    def _mover_conservador(self, mapa):
        """Movimiento conservador del guardian"""
        movimientos = [(0, 1), (1, 0), (0, -1)]  # Excluye izquierda
        dx, dy = random.choice(movimientos)
        return self._aplicar_movimiento(dx, dy, mapa)
    
    def _mover_explorador(self, mapa):
        """Movimiento activo del explorador"""
        movimientos = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1)]
        dx, dy = random.choice(movimientos)
        return self._aplicar_movimiento(dx, dy, mapa)
    
    def _mover_cauteloso(self, mapa):
        """Movimiento cauteloso"""
        movimientos = [(0, 1), (1, 0)]
        dx, dy = random.choice(movimientos)
        return self._aplicar_movimiento(dx, dy, mapa)
    
    def _mover_hacia_amenaza(self, mapa, amenazas):
        """Movimiento hacia la amenaza más cercana"""
        if not amenazas:
            return self._mover_aleatorio(mapa)
        
        # Encontrar amenaza más cercana
        amenaza_cercana = None
        distancia_min = float('inf')
        
        for pos, nivel in amenazas.items():
            if nivel > 0.3:  # Solo amenazas significativas
                dist = self._calcular_distancia(self.posicion, pos)
                if dist < distancia_min:
                    distancia_min = dist
                    amenaza_cercana = pos
        
        if amenaza_cercana:
            # Moverse hacia la amenaza
            dx = 1 if amenaza_cercana[0] > self.posicion[0] else -1 if amenaza_cercana[0] < self.posicion[0] else 0
            dy = 1 if amenaza_cercana[1] > self.posicion[1] else -1 if amenaza_cercana[1] < self.posicion[1] else 0
            return self._aplicar_movimiento(dx, dy, mapa)
        
        return self._mover_aleatorio(mapa)
    
    def _mover_apoyo(self, mapa):
        """Movimiento de apoyo (hacia el centro)"""
        x, y = self.posicion
        dx = 1 if x < mapa.ancho // 2 else -1 if x > mapa.ancho // 2 else 0
        dy = 1 if y < mapa.alto // 2 else -1 if y > mapa.alto // 2 else 0
        return self._aplicar_movimiento(dx, dy, mapa)
    
    def _mover_aleatorio(self, mapa):
        """Movimiento aleatorio básico"""
        dx = random.randint(-1, 1)
        dy = random.randint(-1, 1)
        return self._aplicar_movimiento(dx, dy, mapa)
    
    def _aplicar_movimiento(self, dx, dy, mapa):
        """Aplica movimiento manteniéndose dentro del mapa"""
        x, y = self.posicion
        nueva_x = max(0, min(mapa.ancho - 1, x + dx))
        nueva_y = max(0, min(mapa.alto - 1, y + dy))
        
        nueva_pos = (nueva_x, nueva_y)
        self.posicion = nueva_pos
        
        # Actualizar posición en Prolog
        try:
            self.prolog.retractall(f"posicion_actual({self.id}, _)")
            self.prolog.assertz(f"posicion_actual({self.id}, {nueva_pos})")
        except:
            pass
            
        return nueva_pos
    
    def _calcular_distancia(self, pos1, pos2):
        """Calcula distancia Manhattan entre dos puntos"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def necesita_ayuda(self):
        """Verifica si el agente necesita ayuda (simplificado)"""
        # Simular necesidad de ayuda basada en decisiones recientes
        return random.random() < 0.2  # 20% de probabilidad
