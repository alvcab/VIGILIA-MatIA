# vigilia-m4-gds3725

Nuevo stack de VIGILIA para la etapa `Mac mini M4 + GDS3725`.

Este repo nace separado del prototipo Dahua/Asterisk para mantener una arquitectura mas limpia, enfocada en:

- audio confiable
- modos de prueba seguros
- servicios desacoplados
- menor complejidad operativa

## Objetivo

Recibir audio desde el intercom, transcribirlo, tomar una decision y responder de forma segura.

## Principios

- separar telephony, transcription, decision, TTS y access control
- soportar `dry-run` desde el dia 1
- no depender de apertura real para probar IA
- no asumir Asterisk como requisito base

## Modos iniciales

- `decision-only`: evalua policy desde texto
- `dry-run`: simula flujo y apertura
- `session-replay`: simula una sesion de intercom sin Asterisk
- `audio-file`: simula una sesion de audio real desde un WAV local
- `sip-preview`: muestra el contrato SIP esperado para conectar el `GDS3725`
- `sip-session`: simula el lifecycle SIP de una llamada sin Asterisk
- `baresip-preview`: muestra como quedaria la integracion recomendada con `baresip`
- `hybrid-decision`: combina reglas y guia lista para una futura capa de modelo
- `conversation-turn`: prueba continuidad de sesion y segundo turno
- `department-watch-once`: procesa respuestas de autorizacion de departamento por sesion

## Estructura

- `app/`: entrypoint y configuracion
- `services/`: bloques funcionales
- `config/`: ejemplos de configuracion
- `docs/`: arquitectura y flujos
- `scripts/`: helpers de prueba
- `tests/`: validacion automatizada

## Ejecutar

```bash
python3 -m app.main --mode decision-only --text "hola vengo donde Alvaro"
```

```bash
python3 -m app.main --mode dry-run --text "abre por favor"
```

```bash
python3 -m app.main --mode session-replay --caller-id "gds-front-door" --text "hola"
```

```bash
python3 -m app.main --mode audio-file --caller-id "gds-front-door" --audio-file runtime/sample.wav
```

Ese modo ahora evalua:

- transcripcion
- decision
- guia de modelo
- accion `dry-run`

La transcripcion se controla con:

```bash
VIGILIA_TRANSCRIPTION_BACKEND=sidecar
```

o:

```bash
VIGILIA_TRANSCRIPTION_BACKEND=whisper-local
VIGILIA_WHISPER_MODEL=tiny
```

```bash
python3 -m app.main --mode sip-preview --caller-id "gds-front-door"
```

```bash
python3 -m app.main --mode sip-session --caller-id "gds-front-door"
```

```bash
python3 -m app.main --mode baresip-preview --caller-id "gds-front-door"
```

```bash
python3 -m app.main --mode hybrid-decision --text "abre por favor donde Alvaro"
```

Ese modo ya entrega una respuesta generada por un backend de modelo simulado, sin depender aun de un LLM real.

```bash
python3 -m app.main --mode conversation-turn --session-id demo-1 --text "hola"
python3 -m app.main --mode conversation-turn --session-id demo-1 --text "vengo donde Alvaro"
```

El backend se controla con:

```bash
VIGILIA_MODEL_BACKEND=stub
```

o:

```bash
VIGILIA_MODEL_BACKEND=echo
```

O con Ollama local:

```bash
VIGILIA_MODEL_BACKEND=ollama
VIGILIA_OLLAMA_MODEL=vigilia-mini
VIGILIA_OLLAMA_TIMEOUT_SECONDS=8
```

```bash
./scripts/prepare_baresip_runtime.sh
./scripts/run_baresip_local.sh
```

```bash
python3 -m app.main --mode baresip-inbox --audio-file runtime/baresip/inbox/demo.wav --caller-id gds-front-door
```

```bash
python3 -m app.main --mode baresip-watch-once
```

```bash
python3 -m app.main --mode department-watch-once
```

El contrato esperado del inbox esta descrito en [docs/baresip-inbox-contract.md](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/docs/baresip-inbox-contract.md:1).

La integracion recomendada para que `baresip` deposite `WAV` y metadata de forma
atomica esta descrita en [docs/integracion-baresip-inbox.md](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/docs/integracion-baresip-inbox.md:1).

Cuando `MatIA` necesita llamar a un departamento, el pipeline deja una solicitud en:

- `runtime/baresip/department_authorization/requests`

Y luego consume respuestas estructuradas desde:

- `runtime/baresip/department_authorization/responses`

guardando resultados en:

- `runtime/baresip/department_authorization/processed`

## Estado

Este scaffold no abre portones reales.
La pila SIP real del `GDS3725` todavia no esta conectada, pero el contrato de sesion/audio sin Asterisk ya queda definido y se puede probar desde WAV local.

`baresip` todavia no es obligatorio para validar el scaffold, pero el repo ya deja listos los archivos `config` y `accounts` para la siguiente etapa.

## Rol de MatIA

En la arquitectura objetivo, `MatIA` sera el agente conversacional principal.

- `MatIA` habla con la visita
- VIGILIA aplica policy y autorizacion
- `baresip` queda como puente SIP/audio

El detalle esta en [docs/matia-como-agente-conversacional.md](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/docs/matia-como-agente-conversacional.md:1).
