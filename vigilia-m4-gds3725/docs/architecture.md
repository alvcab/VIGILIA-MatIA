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
