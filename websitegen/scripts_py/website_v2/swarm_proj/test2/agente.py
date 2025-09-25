from pyswip import Prolog
import random

class Agente:
    def __init__(self, id, perfil, posicion_inicial):
        self.id = id
        self.perfil_actual = perfil
        self.perfil_original = perfil
        self.posicion = posicion_inicial
        self.salud = 1.0
        self.estado = "normal"
        self.prolog = Prolog()
        self._cargar_conocimiento()
        self._inicializar_hechos()
        
    def _cargar_conocimiento(self):
        """Carga la base de conocimiento Prolog"""
        archivos = [
            'knowledge_base/comportamientos.pl',
            'knowledge_base/reglas_decision.pl',
            'knowledge_base/coordinacion.pl',
            'knowledge_base/roles_dinamicos.pl'
        ]
        for archivo in archivos:
            try:
                self.prolog.consult(archivo)
                print(f"✓ Cargado: {archivo}")
            except Exception as e:
                print(f"✗ Error cargando {archivo}: {e}")
    
    def _inicializar_hechos(self):
        """Inicializa los hechos del agente en Prolog"""
        # Limpiar hechos anteriores
        self._limpiar_hechos_agente()
        
        # Agregar nuevos hechos
        self.prolog.assertz(f"agente({self.id})")
        self.prolog.assertz(f"tiene_perfil({self.id}, {self.perfil_actual})")
        self.prolog.assertz(f"posicion_actual({self.id}, {self.posicion})")
        self.prolog.assertz(f"estado_salud({self.id}, {self.salud})")
        self.prolog.assertz(f"estado_actual({self.id}, {self.estado})")
    
    def _limpiar_hechos_agente(self):
        """Limpia todos los hechos del agente"""
        facts_to_remove = [
            f"agente({self.id})",
            f"tiene_perfil({self.id}, _)",
            f"posicion_actual({self.id}, _)",
            f"estado_salud({self.id}, _)",
            f"estado_actual({self.id}, _)"
        ]
        
        for fact in facts_to_remove:
            try:
                self.prolog.retractall(fact)
            except:
                pass
    
    def _limpiar_hechos_temporales(self):
        """Limpia los hechos temporales antes de cada nueva consulta"""
        try:
            # Limpiar amenazas
            self.prolog.retractall("nivel_amenaza(_, _)")
            
            # Limpiar otros agentes (excepto este)
            otros_agentes = list(self.prolog.query("agente(Id), Id \\= " + str(self.id)))
            for agente in otros_agentes:
                agente_id = agente["Id"]
                self.prolog.retractall(f"posicion_actual({agente_id}, _)")
                self.prolog.retractall(f"tiene_perfil({agente_id}, _)")
                
        except Exception as e:
            print(f"Error limpiando hechos temporales: {e}")
    
    def actualizar_contexto(self, amenazas, otros_agentes):
        """Actualiza el contexto del agente"""
        # Primero limpiar hechos temporales
        self._limpiar_hechos_temporales()
        
        # Actualizar amenazas
        for pos, nivel in amenazas.items():
            try:
                self.prolog.assertz(f"nivel_amenaza({pos}, {nivel})")
            except:
                pass
        
        # Actualizar otros agentes
        for agente_id, (pos, perfil) in otros_agentes.items():
            if agente_id != self.id:
                try:
                    self.prolog.assertz(f"posicion_actual({agente_id}, {pos})")
                    self.prolog.assertz(f"tiene_perfil({agente_id}, {perfil})")
                except:
                    pass
    
    def tomar_decision(self):
        """Toma una decisión basada en las reglas Prolog"""
        try:
            query = f"decision_agente({self.id}, Accion, Prioridad)"
            resultados = list(self.prolog.query(query))
            if resultados:
                accion = resultados[0].get("Accion", "esperar")
                print(f"Agente {self.id} decidió: {accion}")
                return accion
        except Exception as e:
            print(f"Error en toma de decisión agente {self.id}: {e}")
        return "esperar"
    
    def ejecutar_accion(self, accion, mapa):
        """Ejecuta la acción decidida"""
        acciones = {
            "patrullar_perimetro": self._mover_perimetro,
            "explorar_puntos_calientes": self._mover_aleatorio,
            "optimizar_rutas": self._mover_centro,
            "esperar_central": lambda m: self.posicion,
            "monitorear_zona": self._mover_observador,
            "investigar_amenaza": self._investigar_amenaza,
            "pedir_ayuda": self._pedir_ayuda,
            "acercarse_amenaza": self._investigar_amenaza,
            "enfrentar_amenaza": self._investigar_amenaza,
            "redistribuir_agentes": self._mover_centro,
            "coordinar_defensa": self._mover_centro,
            "moverse_a_amenaza": self._investigar_amenaza,
            "reportar_anomalias": lambda m: self.posicion
        }
        
        funcion_accion = acciones.get(accion, lambda m: self.posicion)
        nueva_pos = funcion_accion(mapa)
        
        # Actualizar posición en Prolog
        self._actualizar_posicion(nueva_pos)
        return nueva_pos
    
    def _actualizar_posicion(self, nueva_pos):
        """Actualiza la posición en Prolog"""
        self.posicion = nueva_pos
        try:
            self.prolog.retractall(f"posicion_actual({self.id}, _)")
            self.prolog.assertz(f"posicion_actual({self.id}, {self.posicion})")
        except:
            pass
    
    def _mover_perimetro(self, mapa):
        """Movimiento típico del guardian del perímetro"""
        movimientos = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = random.choice(movimientos)
        x, y = self.posicion
        nueva_x = max(0, min(mapa.ancho - 1, x + dx))
        nueva_y = max(0, min(mapa.alto - 1, y + dy))
        return (nueva_x, nueva_y)
    
    def _mover_aleatorio(self, mapa):
        """Movimiento aleatorio para exploración"""
        x, y = self.posicion
        nueva_x = max(0, min(mapa.ancho - 1, x + random.randint(-1, 1)))
        nueva_y = max(0, min(mapa.alto - 1, y + random.randint(-1, 1)))
        return (nueva_x, nueva_y)
    
    def _mover_centro(self, mapa):
        """Movimiento hacia el centro"""
        x, y = self.posicion
        centro_x, centro_y = mapa.ancho // 2, mapa.alto // 2
        
        dx = 1 if x < centro_x else -1 if x > centro_x else 0
        dy = 1 if y < centro_y else -1 if y > centro_y else 0
        
        nueva_x = max(0, min(mapa.ancho - 1, x + dx))
        nueva_y = max(0, min(mapa.alto - 1, y + dy))
        return (nueva_x, nueva_y)
    
    def _mover_observador(self, mapa):
        """Movimiento mínimo del observador"""
        if random.random() < 0.8:  # 80% de no moverse
            return self.posicion
        
        movimientos = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dx, dy = random.choice(movimientos)
        x, y = self.posicion
        nueva_x = max(0, min(mapa.ancho - 1, x + dx))
        nueva_y = max(0, min(mapa.alto - 1, y + dy))
        return (nueva_x, nueva_y)
    
    def _investigar_amenaza(self, mapa):
        """Movimiento para investigar amenazas"""
        x, y = self.posicion
        nueva_x = max(0, min(mapa.ancho - 1, x + random.randint(-1, 1)))
        nueva_y = max(0, min(mapa.alto - 1, y + random.randint(-1, 1)))
        return (nueva_x, nueva_y)
    
    def _pedir_ayuda(self, mapa):
        """No se mueve cuando pide ayuda"""
        return self.posicion
    
    def necesita_ayuda(self):
        """Verifica si el agente necesita ayuda"""
        try:
            query = f"necesita_ayuda({self.id})"
            return bool(list(self.prolog.query(query)))
        except:
            return False
