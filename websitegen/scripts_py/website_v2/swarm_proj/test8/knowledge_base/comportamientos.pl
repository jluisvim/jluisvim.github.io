% Perfiles comportamentales básicos para 3 agentes
perfil(guardian, [
    objetivo(proteger_area),
    estrategia(patrulla_sistematica),
    movimiento(conservador),
    radio_accion(3),
    umbral_riesgo(0.6)
]).

perfil(explorador, [
    objetivo(investigar_zonas),
    estrategia(busqueda_activa),
    movimiento(arriesgado),
    radio_accion(5),
    umbral_riesgo(0.3)
]).

perfil(soporte, [
    objetivo(apoyar_agentes),
    estrategia(respuesta_rapida),
    movimiento(equilibrado),
    radio_accion(4),
    umbral_riesgo(0.5)
]).
