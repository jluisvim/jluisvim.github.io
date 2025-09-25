% Reglas básicas de coordinación - VERSION SIMPLIFICADA
necesita_ayuda(Agente) :-
    posicion_actual(Agente, Pos),
    nivel_amenaza(Pos, Nivel),
    Nivel > 0.6.  % Umbral fijo simplificado

% Predicado de distancia básico
distancia((X1, Y1), (X2, Y2), Dist) :-
    DiffX is abs(X1 - X2),
    DiffY is abs(Y1 - Y2),
    Dist is sqrt(DiffX * DiffX + DiffY * DiffY).
