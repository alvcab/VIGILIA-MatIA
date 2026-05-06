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

## audio-only

Reservado para la futura integracion de audio del `GDS3725`.

## full-flow

Reservado para la futura integracion completa con telephony, TTS y gate real.
