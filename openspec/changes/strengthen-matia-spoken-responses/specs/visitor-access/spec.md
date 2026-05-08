# Delta de visitor-access

## Requisitos Modificados

### Requisito: Entregar retroalimentacion al visitante

#### Escenario: Respuesta hablada breve y apta para TTS

- DADO que el sistema ya decidio no abrir o necesita aclaracion
- CUANDO genera una respuesta hablada con apoyo del modelo
- ENTONCES la respuesta final debe ser breve, clara y apta para TTS
- Y no debe incluir explicaciones internas ni eco del prompt

#### Escenario: Tono ajustado al tipo de visita

- DADO que el sistema necesita hablar con una visita
- CUANDO genera una respuesta para saludo, entrega, autorizacion, urgencia o confirmacion con residente
- ENTONCES el tono de la respuesta se ajusta al momento conversacional
- Y mantiene frases breves y respetuosas

#### Escenario: Referencia contextual conocida en la respuesta

- DADO que el flujo ya resolvio un residente o departamento candidato
- CUANDO el sistema genera una aclaracion o una confirmacion hablada
- ENTONCES la respuesta puede nombrar esa referencia conocida de forma natural
- Y evita pedir contexto como si no existiera

#### Escenario: Salida generada invalida

- DADO que el backend de modelo devuelve una respuesta vacia, verbosa o fuera de contrato
- CUANDO el flujo necesita hablarle al visitante
- ENTONCES el sistema usa una respuesta fija de respaldo
- Y mantiene la misma decision de acceso
