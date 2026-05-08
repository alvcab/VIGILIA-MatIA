# Integracion de baresip con la respuesta de audio del departamento

Este documento define el contrato operativo para que una llamada saliente viva de
`baresip` deposite el audio de respuesta del departamento en el host persistente
de `MatIA`.

La idea es simple:

- `MatIA` inicia la llamada al departamento
- la sesion activa publica donde debe caer el `WAV` de respuesta
- el hook o exportador de `baresip` escribe ese audio en la ruta publicada
- `MatIA` corre el watcher y transforma la respuesta en `approved`, `denied`
  o `no_response`

## Objetivo

Queremos terminar con un flujo asi:

`MatIA -> llamada saliente por baresip -> WAV de respuesta -> reply_audio_inbox -> watcher -> VIGILIA`

## Contrato publicado por la sesion activa

Cada llamada saliente ya publica un bloque `reply_audio_capture` con:

```json
{
  "audio_file": "runtime/baresip/matia_call_service/reply_audio_inbox/matia-call-7.wav",
  "metadata_file": "runtime/baresip/matia_call_service/reply_audio_inbox/matia-call-7.json"
}
```

Ese bloque aparece en:

- el plan de llamada al departamento
- la sesion saliente viva
- el snapshot `active` del host persistente de `MatIA`

## Regla principal

El integrador de `baresip` no debe inventar nombres de archivo.

Debe escribir exactamente en la ruta publicada por `reply_audio_capture.audio_file`.

## Metadata recomendada

El `.json` al lado del audio puede contener:

```json
{
  "session_id": "matia-call-7",
  "source_label": "baresip-live-call",
  "transport": "sip-udp",
  "captured_at": "2026-05-07T22:15:00Z",
  "department_target": "Departamento 1",
  "target_uri": "sip:depto1@192.168.100.71:5060;transport=udp",
  "active_state": "active"
}
```

## Escritura atomica recomendada

Orden sugerido:

1. escribir `*.wav.tmp`
2. escribir `*.json.tmp`
3. si existe sidecar de texto, escribir `*.txt.tmp`
4. renombrar primero `json.tmp -> .json`
5. renombrar luego `txt.tmp -> .txt`
6. renombrar al final `wav.tmp -> .wav`

La razon es la misma que en el inbox principal:

- el watcher toma `*.wav` finales como senal de "audio listo"
- el `wav` debe ser siempre la ultima senal visible

## Operacion Python

El repo ya expone una operacion directa:

```bash
python3 -m app.main --mode department-call-service-deposit-reply-audio --session-id matia-call-7 --audio-file /ruta/a/respuesta.wav
```

Esa operacion:

- busca la sesion activa
- lee la ruta publicada por `reply_audio_capture`
- copia el audio a esa ruta
- genera metadata al lado
- copia tambien un `.txt` sidecar si el WAV origen ya lo trae

## Helper shell

Tambien existe un helper:

```bash
./scripts/deposit_department_reply_audio.sh matia-call-7 /ruta/a/respuesta.wav
```

## Watcher posterior

Una vez depositado el audio, `MatIA` procesa la respuesta con:

```bash
python3 -m app.main --mode department-call-service-reply-audio-watch-once
```

## Restriccion de seguridad

El watcher solo procesa audios de sesiones que sigan `active`.

Eso evita:

- reprocesar respuestas tardias
- reabrir una autorizacion ya cerrada
- mezclar audios viejos con una sesion nueva

## Lo que falta despues

Este documento deja cerrada la interfaz de deposito. Lo que todavia falta es el
hook concreto de `baresip` que capture el audio de la llamada saliente y llame a
esta operacion automaticamente.
