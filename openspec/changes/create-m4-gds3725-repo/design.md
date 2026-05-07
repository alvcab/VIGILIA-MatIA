# Design: `vigilia-m4-gds3725`

## Decision

Se crea un nuevo scaffold de repositorio para la futura plataforma `Mac mini M4 + GDS3725`.

La arquitectura objetivo asume:

- transporte de audio / intercom desacoplado
- capa de transcripcion persistente
- capa de decision independiente
- capa de TTS separada
- capa de apertura con `dry-run`

## Why No Asterisk First

La motivacion principal es bajar complejidad estructural.

El nuevo repo no asume Asterisk como base obligatoria. Puede agregarse despues como adaptador de transporte si el `GDS3725` lo requiere, pero no debe ser el centro del diseño.

## Initial Components

- `app/`: entrypoint y paths de runtime
- `services/decision/`: policy inicial en espanol para pruebas de IA
- `services/transcription/`: interfaz de transcripcion
- `services/access_control/`: simulacion segura de apertura
- `services/tts/`: respuestas cortas reutilizables
- `services/telephony/`: contratos de SIP / audio session handling

## Execution Modes

- `decision-only`: prueba policy desde texto
- `dry-run`: simula decision y apertura sin tocar hardware
- `audio-only`: reservado para pruebas futuras con audio real
- `full-flow`: reservado para la integracion futura

## Initial IA Policy Scope

La primera policy del scaffold debe ser suficiente para distinguir casos basicos de intercom:

- saludo simple
- pedido explicito de apertura
- visita con residente mencionado
- delivery o paquete
- audio o texto insuficiente

## Authorization And Follow-Up

La policy debe poder apoyarse en reglas de residentes y preparar un segundo turno:

- reglas por residente para apertura o confirmacion
- siguiente paso sugerido para la conversacion
- contexto estructurado para una futura capa de prompts/modelo

## Session Conversation History

El scaffold agrega un historial de conversacion por sesion:

- almacenamiento simple en `runtime`
- seguimiento de turnos
- continuidad de contexto entre mensajes de una misma interaccion

## End-To-End Audio Evaluation

La prueba `audio-file` debe poder recorrer:

- ingesta de audio
- transcripcion
- policy deterministica
- capa hibrida de modelo

para validar el comportamiento de IA sin requerir todavia una sesion SIP real.

## Transcription Backends

La capa de transcripcion debe soportar:

- `sidecar` para pruebas reproducibles basadas en texto controlado
- `whisper-local` para pruebas locales mas realistas
- fallback seguro a transcript vacio si el backend real no esta disponible

## Safety

- nada del scaffold inicial debe abrir el porton real
- el acceso inicial debe operar solo en `dry-run`
- la configuracion debe vivir en archivos ejemplo o variables de entorno

## First No-Asterisk Interface

Como primer paso concreto sin Asterisk, el scaffold agrega:

- configuracion SIP del dispositivo / cuenta destino
- sesion de intercom con referencia a archivo de audio
- adaptador de ingesta desde WAV para pruebas locales
- planificador de endpoint SIP y URIs para el `GDS3725`
- contrato de transporte SIP con lifecycle de llamada
- adaptador de transporte pensado para `baresip` como proceso externo

Esto no reemplaza aun una pila SIP completa, pero define el contrato de integracion real que luego podra conectarse al `GDS3725`.

## Baresip Runtime Scaffold

El scaffold agrega:

- generacion de `config` y `accounts`
- layout de runtime para `baresip`
- script de arranque local

Esto permite preparar el `Mac mini` para la siguiente etapa sin requerir todavia llamada SIP real en esta fase.

## Baresip Inbox Integration

Para conectar `baresip` con VIGILIA sin PBX:

- `baresip` deja audio y metadata en un inbox de runtime
- VIGILIA consume ese inbox
- el mismo pipeline de transcripcion, decision y modelo procesa la llamada

## Baresip Watcher

El scaffold agrega un watcher no bloqueante:

- procesa WAVs nuevos del inbox
- guarda resultados en `runtime/baresip/processed`
- evita reprocesar archivos ya resueltos

## MatIA As Conversational Agent

La arquitectura objetivo se aclara aun mas:

- `MatIA` sera el agente conversacional principal
- VIGILIA mantiene la policy y la autorizacion
- `baresip` mantiene el transporte SIP/audio

Esto implica que el inbox de `baresip` debe entenderse principalmente como:

- canal de integracion simple
- replay de sesiones
- diagnostico

y no como el cerebro definitivo del flujo conversacional.

## Internal Turn Interface For MatIA

El scaffold agrega una interfaz Python interna por turno:

- `TurnEvaluator.evaluate_turn(...)`

Su objetivo es que `MatIA` pueda invocar la policy de VIGILIA sin pasar por CLI,
sin depender del transporte SIP y con estado de conversacion persistente por sesion.

## Trusted Face Shortcut

Si el `GDS3725` entrega un match facial confiable para un residente habilitado:

- el saludo inicial puede sonar primero
- y luego VIGILIA debe devolver apertura inmediata

Esto evita obligar a `MatIA` a continuar un dialogo innecesario cuando el dispositivo
ya entrego una identidad residente suficientemente confiable.

## Department Authorization Flow

Cuando no exista un rostro confiable y la visita ya identifique a un residente o departamento,
`MatIA` debe escalar desde la conversacion hacia una autorizacion del departamento.

