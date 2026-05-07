# MatIA como agente conversacional principal

Este documento fija el reparto de responsabilidades para la etapa
`Mac mini M4 + GDS3725`.

La idea central es simple:

- `MatIA` habla con la visita
- `VIGILIA` decide si una accion sensible esta autorizada
- `baresip` transporta audio y metadata SIP

## Objetivo

Evitar que la capa conversacional y la capa de autorizacion queden mezcladas.

Eso nos da tres beneficios:

- conversaciones mas naturales sin meter reglas duras dentro del transporte SIP
- decisiones de acceso mas trazables
- una separacion limpia entre experiencia conversacional y seguridad

## Reparto de roles

## MatIA

Responsabilidades:

- recibir el contexto de la llamada
- conversar con la visita
- pedir aclaraciones
- confirmar a que residente viene a ver
- responder con voz
- mantener el hilo conversacional de la sesion

`MatIA` no deberia abrir el porton directamente.

## VIGILIA

Responsabilidades:

- resolver residentes y aliases
- aplicar reglas de autorizacion
- clasificar intenciones de acceso
- decidir `open`, `clarify`, `announce`, `escalate` o `deny`
- registrar razones y trazabilidad
- ejecutar apertura real o `dry-run`

VIGILIA es la capa de seguridad y policy.

## baresip

Responsabilidades:

- recibir la llamada SIP del `GDS3725`
- encapsular caller id y metadata de sesion
- dejar disponible el audio de la sesion
- actuar como puente fino de transporte

`baresip` no deberia decidir logica de acceso ni contenido conversacional.

## GDS3725

Responsabilidades:

- originar la sesion de intercom
- entregar audio util
- actuar como endpoint SIP del acceso

## Flujo objetivo

Flujo principal deseado:

`GDS3725 -> baresip -> MatIA -> VIGILIA policy/access-control -> respuesta -> accion`

Interpretacion:

1. el `GDS3725` origina la llamada
2. `baresip` recibe la sesion
3. `MatIA` conduce la conversacion
4. cuando hay que tomar una decision sensible, `MatIA` consulta a VIGILIA
5. VIGILIA responde con decision estructurada y razon
6. `MatIA` responde a la visita
7. si corresponde, VIGILIA abre el porton

## Atajo por rostro confiable

Si el `GDS3725` entrega un match facial confiable de un residente habilitado:

- el sistema puede saludar primero
- y despues abrir de inmediato sin pasar por el resto del dialogo

En ese caso:

- `MatIA` no necesita pedir residente ni autorizacion
- VIGILIA responde con una decision estructurada de apertura inmediata
- el motivo debe quedar trazado como match facial confiable
- y no se requiere una respuesta hablada adicional despues del saludo inicial

Si el dispositivo intento rostro y no encontro un match confiable:

- `MatIA` debe seguir la conversacion normal
- pero con una pregunta mas explicita orientada a residente o unidad
- evitando respuestas genericas que ignoren el contexto facial

## Donde entra el inbox

El inbox de `baresip` ya no se interpreta como el cerebro del sistema.

Su rol preferente pasa a ser:

- integracion asincronica simple
- replay de sesiones
- diagnostico de audio
- pruebas controladas del pipeline

Puede servir tambien como puente inicial entre `baresip` y `MatIA`, pero no debe
forzar la arquitectura final si despues conviene una integracion mas directa por
stream o por eventos de sesion.

## Contrato entre MatIA y VIGILIA

La integracion entre ambos deberia moverse sobre objetos estructurados, no sobre
texto libre solamente.

Entrada minima esperada desde `MatIA` hacia VIGILIA:

- `session_id`
- `turn_index`
- `transcript`
- `caller_id`
- `resident_hint` opcional
- `device_label`

Salida minima esperada desde VIGILIA hacia `MatIA`:

- `action`
- `should_open`
- `reason`
- `confidence`
- `resident_hint`
- `next_step`
- `follow_up_prompt`

## Principio de seguridad

La capa conversacional no debe tener autorizacion implicita para abrir.

Regla:

- `MatIA` propone o consulta
- `VIGILIA` autoriza
- `gate service` ejecuta

## Consecuencia para este repo

`vigilia-m4-gds3725` debe evolucionar hacia:

- una integracion clara con `MatIA`
- una policy reusable desde fuera del transporte SIP
- una interfaz de decision invocable por sesion o por turno
- TTS conversacional desacoplado del mecanismo de apertura

## Consecuencia para las pruebas

Pruebas utiles desde ahora:

- `audio-file` para validar transcripcion y policy
- `conversation-turn` para validar continuidad de contexto
- `baresip-watch-once` para validar replay e inbox

Pruebas que quedan para la siguiente etapa:

- `MatIA -> VIGILIA` con decision estructurada por turno
- audio bidireccional real sobre SIP
- apertura real protegida por policy
