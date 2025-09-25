% Reglas de decisión muy simples y robustas
decision_agente(Agente, Accion) :-
    tiene_perfil(Agente, Perfil),
    posicion_actual(Agente, Pos),
    (nivel_amenaza(Pos, Nivel) -> true ; Nivel = 0.0),
    regla_simple(Perfil, Nivel, Accion).

% Reglas simples por perfil
regla_simple(guardian, Nivel, patrullar_conservador) :- Nivel < 0.4.
regla_simple(guardian, Nivel, investigar_cauteloso) :- Nivel >= 0.4, Nivel < 0.7.
regla_simple(guardian, Nivel, pedir_ayuda) :- Nivel >= 0.7.

regla_simple(explorador, _, explorar_activo).
regla_simple(explorador, Nivel, acercarse_amenaza) :- Nivel >= 0.3.
regla_simple(explorador, Nivel, enfrentar_directo) :- Nivel >= 0.6.

regla_simple(soporte, Nivel, esperar_central) :- Nivel < 0.3.
regla_simple(soporte, Nivel, moverse_apoyar) :- Nivel >= 0.3.

% Fallback para cualquier caso
regla_simple(_, _, esperar).
