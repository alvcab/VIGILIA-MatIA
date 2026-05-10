# GDS3725 First Setup

Guia corta para la primera prueba de `GDS3725 -> baresip -> VIGILIA` sin Asterisk.

## Objetivo

Levantar una primera llamada SIP simple entre el `GDS3725` y el `Mac mini M4`, minimizando variables.

## Supuestos Iniciales

- `Mac mini M4`: `192.168.100.50`
- `GDS3725`: `192.168.100.60`
- cuenta local VIGILIA / `baresip`: `vigilia`
- cuenta del dispositivo: `door`
- transporte inicial: `UDP`

## 1. Preparar el lado VIGILIA

En el `Mac mini`:

```bash
cd vigilia-m4-gds3725
cp .env.example .env
./scripts/prepare_baresip_runtime.sh
./scripts/run_baresip_local.sh
```

Verifica que el archivo [runtime/baresip/accounts](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/accounts:1) contenga una linea parecida a esta:

```text
<sip:vigilia@192.168.100.50:5060;transport=udp>;regint=0
```

## 2. Configurar el GDS3725

Usa `Direct IP Call` / peering como primera prueba. `baresip` actua como UA
local, no como PBX ni registrar SIP.

- habilitar `Direct IP Call` en la configuracion avanzada SIP
- `Doorbell Mode`: `Call Doorbell Number`
- `Number Called When Door Bell Pressed`: `<IP_DEL_MAC>:5060`
- `Door Bell Call Mode`: `Serial Hunting`
- `SIP Transport`: `UDP`
- `NAT Traversal`: `No`
- `SRTP`: `Disabled`
- `TLS`: `Disabled`
- `DTMF`: `RFC2833`

Si el firmware exige una cuenta SIP activa aunque se use peering, manten una
cuenta local simple, pero no dependas de registro contra `baresip`.

## 3. Codecs Recomendados Para La Primera Prueba

Orden sugerido:

1. `G.722`
2. `G.711u`
3. `G.711a`

## 4. Primera Prueba

- deja corriendo `baresip`
- inicia la llamada desde el `GDS3725`
- confirma si el `Mac mini` recibe intento SIP
- si no hay audio, prueba primero con `G.711u`

## 5. Mantener La Prueba Simple

Para la primera iteracion:

- no usar `TLS`
- no usar `SRTP`
- no usar `Outbound Proxy`
- no usar NAT traversal si ambos estan en la misma LAN
- no abrir porton real

## 6. Resultado Esperado

La meta de la primera prueba no es abrir el porton.

La meta es confirmar:

- que el `GDS3725` llama a la cuenta correcta
- que `baresip` recibe la sesion
- que la ruta `GDS3725 -> Mac mini` funciona sin Asterisk

## 7. Proximo Paso

Una vez confirmada la sesion SIP:

- capturar el audio
- conectarlo a la capa de transcripcion
- dejar `dry-run` para la decision
- recien despues evaluar apertura real

## 8. Prueba De Audio De Vuelta Al GDS

Para validar que MatIA puede hablar por el parlante del `GDS3725`, usa el modo
local de saludo:

```bash
python3 -m app.main --mode gds-hello-test
baresip -s -f runtime/baresip-hello
```

Ese modo genera un `WAV` local con una frase breve de MatIA, prepara una cuenta
SIP `door@<IP_DEL_MAC>:5060` y configura `baresip` para responder
automaticamente.

En el `GDS3725`, desde `Llamadas -> Llamadas salientes`, llama a:

```text
door@<IP_DEL_MAC>
```

Resultado esperado:

- el terminal de `baresip` muestra el `INVITE` entrante
- `baresip` contesta la llamada automaticamente
- el parlante del `GDS3725` reproduce el saludo de MatIA
- el audio recibido desde el microfono del `GDS3725` queda en `runtime/baresip-hello/gds-rx.wav`

Para procesar la captura en modo seguro:

```bash
python3 -m app.main --mode gds-capture-process
```

Ese comando usa el audio recibido por `baresip`, lo transcribe con el backend
configurado y ejecuta la decision en `dry-run`.

Si todavia estas usando `sidecar` como backend de transcripcion, puedes simular
la transcripcion creando:

```bash
printf "hola vengo donde Alvaro\n" > runtime/baresip-hello/gds-rx.txt
python3 -m app.main --mode gds-capture-process
```

Para transcribir el audio real con Whisper local:

```bash
VIGILIA_TRANSCRIPTION_BACKEND=whisper-local VIGILIA_WHISPER_MODEL=tiny \
  .venv/bin/python -m app.main --mode gds-capture-process
```

o usa el helper:

```bash
./scripts/process_gds_capture_whisper.sh
```

Para ejecutar la misma captura y abrir el GDS solo cuando la decision autoriza
`should_open=true`, usa el modo de prueba con apertura HTTP:

```bash
./scripts/process_gds_capture_and_open.sh
```

Para una prueba controlada de rostro confiable desde el GDS, sin integrar aun un
motor de vision, pasa la coincidencia simulada por CLI:

```bash
./scripts/process_gds_capture_and_open.sh \
  --face-trusted \
  --face-resident-id alvaro \
  --face-display-name Alvaro \
  --face-confidence high
```

Ese comando carga `.env`, usa Whisper local por defecto y llama al endpoint HTTP
del GDS solo si la evaluacion final queda en `open`.

Para una prueba semi-automatica de extremo a extremo:

```bash
./scripts/run_gds_hello_then_open.sh
```

Ese helper prepara el saludo, ejecuta `baresip`, espera la llamada del GDS y,
cuando detecta audio, corta la llamada unos segundos despues y procesa
`runtime/baresip-hello/gds-rx.wav` con rostro confiable simulado para abrir por
HTTP si la decision queda autorizada. Puedes ajustar los tiempos con
`VIGILIA_GDS_CALL_WAIT_SECONDS` y `VIGILIA_GDS_AFTER_CAPTURE_SECONDS`.
Cuando se usa `--face-trusted`, el modo `gds-capture-open` omite Whisper y abre
con la decision de rostro confiable para que la prueba no espere la
transcripcion local.

En el entorno local validado, `openai-whisper` vive dentro de `.venv` y usa
`ffmpeg`. Si `torch` muestra avisos de ABI con NumPy 2, fija NumPy localmente:

```bash
.venv/bin/python -m pip install "numpy<2"
```
