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
./scripts/prepare_baresip_runtime.sh
./scripts/run_baresip_local.sh
```

## Estado

Este scaffold no abre portones reales.
La pila SIP real del `GDS3725` todavia no esta conectada, pero el contrato de sesion/audio sin Asterisk ya queda definido y se puede probar desde WAV local.

`baresip` todavia no es obligatorio para validar el scaffold, pero el repo ya deja listos los archivos `config` y `accounts` para la siguiente etapa.
