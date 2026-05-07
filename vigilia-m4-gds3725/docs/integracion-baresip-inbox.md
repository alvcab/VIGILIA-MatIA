# Integracion de baresip con el inbox de VIGILIA

Este documento define como deberia escribir una integracion real de `baresip`
hacia `runtime/baresip/inbox`.

La idea no es que `baresip` conozca la logica de IA. Su responsabilidad minima es:

- capturar o exportar un `WAV`
- generar metadata de sesion
- dejar ambos archivos en el inbox
- hacerlo de forma atomica para que el watcher no lea archivos incompletos

## Objetivo

Queremos terminar con un flujo asi:

`GDS3725 -> baresip -> exportador local -> runtime/baresip/inbox -> watcher -> IA`

## Archivos esperados por sesion

Para una sesion `20260506-193000-front-door`, la integracion deberia dejar:

- `runtime/baresip/inbox/20260506-193000-front-door.wav`
- `runtime/baresip/inbox/20260506-193000-front-door.json`

Opcionalmente puede dejar tambien:

- `runtime/baresip/inbox/20260506-193000-front-door.txt`

Ese `.txt` solo sirve para pruebas o replay manual. En captura real no deberia ser
necesario.

## Orden correcto de escritura

La integracion no deberia escribir directo al nombre final si el archivo todavia se
esta generando.

Orden recomendado:

1. escribir `20260506-193000-front-door.wav.tmp`
2. escribir `20260506-193000-front-door.json.tmp`
3. renombrar `json.tmp -> .json`
4. renombrar `wav.tmp -> .wav`

La razon es simple:

- el watcher busca `*.wav`
- si el `wav` aparece antes de tiempo, VIGILIA puede procesar audio truncado
- por eso el `wav` final debe ser la ultima senal de "sesion lista"

## Metadata minima recomendada

El `.json` deberia contener al menos:

```json
{
  "session_id": "20260506-193000-front-door",
  "caller_id": "front-door",
  "device_label": "gds3725",
  "transport": "sip-udp",
  "received_at": "2026-05-06T23:30:00Z",
  "face_match": {
    "resident_id": "alvaro",
    "display_name": "Alvaro",
    "confidence": "high",
    "trusted": true
  }
}
```

Campos recomendados:

- `session_id`: id unico de la sesion
- `caller_id`: identidad SIP o etiqueta de quien llama
- `device_label`: nombre del equipo o puerta
- `transport`: por ejemplo `sip-udp`
- `received_at`: timestamp UTC de llegada
- `face_match`: bloque opcional con reconocimiento facial entregado por el dispositivo

Campos futuros posibles:

- `codec`
- `sample_rate_hz`
- `duration_seconds`
- `remote_uri`
- `local_uri`
- `capture_status`

Si el dispositivo entrega reconocimiento facial, el formato recomendado es:

```json
{
  "face_match": {
    "resident_id": "alvaro",
    "display_name": "Alvaro",
    "confidence": "high",
    "trusted": true
  }
}
```

Si `trusted=true` y el residente reconocido es valido, VIGILIA puede devolver
apertura inmediata despues del saludo inicial.

## Helper local de referencia

Para simular desde ya esa escritura atomica, el repo incluye:

```bash
./scripts/deposit_baresip_inbox.sh <archivo.wav> <session_id> [caller_id] [device_label] [transport]
```

Ejemplo:

```bash
cd vigilia-m4-gds3725
./scripts/deposit_baresip_inbox.sh /tmp/prueba.wav sesion-001 front-door gds3725 sip-udp
python3 -m app.main --mode baresip-watch-once
```

## Responsabilidad del exportador

La integracion real entre `baresip` y VIGILIA deberia mantener estas reglas:

- no mezclar varias sesiones en un mismo archivo
- no sobrescribir archivos ya existentes
- usar ids unicos por sesion
- dejar el `wav` final solo cuando el audio este completo
- no invocar la IA directamente desde `baresip`

## Lo que no queremos hacer

- que `baresip` decida cuando abrir el porton
- que el watcher procese archivos a medio escribir
- que la metadata viva solo en el nombre del archivo
- que la integracion real dependa del `.txt`

## Siguiente etapa

Cuando el `GDS3725` ya este en mano, el siguiente paso tecnico sera definir que
pieza exacta hace de exportador:

- modulo o hook propio alrededor de `baresip`
- wrapper de proceso que observe llamadas y materialice el `wav`
- o una herramienta lateral que convierta una captura o dump local en archivos de inbox

Mientras tanto, este contrato ya deja fija la forma en que VIGILIA espera recibir
las sesiones.
