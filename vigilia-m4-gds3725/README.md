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

## Estado

Este scaffold no abre portones reales.
La integracion SIP/audio real del `GDS3725` queda para la siguiente etapa, pero ya existe una simulacion de sesion local para probar el flujo sin Asterisk.
