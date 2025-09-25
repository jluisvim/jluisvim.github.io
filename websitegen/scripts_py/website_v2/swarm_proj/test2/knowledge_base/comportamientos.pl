% Definición de perfiles comportamentales básicos
perfil(guardian_perimetro, [
    objetivo(proteger_limites),
    estrategia(patrulla_sistematica),
    movimiento(conservador),
    radio_accion(3),
    umbral_riesgo(0.7)
]).

perfil(explorador_riesgo, [
    objetivo(investigar_anomalias),
    estrategia(busqueda_activa),
    movimiento(arriesgado),
    radio_accion(6),
    umbral_riesgo(0.3)
]).

perfil(coordinador, [
    objetivo(optimizar_recursos),
    estrategia(comando_central),
    movimiento(estrategico),
    radio_accion(4),
    umbral_riesgo(0.5)
]).

perfil(soporte_rapido, [
    objetivo(responder_emergencias),
    estrategia(respuesta_rapida),
    movimiento(rapido),
    radio_accion(5),
    umbral_riesgo(0.6)
]).

perfil(observador, [
    objetivo(vigilancia_pasiva),
    estrategia(monitoreo),
    movimiento(minimo),
    radio_accion(8),
    umbral_riesgo(0.4)
]).
