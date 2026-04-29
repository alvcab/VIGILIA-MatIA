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
- flujo principal de audio en `v1/puente_vigilia.py`
- integracion base de Asterisk con grabacion, procesamiento IA y reproduccion de respuesta
- captura de snapshots del VTO
- registro de eventos en `data/vigilia.db`
- registro y matching facial
- whitelist facial con habilitacion y deshabilitacion por persona
- entorno unificado de IA en `~/miniforge3/envs/vigilia-face`

## Estructura Principal

- [run_vigilia.sh](./run_vigilia.sh): lanzador principal del flujo de audio
- [scripts/vigilia_env.sh](./scripts/vigilia_env.sh): variables compartidas del runtime repo-local
- [scripts/prepare_repo_runtime.sh](./scripts/prepare_repo_runtime.sh): prepara `.runtime/` y renderiza config activa
- [scripts/start_repo_asterisk.sh](./scripts/start_repo_asterisk.sh): inicia Asterisk usando config repo-local
- [scripts/asterisk_repo_cli.sh](./scripts/asterisk_repo_cli.sh): envia comandos CLI al Asterisk repo-local
- [v1/inference_service.py](./v1/inference_service.py): servicio local persistente para transcripcion Whisper
- [v1/puente_vigilia.py](./v1/puente_vigilia.py): pipeline de acceso con voz, snapshot, matching facial y decision
- [v1/vto_camera.py](./v1/vto_camera.py): vista en vivo y snapshots del VTO
- [v1/event_store.py](./v1/event_store.py): acceso a SQLite
- [v1/face_registry.py](./v1/face_registry.py): gestion de personas y observaciones faciales
- [v1/asterisk/extensions.conf](./v1/asterisk/extensions.conf): dialplan de entrada desde el VTO
- [v1/asterisk/procesar_llamada_vto.sh](./v1/asterisk/procesar_llamada_vto.sh): wrapper entre Asterisk y `run_vigilia.sh`
- [v1/asterisk/preparar_saludo_vigilia.sh](./v1/asterisk/preparar_saludo_vigilia.sh): generacion del saludo inicial reutilizable
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

El runner intenta mantener un servicio local persistente en `.runtime/run/vigilia_inference.sock` para evitar recargar Whisper en cada llamada. Si el servicio no responde a tiempo, el flujo vuelve automaticamente al modo local para esa transcripcion.

## Comandos Utiles

Abrir el porton manualmente:

```bash
python3 test_conserje.py --once
```

Probar canales del Dahua:

```bash
python3 test_conserje.py --diagnose
```

Si el relay correcto no es el `1`, fija el canal real antes de probar el flujo:

```bash
export VTO_GATE_CHANNEL=2
python3 test_conserje.py --once
```

Ver la camara del VTO:

```bash
python3 v1/vto_camera.py live
```

Capturar un snapshot:

```bash
python3 v1/vto_camera.py snapshot
```

Ejecutar el flujo principal con un audio real:

```bash
./run_vigilia.sh /ruta/al/audio.wav
```

Variables utiles para configuracion local no versionada:

```bash
export VTO_IP=192.168.100.108
export VTO_USER=admin
export VTO_PASS='tu-clave-local'
export VTO_GATE_CHANNEL=2
```

Ver el log del servicio persistente:

```bash
tail -f .runtime/logs/vigilia_inference.log
```

Registrar una persona autorizada:

```bash
python3 v1/face_registry.py add-person "Alvaro" captures/puerta.jpg allow
```

Deshabilitar o habilitar una persona ya registrada:

```bash
python3 v1/face_registry.py set-access 2 deny
python3 v1/face_registry.py set-access 2 allow
```

Actualizar la imagen de referencia:

```bash
python3 v1/face_registry.py update-reference-image 2 captures/nueva_foto.jpg
```

Eliminar una persona del registro:

```bash
python3 v1/face_registry.py remove-person 3
```

Probar reconocimiento facial:

```bash
~/miniforge3/envs/vigilia-face/bin/python v1/reconocer_rostro.py captures/puerta.jpg
```

Registrar y probar reconocimiento en un solo paso:

```bash
~/miniforge3/envs/vigilia-face/bin/python v1/probar_reconocimiento.py "Alvaro" captures/puerta.jpg captures/puerta.jpg
```

Ver eventos recientes:

```bash
python3 v1/ver_eventos.py 5
```

Ver observaciones faciales:

```bash
python3 v1/face_registry.py list-observations 5
```

## Operacion Asterisk

Preparar el runtime local del repo:

```bash
./scripts/prepare_repo_runtime.sh
```

Iniciar Asterisk con config repo-local:

```bash
./scripts/start_repo_asterisk.sh
```

Enviar comandos CLI al Asterisk repo-local:

```bash
./scripts/asterisk_repo_cli.sh "dialplan reload"
./scripts/asterisk_repo_cli.sh "pjsip show endpoints"
```

Generar el saludo inicial para el dialplan:

```bash
./v1/asterisk/preparar_saludo_vigilia.sh
```

El contexto `from-vto` ahora hace este flujo:

- responde la llamada
- reproduce un saludo inicial si existe `/tmp/vigilia_prompt.wav`
- espera voz y graba audio con `MixMonitor`
- procesa el WAV con `run_vigilia.sh`
- reproduce la respuesta generada por la IA

Archivos utiles para debug:

- audio entrante: `.runtime/audio/vigilia_in_<UNIQUEID>.wav`
- audio RTSP auxiliar: `.runtime/audio/<CALL_ID>_rtsp.wav`
- audio de respuesta: `.runtime/audio/vigilia_out_<UNIQUEID>.wav`
- prompt inicial: `.runtime/audio/vigilia_prompt.*`
- log operativo: `.runtime/logs/vigilia_asterisk.log`

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
- `.runtime/` no se versiona y concentra sockets, logs y audio temporal.
- En pruebas nocturnas del VTO, `Dia/Noche = Black/White` dio mejores resultados de matching facial que `Automatico`.
- Contraluces fuertes, como una TV brillante o luz lateral detras del visitante, degradan mucho el matching aunque la cara siga siendo visible.
- Si el sistema no logra una cara usable, ahora intenta snapshots adicionales y orienta al visitante a acercarse y mirar de frente a la camara.

## Camino a Jetson

La ruta recomendada para migrar a Jetson es:

1. clonar este repo completo
2. instalar Asterisk y dependencias del sistema en la maquina destino
3. preparar el runtime local con `./scripts/prepare_repo_runtime.sh`
4. iniciar Asterisk con `./scripts/start_repo_asterisk.sh`
5. mantener secretos y parametros de red fuera de git via variables de entorno o `.env` local
