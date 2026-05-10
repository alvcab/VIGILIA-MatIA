# OpenVoice Para Voz De MatIA

## Objetivo

Preparar una voz clonada de MatIA desde una muestra real, manteniendo el flujo
GDS estable separado de la experimentacion de voz.

## Estado

OpenVoice queda como capa opcional. No reemplaza aun la voz actual del GDS ni el
servicio `matia_gds_service.sh`.

## Instalacion Base

```bash
./scripts/bootstrap_openvoice.sh
./scripts/verify_openvoice_ready.sh
```

OpenVoice recomienda Python 3.9 y su instalacion oficial esta orientada a
Linux/Conda. En Mac mini se trata como instalacion experimental local.

## Muestra De Voz

Grabar una muestra limpia:

```bash
./scripts/record_matia_voice_sample.sh
```

El archivo queda en:

```text
runtime/voice/matia-reference.wav
```

Recomendaciones:

- grabar en una pieza silenciosa
- hablar cerca del microfono
- usar una voz con consentimiento explicito
- grabar 20 a 40 segundos
- evitar musica, eco y ruido de calle

Texto sugerido:

```text
Hola, soy MatIA. Estoy probando mi voz para el control de acceso.
Rostro identificado. Abriendo el porton.
No reconozco tu rostro. Indica a que residente vienes a ver.
Un momento, estoy contactando al departamento.
```

## Checkpoints

La instalacion base clona el repo y prepara entorno, pero los checkpoints se
descargan aparte desde las fuentes oficiales de OpenVoice.

Para V2, extraerlos en:

```text
vendor/OpenVoice/checkpoints_v2
```

Para V2 tambien puede hacer falta MeloTTS:

```bash
.venv-openvoice/bin/python -m pip install git+https://github.com/myshell-ai/MeloTTS.git
.venv-openvoice/bin/python -m unidic download
```

## Integracion Pendiente

Cuando la voz clonada este validada:

1. generar frases fijas de MatIA como WAV
2. convertirlas a `8000 Hz`, mono, `pcm_s16le`
3. reemplazar el saludo generado por `say`
4. mantener fallback a voz macOS si OpenVoice falla

## Fuentes

- OpenVoice docs: `https://docs.myshell.ai/technology/openvoice`
- OpenVoice GitHub: `https://github.com/myshell-ai/OpenVoice`
- Uso oficial: `https://github.com/myshell-ai/OpenVoice/blob/main/docs/USAGE.md`
