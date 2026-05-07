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
  "received_at": "2026-05-06T18:30:00+00:00",
  "face_match": {
    "resident_id": "alvaro",
    "display_name": "Alvaro",
    "confidence": "high",
    "trusted": true
  }
}
```

## Campos Minimos Recomendados

- `caller_id`: identificador simple del origen
- `device_label`: nombre del dispositivo
- `transport`: por ejemplo `sip-udp`
- `received_at`: timestamp ISO 8601
- `face_match`: bloque opcional con informacion facial del dispositivo

Dentro de `face_match`:

- `resident_id`: id del residente reconocido por el dispositivo
- `display_name`: nombre visible del residente reconocido
- `confidence`: etiqueta de confianza, por ejemplo `high`
- `trusted`: indica si el dispositivo considera el match facial confiable

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

## Comportamiento Con Rostro Confiable

Si la metadata incluye:

- `face_match.trusted: true`
- y un residente reconocido valido

VIGILIA puede devolver apertura inmediata en el pipeline de `MatIA`, sin requerir
mas aclaraciones conversacionales.

## Compatibilidad Hacia Atras

El pipeline actual tambien acepta, por compatibilidad, estas claves planas:

- `face_match_resident_id`
- `face_match_display_name`
- `face_match_confidence`
- `face_match_trusted`

Pero el formato recomendado desde ahora en adelante es el bloque anidado
`face_match`.

## Objetivo Del Contrato

Hacer que el puente:

`baresip -> inbox -> VIGILIA`

sea simple, trazable y estable, sin depender de Asterisk.
