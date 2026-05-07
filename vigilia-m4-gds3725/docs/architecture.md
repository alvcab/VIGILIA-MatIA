# Architecture

## Summary

`vigilia-m4-gds3725` separa el flujo en servicios simples.

Flujo objetivo:

`GDS3725 -> baresip/telephony -> MatIA -> VIGILIA decision/access_control`

## Services

### Telephony

- recibe la sesion de intercom
- delimita la ventana de audio
- entrega audio limpio a la siguiente capa
- encapsula caller id, metadata SIP y referencia al audio capturado

### Transcription

- transcribe WAV o stream de audio
- reporta tiempos y fallas
- distingue audio vacio de audio util

### MatIA

- conduce la conversacion
- pide aclaraciones
- decide que decir en cada turno
- consulta a VIGILIA cuando la conversacion necesita una decision sensible
- usa un perfil de voz separado para visita y para departamento
- recibe un plan de llamada al departamento cuando VIGILIA devuelve `contact_department`

### Decision

- aplica reglas y prompts
- decide abrir, aclarar o rechazar
- usa contexto de residentes

### Access Control

- ejecuta apertura real o `dry-run`
- registra auditoria

## Modes

- `decision-only`
- `dry-run`
- `session-replay`
- `audio-only` futuro
- `full-flow` futuro

## Design Rule

Asterisk no es un requisito estructural del nuevo stack.
Si se usa, debe ser como adaptador fino, no como cerebro del sistema.

## No-Asterisk Start

La primera integracion esperada es:

- un adaptador de sesion SIP/audio o intercom
- un `call_router` propio
- servicios de decision y TTS desacoplados

Mientras llega la integracion real, `session-replay` permite validar el contrato interno de una sesion sin depender de Asterisk.

El siguiente escalon es `audio-file`, que valida el contrato de audio real usando WAV local como sustituto del stream del `GDS3725`.

El escalon siguiente es `sip-preview`, que define:

- URI local de VIGILIA
- URI esperada del `GDS3725`
- puerto, transporte y metadata de endpoint

asi el equipo puede configurarse sin introducir todavia una PBX intermedia.

Luego `sip-session` valida el lifecycle esperado de una llamada:

- register
- invite
- accept
- hangup

sin requerir aun una libreria SIP real.

La ruta recomendada actual es:

`GDS3725 -> baresip -> MatIA -> VIGILIA`

donde:

- `baresip` actua como user agent / transporte SIP ligero
- `MatIA` es el agente conversacional principal
- VIGILIA conserva policy, autorizacion, transcripcion utilitaria y control

El detalle del reparto entre `MatIA` y VIGILIA esta descrito en
[matia-como-agente-conversacional.md](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/docs/matia-como-agente-conversacional.md:1).

Si el dispositivo entrega un match facial confiable de residente conocido, VIGILIA
debe poder devolver apertura inmediata despues del saludo inicial, sin depender del
resto del flujo conversacional.

Cuando no hay rostro confiable y se requiere llamar al departamento:

- VIGILIA no decide la voz ni el transporte
- VIGILIA entrega a `MatIA` un `call_plan_for_matia`
- y un `baresip_outgoing_call_preview`
- ese plan incluye:
  - texto de apertura
  - pregunta de autorizacion
  - estrategia si no hay respuesta
  - perfil de voz del canal departamento

El `baresip_outgoing_call_preview` agrega:

- URI local de origen
- URI SIP del departamento
- preview del `invite`
- preview de ejecucion interactiva de `baresip`
- secuencia esperada de `dial`, `hangup` y `quit`

Sobre ese contrato, el scaffold agrega un runner Python que puede operar en
`dry-run` para que `MatIA` pruebe la llamada saliente sin depender todavia de un
departamento SIP real.

Ese runner tambien puede mantener una sesion saliente en memoria del proceso de
`MatIA`, lo que permite separar:

- inicio de la llamada
- intercambio de comandos durante la sesion
- cierre explicito de la llamada

Eso deja definido el contrato para la futura llamada saliente mediada por `baresip`.
