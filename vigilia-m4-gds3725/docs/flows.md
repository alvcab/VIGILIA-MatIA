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

## audio-only

Reservado para la futura integracion de audio del `GDS3725`.

## full-flow

Reservado para la futura integracion completa con telephony, TTS y gate real.
