% Coordinación básica entre 3 agentes
necesita_ayuda(Agente) :-
    posicion_actual(Agente, Pos),
    nivel_amenaza(Pos, Nivel),
    Nivel > 0.6.

agente_cercano(Agente1, Agente2) :-
    Agente1 \= Agente2,
    posicion_actual(Agente1, Pos1),
    posicion_actual(Agente2, Pos2),
    distancia_manhattan(Pos1, Pos2, Distancia),
    Distancia =< 4.

distancia_manhattan((X1, Y1), (X2, Y2), Distancia) :-
    Distancia is abs(X1 - X2) + abs(Y1 - Y2).
