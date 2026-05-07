# MatIA como agente conversacional principal

Este documento fija el reparto de responsabilidades para la etapa
`Mac mini M4 + GDS3725`.

La idea central es simple:

- `MatIA` habla con la visita
- `VIGILIA` decide si una accion sensible esta autorizada
- `baresip` transporta audio y metadata SIP

## Objetivo

Evitar que la capa conversacional y la capa de autorizacion queden mezcladas.

Eso nos da tres beneficios:

- conversaciones mas naturales sin meter reglas duras dentro del transporte SIP
- decisiones de acceso mas trazables
- una separacion limpia entre experiencia conversacional y seguridad

## Reparto de roles

## MatIA

Responsabilidades:

- recibir el contexto de la llamada
- conversar con la visita
- pedir aclaraciones
- confirmar a que residente viene a ver
- contactar al departamento cuando VIGILIA lo indique
- recoger la respuesta del departamento y reenviarla a VIGILIA
- responder con voz
- mantener el hilo conversacional de la sesion
- usar un perfil de voz distinto para la visita y para el departamento

`MatIA` no deberia abrir el porton directamente.

## VIGILIA

Responsabilidades:

- resolver residentes y aliases
- aplicar reglas de autorizacion
- clasificar intenciones de acceso
- decidir `open`, `clarify`, `announce`, `escalate` o `deny`
- registrar razones y trazabilidad
- ejecutar apertura real o `dry-run`

VIGILIA es la capa de seguridad y policy.

## baresip

Responsabilidades:

- recibir la llamada SIP del `GDS3725`
- encapsular caller id y metadata de sesion
- dejar disponible el audio de la sesion
- actuar como puente fino de transporte

`baresip` no deberia decidir logica de acceso ni contenido conversacional.

## GDS3725

Responsabilidades:

- originar la sesion de intercom
- entregar audio util
- actuar como endpoint SIP del acceso

## Flujo objetivo

Flujo principal deseado:

`GDS3725 -> baresip -> MatIA -> VIGILIA policy/access-control -> respuesta -> accion`

Interpretacion:

1. el `GDS3725` origina la llamada
2. `baresip` recibe la sesion
3. `MatIA` conduce la conversacion
4. cuando hay que tomar una decision sensible, `MatIA` consulta a VIGILIA
5. VIGILIA responde con decision estructurada y razon
6. `MatIA` responde a la visita
7. si corresponde, VIGILIA abre el porton

## Atajo por rostro confiable

Si el `GDS3725` entrega un match facial confiable de un residente habilitado:

- el sistema puede saludar primero
- y despues abrir de inmediato sin pasar por el resto del dialogo

En ese caso:

- `MatIA` no necesita pedir residente ni autorizacion
- VIGILIA responde con una decision estructurada de apertura inmediata
- el motivo debe quedar trazado como match facial confiable
- y no se requiere una respuesta hablada adicional despues del saludo inicial

Si el dispositivo intento rostro y no encontro un match confiable:

- `MatIA` debe seguir la conversacion normal
- pero con una pregunta mas explicita orientada a residente o departamento
- evitando respuestas genericas que ignoren el contexto facial

## Donde entra el inbox

El inbox de `baresip` ya no se interpreta como el cerebro del sistema.

Su rol preferente pasa a ser:

- integracion asincronica simple
- replay de sesiones
- diagnostico de audio
- pruebas controladas del pipeline

Puede servir tambien como puente inicial entre `baresip` y `MatIA`, pero no debe
forzar la arquitectura final si despues conviene una integracion mas directa por
stream o por eventos de sesion.

## Contrato entre MatIA y VIGILIA

La integracion entre ambos deberia moverse sobre objetos estructurados, no sobre
texto libre solamente.

Entrada minima esperada desde `MatIA` hacia VIGILIA:

- `session_id`
- `turn_index`
- `transcript`
- `caller_id`
- `resident_hint` opcional
- `device_label`

Salida minima esperada desde VIGILIA hacia `MatIA`:

- `action`
- `should_open`
- `reason`
- `confidence`
- `resident_hint`
- `next_step`
- `follow_up_prompt`

## Principio de seguridad

La capa conversacional no debe tener autorizacion implicita para abrir.

Regla:

- `MatIA` propone o consulta
- `VIGILIA` autoriza
- `gate service` ejecuta

Aplicado al caso de departamentos:

- `MatIA` puede llamar o contactar al departamento
- `MatIA` puede recibir `approved`, `denied` o `no_response`
- pero quien transforma eso en apertura o rechazo sigue siendo VIGILIA

## Productor principal de respuestas de departamento

Desde este punto del scaffold, el productor principal de la respuesta de departamento
debe ser `MatIA`.

Eso significa que el camino preferido es:

1. `MatIA` recibe una decision `contact_department`
2. `MatIA` intenta contactar al departamento
3. `MatIA` obtiene `approved`, `denied` o `no_response`
4. `MatIA` entrega ese resultado a VIGILIA por interfaz Python
5. VIGILIA devuelve `open`, `deny_access` o `request_visit_code`

Los comandos y archivos de runtime quedan como:

- fallback operativo
- depuracion
- replay
- integracion provisional con otras piezas externas

## Voz de MatIA

La voz de `MatIA` debe tratarse como una capa separada del transporte SIP.

Perfiles iniciales:

- `matia-visitor-es-cl`
  - tono calmado y breve
  - pensado para la visita
- `matia-department-es-cl`
  - tono formal y claro
  - pensado para llamar al departamento

Cuando VIGILIA devuelve `contact_department`, el pipeline ya puede entregar a `MatIA`:

- la solicitud de autorizacion
- un `call_plan_for_matia`

Ese plan contiene:

- `opening_text`
- `authorization_question`
- `no_response_strategy`
- `voice_plan`

Y tambien puede incluir:

- `baresip_outgoing_call_preview`

Ese preview le dice a `MatIA`:

- desde que URI local saldria la llamada
- a que URI SIP del departamento deberia llamar
- como se veria el `invite` inicial por `baresip`
- como levantar el proceso de `baresip`
- que secuencia de `stdin` usar para `dial`, `hangup` y `quit`

Ademas, `MatIA` ya puede apoyarse en un runner Python en `dry-run` para esa
llamada saliente. Eso permite probar la integracion conversacional sin exigir
todavia una llamada SIP real al departamento.

Asi `MatIA` no improvisa la llamada al departamento y no mezcla policy con TTS.

## Consecuencia para este repo

`vigilia-m4-gds3725` debe evolucionar hacia:

- una integracion clara con `MatIA`
- una policy reusable desde fuera del transporte SIP
- una interfaz de decision invocable por sesion o por turno
- TTS conversacional desacoplado del mecanismo de apertura

## Consecuencia para las pruebas

Pruebas utiles desde ahora:

- `audio-file` para validar transcripcion y policy
- `conversation-turn` para validar continuidad de contexto
- `baresip-watch-once` para validar replay e inbox

Pruebas que quedan para la siguiente etapa:

- `MatIA -> VIGILIA` con decision estructurada por turno
- audio bidireccional real sobre SIP
- apertura real protegida por policy
