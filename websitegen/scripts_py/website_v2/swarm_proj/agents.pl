% Hechos dinámicos (se modifican durante la ejecución)
:- dynamic posicion/3.
:- dynamic velocidad/3.
:- dynamic vecino/3.

% Energy decays each step
decay_energy(AgentID, Decay) :-
    energia(AgentID, E),
    NewE is E - Decay,
    retract(energia(AgentID, _)),
    assertz(energia(AgentID, NewE)).

% Gain energy when near food (example rule)
gain_energy(AgentID, Amount) :-
    posicion(AgentID, X, Y),
    comida(X, Y),  % Hypothetical food fact
    energia(AgentID, E),
    NewE is E + Amount,
    retract(energia(AgentID, _)),
    assertz(energia(AgentID, NewE)).

% Rule to update agent direction using flocking rules (alignment, cohesion, separation)
actualizar_direccion(AgentID, NewVX, NewVY) :-
    % Alignment: Average velocity of neighbors
    (   findall((VX, VY), 
                (vecino(AgentID, OtherID, _), velocidad(OtherID, VX, VY)), 
                VecinosVelocidades),
        VecinosVelocidades \= [],
        sum_velocidades(VecinosVelocidades, SumVX, SumVY),
        length(VecinosVelocidades, N),
        NewAlignVX is SumVX / N,
        NewAlignVY is SumVY / N
    ;   NewAlignVX = 0, NewAlignVY = 0), % Default if no neighbors

    % Cohesion: Move toward center of mass of neighbors
    (   findall((X, Y), 
                (vecino(AgentID, OtherID, _), posicion(OtherID, X, Y)), 
                VecinosPosiciones),
        VecinosPosiciones \= [],
        sum_posiciones(VecinosPosiciones, SumX, SumY),
        length(VecinosPosiciones, M),
        CentroX is SumX / M,
        CentroY is SumY / M,
        posicion(AgentID, MyX, MyY),
        NewCohesionVX is (CentroX - MyX) * 0.01,
        NewCohesionVY is (CentroY - MyY) * 0.01
    ;   NewCohesionVX = 0, NewCohesionVY = 0),

    % Separation: Avoid collisions (repulsion from close neighbors)
    (   findall((DX, DY), 
                (vecino(AgentID, OtherID, Dist), 
                 Dist < 3, % Separation threshold
                 posicion(OtherID, X, Y),
                 posicion(AgentID, MyX, MyY),
                 DX is MyX - X,
                 DY is MyY - Y), 
                Desplazamientos),
        Desplazamientos \= [],
        sum_velocidades(Desplazamientos, SumSepVX, SumSepVY),
        NewSepVX is SumSepVX * 0.05,
        NewSepVY is SumSepVY * 0.05
    ;   NewSepVX = 0, NewSepVY = 0),

    % Combine rules (weighted sum)
    NewVX is NewAlignVX + NewCohesionVX + NewSepVX,
    NewVY is NewAlignVY + NewCohesionVY + NewSepVY.

% Helper predicates
sum_velocidades([], 0, 0).
sum_velocidades([(VX, VY)|T], SumX, SumY) :-
    sum_velocidades(T, TX, TY),
    SumX is VX + TX,
    SumY is VY + TY.

sum_posiciones([], 0, 0).
sum_posiciones([(X, Y)|T], SumX, SumY) :-
    sum_posiciones(T, TX, TY),
    SumX is X + TX,
    SumY is Y + TY.
