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
- `services/decision/`: policy minima para pruebas de IA
- `services/transcription/`: interfaz de transcripcion
- `services/access_control/`: simulacion segura de apertura
- `services/tts/`: respuestas cortas reutilizables
- `services/telephony/`: espacio reservado para SIP / audio session handling

## Execution Modes

- `decision-only`: prueba policy desde texto
- `dry-run`: simula decision y apertura sin tocar hardware
- `audio-only`: reservado para pruebas futuras con audio real
- `full-flow`: reservado para la integracion futura

## Safety

- nada del scaffold inicial debe abrir el porton real
- el acceso inicial debe operar solo en `dry-run`
- la configuracion debe vivir en archivos ejemplo o variables de entorno
