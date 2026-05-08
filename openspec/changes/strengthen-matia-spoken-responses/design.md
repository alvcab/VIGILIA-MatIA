# Diseno: Fortalecer respuestas habladas de MatIA

## Decision 1: El prompt debe fijar contrato de salida

Las instrucciones al backend deben pedir explicitamente:

- espanol claro
- una o dos frases cortas
- tono breve y respetuoso
- sin explicar reglas internas
- sin devolver el prompt ni prefijos tipo `Contexto previo`

## Decision 2: La salida generada se valida antes de hablar

Aunque el backend produzca texto, el sistema debe validar que:

- no este vacio
- no sea demasiado largo
- no haga eco del prompt o del bloque de contexto
- no tenga saltos o formato innecesario

Si falla cualquiera de esas condiciones, se usa la respuesta fija ya segura.

## Decision 3: El stub tambien debe reflejar el contrato

El backend `stub` debe producir frases mas naturales y alineadas con el mismo estilo esperado del backend real.

## Decision 4: Variar el tono segun el momento de la visita

Las respuestas no deben sonar iguales en todos los casos.
El estilo esperado cambia segun el flujo:

- saludo o aclaracion inicial: tono de recepcion breve
- entrega: tono practico
- autorizacion o control de acceso: tono firme y respetuoso
- urgencia: tono calmo pero rapido
- confirmacion con residente: tono de espera breve y ordenado

## Decision 5: Reusar referencias conocidas cuando existan

Si el flujo ya conoce un residente o departamento candidato, la respuesta hablada debe poder nombrarlo de forma natural.
Eso evita preguntas demasiado genericas y ayuda a que la visita entienda que el sistema esta siguiendo el contexto correcto.
