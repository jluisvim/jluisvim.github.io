% Reglas básicas de toma de decisiones - VERSION CORREGIDA
decision_agente(Agente, Accion, Prioridad) :-
    tiene_perfil(Agente, Perfil),
    estado_actual(Agente, Estado),
    posicion_actual(Agente, Pos),
    nivel_amenaza(Pos, NivelAmenaza),
    estado_salud(Agente, Salud),
    regla_comportamiento(Perfil, Estado, NivelAmenaza, Salud, Accion, Prioridad).

% Guardian del perímetro
regla_comportamiento(guardian_perimetro, normal, Nivel, Salud, patrullar_perimetro, 1) :- 
    Nivel < 0.3, Salud > 0.6.
regla_comportamiento(guardian_perimetro, normal, Nivel, _, investigar_amenaza, 3) :- 
    Nivel >= 0.3, Nivel < 0.7.
regla_comportamiento(guardian_perimetro, normal, Nivel, _, pedir_ayuda, 5) :- 
    Nivel >= 0.7.
regla_comportamiento(guardian_perimetro, herido, _, Salud, pedir_ayuda, 5) :- 
    Salud < 0.5.

% Explorador de riesgo
regla_comportamiento(explorador_riesgo, normal, _, _, explorar_puntos_calientes, 2).
regla_comportamiento(explorador_riesgo, normal, Nivel, _, acercarse_amenaza, 4) :- 
    Nivel >= 0.4.
regla_comportamiento(explorador_riesgo, normal, Nivel, _, enfrentar_amenaza, 6) :- 
    Nivel >= 0.7.

% Coordinador
regla_comportamiento(coordinador, normal, _, _, optimizar_rutas, 2).
regla_comportamiento(coordinador, normal, Nivel, _, redistribuir_agentes, 4) :- 
    Nivel >= 0.5.
regla_comportamiento(coordinador, normal, Nivel, _, coordinar_defensa, 6) :- 
    Nivel >= 0.8.

% Soporte rápido
regla_comportamiento(soporte_rapido, normal, Nivel, _, esperar_central, 1) :- 
    Nivel < 0.4.
regla_comportamiento(soporte_rapido, normal, Nivel, _, moverse_a_amenaza, 5) :- 
    Nivel >= 0.4.

% Observador
regla_comportamiento(observador, normal, _, _, monitorear_zona, 1).
regla_comportamiento(observador, normal, Nivel, _, reportar_anomalias, 3) :- 
    Nivel >= 0.3.
