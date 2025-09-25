% Reglas básicas para cambio de roles - VERSION SIMPLIFICADA
puede_ayudar(AgenteAyudante, AgenteNecesitado) :-
    necesita_ayuda(AgenteNecesitado),
    posicion_actual(AgenteAyudante, Pos1),
    posicion_actual(AgenteNecesitado, Pos2),
    distancia(Pos1, Pos2, Dist),
    Dist =< 3,  % Radio de ayuda
    estado_salud(AgenteAyudante, Salud),
    Salud > 0.7.

perfil_compatible_ayuda(soporte_rapido).
perfil_compatible_ayuda(coordinador).
