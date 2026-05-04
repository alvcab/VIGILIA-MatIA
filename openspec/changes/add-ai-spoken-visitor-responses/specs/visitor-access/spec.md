## MODIFIED Requirements

### Requisito: Entregar retroalimentacion al visitante

#### Escenario: Respuesta hablada generada por IA para una visita no autorizada

- DADO que el sistema ya decidio no abrir el porton
- Y existe una transcripcion util del visitante
- CUANDO el flujo genera la respuesta hablada
- ENTONCES el sistema puede usar un modelo local para redactar una frase breve en espanol
- Y esa respuesta no altera la decision de apertura

#### Escenario: Repartidor o paquete sin autorizacion de apertura

- DADO que el visitante indica que viene a dejar un paquete o encargo
- Y el sistema no ha decidido abrir el porton
- CUANDO genera la respuesta hablada al visitante
- ENTONCES la respuesta puede orientar a dejar el paquete en conserjeria
- Y el porton permanece cerrado

#### Escenario: Fallback de respuesta hablada cuando la IA falla

- DADO que el sistema ya decidio abrir o no abrir
- Y la generacion de respuesta hablada por IA falla, excede su timeout o devuelve una salida invalida
- CUANDO el flujo necesita hablarle al visitante
- ENTONCES el sistema usa una respuesta fija de respaldo
- Y mantiene la misma decision de acceso ya tomada

#### Escenario: Segundo turno local para aclarar residente o departamento

- DADO que el flujo corre localmente en el host
- Y el visitante entrega un saludo o una visita ambigua sin pedir apertura
- CUANDO el sistema necesita aclarar a que residente o departamento viene
- ENTONCES puede emitir una pregunta corta al visitante
- Y volver a capturar una segunda respuesta antes de cerrar la interaccion
