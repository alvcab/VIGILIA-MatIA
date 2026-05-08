# Delta de intercom-routing

## Requisitos Modificados

### Requisito: Aceptar trafico SIP del dispositivo de citofonia configurado

- El sistema DEBE aceptar trafico SIP del intercom configurado mediante un adaptador ligero de telefonia, sin requerir Asterisk como control principal.

#### Escenario: Endpoint SIP del intercom configurado

- DADO que el `GDS3725` o intercom equivalente esta configurado para entregar la sesion al stack local
- CUANDO el adaptador SIP recibe la llamada entrante
- ENTONCES la sesion queda disponible para el pipeline de VIGILIA

### Requisito: Enrutar llamadas del VTO al pipeline conversacional

- El sistema DEBE enrutar las llamadas entrantes a un contrato de runtime consumible por `MatIA` y VIGILIA.

#### Escenario: Audio entrante depositado en inbox

- DADO que el adaptador de telefonia recibe una llamada del intercom
- CUANDO termina la captura del audio inicial
- ENTONCES el sistema deposita `WAV` y metadata en `runtime/baresip/inbox`
- Y deja ese artefacto listo para el pipeline conversacional

### Requisito: Mantener el contrato de autorizacion de departamento por sesion

- El sistema DEBE enrutar las solicitudes de autorizacion de departamento como artefactos de runtime por `session_id`.

#### Escenario: VIGILIA solicita contacto con departamento

- DADO que VIGILIA decide `contact_department` para una sesion
- CUANDO el pipeline persiste los artefactos de integracion
- ENTONCES escribe una solicitud en `runtime/baresip/department_authorization/requests`

#### Escenario: Respuesta de departamento reinyectada a la sesion

- DADO que existe una respuesta estructurada para una sesion pendiente
- CUANDO corre el watcher de respuestas de departamento
- ENTONCES el sistema reinyecta `approved`, `denied` o `no_response` en la memoria de esa sesion
- Y guarda un resultado procesado en runtime