El flujo se separa en dos etapas:

- `contact_department`: `MatIA` informa a la visita que intentara llamar al departamento
- respuesta del departamento: VIGILIA recibe un resultado estructurado de autorizacion

Resultados esperados:

- `approved`: abrir el porton
- `denied`: rechazar con un mensaje breve
- `no_response`: informar que no hubo respuesta del departamento

## Registered Visit Fallback Code

Si no hay respuesta del departamento, pero `MatIA` ya tiene registrada una visita valida
para esa sesion o departamento, el sistema no debe abrir de inmediato.

En ese caso:

- solicita un codigo de autorizacion de 4 digitos
- valida ese codigo dentro de la misma memoria de sesion
- solo abre si el codigo coincide con el esperado

Esto permite un fallback seguro cuando la llamada al departamento no responde,
sin degradar a una apertura por simple reclamo verbal del visitante.

## Department Authorization Runtime Contract

Para desacoplar a `MatIA` del mecanismo exacto de llamada al departamento,
el scaffold agrega un runtime de autorizacion con tres carpetas:

- `department_authorization/requests`
- `department_authorization/responses`
- `department_authorization/processed`

`MatIA` y el pipeline generan una solicitud estructurada cuando la decision es
`contact_department`. Luego otro integrador puede producir un evento de respuesta
por sesion con `approved`, `denied` o `no_response`.

VIGILIA consume ese evento como una nueva entrada de sesion, sin depender de flags
manuales del CLI ni de acoplar la policy a una implementacion concreta de llamada SIP.

Para la etapa actual, el scaffold agrega tambien dos operaciones basicas:

- listar solicitudes pendientes
- emitir una respuesta estructurada por `session_id`

Eso permite usar el flujo con un operador humano, una app futura o un softphone
sin cambiar la policy de `MatIA`.

El camino preferido, sin embargo, pasa a ser que `MatIA` produzca la respuesta
de departamento por interfaz Python directa.

Para eso el pipeline agrega una operacion que:

- recibe `session_id`
- recibe `approved`, `denied` o `no_response`
- registra el evento de respuesta
- lo procesa de inmediato contra la memoria de sesion

De esa forma el runtime por archivos sigue existiendo para integracion y fallback,
pero `MatIA` ya no depende del CLI ni del watcher como mecanismo primario.

## MatIA Voice Layer

Antes de cerrar la llamada real al departamento, el scaffold separa la voz de `MatIA`
del transporte SIP.

Se definen al menos dos perfiles:

- `matia-visitor-es-cl`
- `matia-department-es-cl`

Y cuando la decision es `contact_department`, el pipeline prepara un
`call_plan_for_matia` con:

- texto de apertura al departamento
- pregunta de autorizacion
- estrategia para `no_response`
- perfil de voz recomendado

Esto permite que la siguiente integracion de llamada saliente por `baresip`
se apoye en un contrato ya estable de conversacion, en vez de improvisar
texto desde la capa de telephony.

## Outgoing Department Call Via Baresip

La siguiente capa del scaffold define tambien un preview concreto de llamada saliente:

- el residente puede declarar un `department_sip_uri`
- el pipeline construye un `baresip_outgoing_call_preview`
- ese preview incluye `from_uri`, `to_uri` e `invite`

Esto no ejecuta aun la llamada real, pero deja fijado el contrato tecnico para que
`MatIA` y `baresip` coordinen una llamada al departamento sin reinterpretar la policy.

Ademas del preview del `invite`, el contrato agrega un preview operativo para el
proceso `baresip`:

- comando de arranque con `-f <config>`
- comando interactivo `/dial <target_uri>`
- secuencia esperada de `hangup` y `quit`

Con eso la futura integracion real no parte desde cero y `MatIA` puede delegar la
llamada saliente sobre una interfaz ya estabilizada.

## Python Runner For Outgoing Department Calls

El scaffold agrega ademas un runner controlado desde Python para esa llamada saliente.

Objetivos de esta capa:

- encapsular el uso de `subprocess`
- permitir `dry-run` como modo por defecto
- producir un resultado estructurado para `MatIA`
- separar el contrato de llamada de la ejecucion del proceso

En esta etapa, el runner ya puede:

- recibir el `startup_command`
- enviar la secuencia de `stdin`
- devolver `stdout`, `stderr` y `exit_code`
- mantener una sesion saliente en memoria mientras `MatIA` conversa con el departamento
- cerrar esa sesion de forma explicita cuando la llamada termina

pero sigue usandose de forma segura y simulable en tests, sin depender de una llamada
SIP real durante el desarrollo.

## Persistent MatIA Call Service

Para que la llamada saliente no dependa de una sola invocacion corta de CLI,
el scaffold agrega un servicio persistente pensado para vivir dentro del proceso
de `MatIA`.

Ese servicio:

- conserva la sesion saliente en memoria
- delega el transporte al runner de `baresip`
- guarda snapshots de estado en runtime
- separa `active` y `completed`
- agrega una cola simple de solicitudes `queued`
- puede correr en una pasada como host local del proceso de `MatIA`

Esto permite que `MatIA` modele mejor el flujo real:

- encolar una llamada saliente
- iniciar la llamada al departamento
- consultar el estado de la sesion
- cerrarla al terminar

En esta etapa, la persistencia real del proceso sigue siendo responsabilidad del
host donde viva `MatIA`, pero el contrato de servicio ya queda preparado.
