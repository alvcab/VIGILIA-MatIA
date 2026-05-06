# Flows

## decision-only

1. ingresar texto
2. evaluar policy
3. devolver decision estructurada

## dry-run

1. ingresar texto
2. evaluar policy
3. simular respuesta TTS
4. simular apertura si corresponde

## session-replay

1. crear una sesion de intercom simulada
2. adjuntar transcript de entrada
3. enrutar la sesion por el `call_router`
4. obtener decision, respuesta hablada y accion `dry-run`

## audio-file

1. crear una sesion de intercom con referencia a WAV local
2. transcribir el WAV con la interfaz de transcripcion
3. enrutar el texto resultante por la policy
4. devolver decision, respuesta y `dry-run`

## sip-preview

1. cargar la configuracion SIP local
2. construir URIs de VIGILIA y del `GDS3725`
3. exponer el contrato esperado de sesion
4. dejar lista la siguiente etapa de integracion real

## sip-session

1. cargar la configuracion SIP
2. simular `register`
3. simular llamada entrante o saliente
4. simular `accept`
5. entregar un resumen de lifecycle

## baresip-preview

1. cargar configuracion SIP local
2. construir el account line de `baresip`
3. definir binario, archivo de config y runtime esperado
4. exponer el contrato de ejecucion para integrar el `GDS3725`

## baresip-runtime

1. generar `runtime/baresip/config`
2. generar `runtime/baresip/accounts`
3. preparar carpeta de audio
4. ejecutar `baresip -f runtime/baresip/config`

## baresip-inbox

1. `baresip` deja WAV y metadata en `runtime/baresip/inbox`
2. VIGILIA toma el audio
3. corre transcripcion, decision y modelo
4. devuelve accion `dry-run` y respuesta hablada

## baresip-watch-once

1. escanear `runtime/baresip/inbox`
2. ignorar audios ya procesados
3. procesar cada WAV nuevo
4. guardar salida JSON en `runtime/baresip/processed`
5. respetar el contrato definido para `nombre.wav`, `nombre.txt` y `nombre.json`

## hybrid-decision

1. evaluar reglas deterministicas
2. producir una decision base
3. si hay seguimiento pendiente, exponer `model_guidance`
4. dejar lista la costura para una futura capa de modelo
5. generar una respuesta simulada con backend local stub

## conversation-turn

1. cargar o crear una sesion por `session_id`
2. registrar el turno actual en `runtime/conversations`
3. evaluar la policy
4. devolver estado de conversacion y siguiente paso

## audio-only

Reservado para la futura integracion de audio del `GDS3725`.

## full-flow

Reservado para la futura integracion completa con telephony, TTS y gate real.
