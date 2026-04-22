# VIGILIA MatIA

Prototipo de control de acceso para condominio con:

- apertura de porton Dahua por HTTP Digest
- camara VTO por RTSP
- transcripcion de audio con Whisper
- decision local con Ollama
- reconocimiento facial con `dlib` + `face_recognition`
- trazabilidad con OpenSpec
- persistencia local en SQLite

## Estado Actual

El repositorio ya incluye:

- flujo manual de apertura con `test_conserje.py`
- flujo principal de audio en `v1_sin_IA/puente_vigilia.py`
- integracion base de Asterisk con grabacion, procesamiento IA y reproduccion de respuesta
- captura de snapshots del VTO
- registro de eventos en `data/vigilia.db`
- registro y matching facial
- whitelist facial con habilitacion y deshabilitacion por persona
- entorno unificado de IA en `~/miniforge3/envs/vigilia-face`

## Estructura Principal

- [run_vigilia.sh](./run_vigilia.sh): lanzador principal del flujo de audio
- [v1_sin_IA/inference_service.py](./v1_sin_IA/inference_service.py): servicio local persistente para transcripcion Whisper
- [v1_sin_IA/puente_vigilia.py](./v1_sin_IA/puente_vigilia.py): pipeline de acceso con voz, snapshot, matching facial y decision
- [v1_sin_IA/vto_camera.py](./v1_sin_IA/vto_camera.py): vista en vivo y snapshots del VTO
- [v1_sin_IA/event_store.py](./v1_sin_IA/event_store.py): acceso a SQLite
- [v1_sin_IA/face_registry.py](./v1_sin_IA/face_registry.py): gestion de personas y observaciones faciales
- [v1_sin_IA/asterisk/extensions.conf](./v1_sin_IA/asterisk/extensions.conf): dialplan de entrada desde el VTO
- [v1_sin_IA/asterisk/procesar_llamada_vto.sh](./v1_sin_IA/asterisk/procesar_llamada_vto.sh): wrapper entre Asterisk y `run_vigilia.sh`
- [v1_sin_IA/asterisk/preparar_saludo_vigilia.sh](./v1_sin_IA/asterisk/preparar_saludo_vigilia.sh): generacion del saludo inicial reutilizable
- [openspec/](./openspec): trazabilidad funcional y tecnica

## Entorno

El pipeline unificado corre con:

- `~/miniforge3/envs/vigilia-face/bin/python`

Ese entorno contiene:

- `dlib`
- `face_recognition`
- `gTTS`
- `openai-whisper`
- `torch`

El runner intenta mantener un servicio local persistente en `/tmp/vigilia_inference.sock` para evitar recargar Whisper en cada llamada. Si el servicio no responde a tiempo, el flujo vuelve automaticamente al modo local para esa transcripcion.

## Comandos Utiles

Abrir el porton manualmente:

```bash
python3 test_conserje.py --once
```

Probar canales del Dahua:

```bash
python3 test_conserje.py --diagnose
```

Ver la camara del VTO:

```bash
python3 v1_sin_IA/vto_camera.py live
```

Capturar un snapshot:

```bash
python3 v1_sin_IA/vto_camera.py snapshot
```

Ejecutar el flujo principal con un audio real:

```bash
./run_vigilia.sh /ruta/al/audio.wav

Ver el log del servicio persistente:

```bash
tail -f /tmp/vigilia_inference.log
```
```

Registrar una persona autorizada:

```bash
python3 v1_sin_IA/face_registry.py add-person "Alvaro" captures/puerta.jpg allow
```

Deshabilitar o habilitar una persona ya registrada:

```bash
python3 v1_sin_IA/face_registry.py set-access 2 deny
python3 v1_sin_IA/face_registry.py set-access 2 allow
```

Actualizar la imagen de referencia:

```bash
python3 v1_sin_IA/face_registry.py update-reference-image 2 captures/nueva_foto.jpg
```

Eliminar una persona del registro:

```bash
python3 v1_sin_IA/face_registry.py remove-person 3
```

Probar reconocimiento facial:

```bash
~/miniforge3/envs/vigilia-face/bin/python v1_sin_IA/reconocer_rostro.py captures/puerta.jpg
```

Registrar y probar reconocimiento en un solo paso:

```bash
~/miniforge3/envs/vigilia-face/bin/python v1_sin_IA/probar_reconocimiento.py "Alvaro" captures/puerta.jpg captures/puerta.jpg
```

Ver eventos recientes:

```bash
python3 v1_sin_IA/ver_eventos.py 5
```

Ver observaciones faciales:

```bash
python3 v1_sin_IA/face_registry.py list-observations 5
```

## Operacion Asterisk

Generar el saludo inicial para el dialplan:

```bash
./v1_sin_IA/asterisk/preparar_saludo_vigilia.sh
```

Recargar el dialplan:

```bash
asterisk -rx "dialplan reload"
```

El contexto `from-vto` ahora hace este flujo:

- responde la llamada
- reproduce un saludo inicial si existe `/tmp/vigilia_prompt.wav`
- espera voz y graba audio con `MixMonitor`
- procesa el WAV con `run_vigilia.sh`
- reproduce la respuesta generada por la IA

Archivos utiles para debug:

- audio entrante: `/tmp/vigilia_in_<UNIQUEID>.wav`
- audio de respuesta: `/tmp/vigilia_out_<UNIQUEID>.wav`
- log operativo: `/tmp/vigilia_asterisk.log`

## Base de Datos

La base local vive en:

- `data/vigilia.db`

Tablas principales:

- `access_events`
- `authorized_people`
- `face_observations`

Campos utiles de `access_events`:

- `face_match_name`
- `face_match_confidence`
- `face_observation_id`
- `decision_source`
- `decision_reason`

Consulta rapida:

```bash
sqlite3 -header -column data/vigilia.db "select id, created_at, transcript, model_response, gate_opened from access_events order by id desc limit 10;"
```

## Notas Operativas

- El reconocimiento facial ya esta integrado como senal adicional al contexto del modelo.
- La politica hibrida puede abrir si la voz pide acceso y el rostro coincide con alta confianza en una persona habilitada.
- El runner `run_vigilia.sh` exige un archivo WAV existente.
- La whitelist facial vive en `authorized_people.access_enabled`.
- La base SQLite se resuelve con ruta absoluta dentro del repo para evitar inconsistencias entre scripts.
- `captures/` y `data/vigilia.db` no se versionan.

## Proximo Paso Sugerido

La siguiente iteracion natural es estabilizar el flujo completo en llamadas reales: ajustar umbrales faciales, afinar el prompt de decision y endurecer permisos/ejecucion de Asterisk sobre el entorno `vigilia-face`.
