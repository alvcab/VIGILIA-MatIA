# Contrato Del Inbox De Baresip

Este documento define el formato esperado de los archivos que `baresip` deja en `runtime/baresip/inbox`.

## Archivos Esperados

Por cada llamada procesable, VIGILIA espera al menos:

- `nombre.wav`

Y opcionalmente:

- `nombre.txt`
- `nombre.json`

## 1. `nombre.wav`

Audio capturado de la llamada.

Ejemplo:

- `demo.wav`

## 2. `nombre.txt`

Transcript controlado para pruebas reproducibles.

Se usa sobre todo en tests o simulaciones locales.

Ejemplo:

- `demo.txt`

Contenido:

```text
hola, vengo donde Alvaro
```

## 3. `nombre.json`

Metadata de la llamada.

Ejemplo:

- `demo.json`

Formato esperado:

```json
{
  "caller_id": "front-door",
  "device_label": "gds3725",
  "transport": "sip-udp",
  "received_at": "2026-05-06T18:30:00+00:00"
}
```

## Campos Minimos Recomendados

- `caller_id`: identificador simple del origen
- `device_label`: nombre del dispositivo
- `transport`: por ejemplo `sip-udp`
- `received_at`: timestamp ISO 8601

## Campos Opcionales Futuramente Utiles

- `call_id`
- `remote_uri`
- `local_uri`
- `codec`
- `audio_duration_seconds`

## Comportamiento Si Falta Metadata

Si el `.json` no existe:

- VIGILIA sigue pudiendo procesar el `.wav`
- `caller_id` cae al valor por defecto del pipeline

## Objetivo Del Contrato

Hacer que el puente:

`baresip -> inbox -> VIGILIA`

sea simple, trazable y estable, sin depender de Asterisk.
