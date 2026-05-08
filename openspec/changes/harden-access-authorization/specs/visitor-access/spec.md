# Delta de visitor-access

## Requisitos Modificados

### Requisito: Restringir la apertura del porton a decisiones positivas

#### Escenario: Match facial confiable sin residente resoluble

- DADO que la metadata del reconocimiento facial marca un `face_match_trusted`
- Y el `resident_id` o nombre entregado no resuelve a un residente conocido del directorio
- CUANDO el flujo hibrido evalua la llamada
- ENTONCES el sistema no abre el porton
- Y degrada el resultado facial a no-match

#### Escenario: Aprobacion de departamento fuera de contexto

- DADO que llega una respuesta de departamento con estado `approved`, `denied` o `no_response`
- Y la sesion no estaba esperando una autorizacion de departamento
- CUANDO el watcher procesa esa respuesta
- ENTONCES el sistema la trata como invalida
- Y no abre el porton

#### Escenario: Respuesta hablada ambigua del departamento

- DADO que la transcripcion del departamento contiene palabras parciales que incluyen tokens de aprobacion o rechazo
- CUANDO el sistema interpreta esa respuesta
- ENTONCES solo considera marcadores completos y contiguos
- Y no promueve coincidencias parciales accidentales a una autorizacion valida
