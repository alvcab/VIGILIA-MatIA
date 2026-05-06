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
