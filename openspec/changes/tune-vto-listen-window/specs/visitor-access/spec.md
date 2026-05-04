## MODIFIED Requirements

### Requisito: Entregar retroalimentacion al visitante

#### Escenario: Captura inmediata de voz en el flujo real del VTO

- DADO que el VTO real no reproduce de forma confiable el audio entrante desde Asterisk
- CUANDO el sistema atiende una llamada real del VTO
- ENTONCES el flujo puede omitir el saludo y tono del PBX antes de grabar
- Y prioriza una ventana de escucha mas inmediata y mas larga para captar la voz del visitante
