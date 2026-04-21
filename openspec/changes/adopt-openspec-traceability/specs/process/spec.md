# Delta de Proceso

## Requisitos Agregados

### Requisito: Trazar cambios relevantes del repositorio mediante artefactos OpenSpec

El repositorio DEBE documentar cambios funcionales o arquitectonicos relevantes mediante artefactos OpenSpec antes o durante la implementacion.

#### Escenario: Nueva funcionalidad o modificacion importante

- DADO que una persona desarrolladora planea un cambio relevante
- CUANDO el trabajo comienza
- ENTONCES el repositorio contiene una carpeta de cambio con propuesta, diseno, tareas y las delta specs correspondientes

#### Escenario: El comportamiento cambia al aprender durante la implementacion

- DADO que la implementacion revela nuevas restricciones o un comportamiento revisado
- CUANDO los artefactos del cambio se actualizan
- ENTONCES la propuesta, el diseno, las tareas o las delta specs se revisan para reflejar el entendimiento mas reciente

### Requisito: Preservar el comportamiento actual del sistema como specs vivas

El repositorio DEBE mantener specs base que describan el comportamiento visible actual del sistema.

#### Escenario: Revision de la intencion del sistema

- DADO que una persona desarrolladora o revisora necesita entender el comportamiento actual
- CUANDO inspecciona `openspec/specs/`
- ENTONCES puede encontrar especificaciones orientadas a comportamiento para los dominios activos del sistema

### Requisito: Proveer guia para agentes en una colaboracion guiada por specs

El repositorio DEBE proveer instrucciones legibles por agentes que orienten a los asistentes de codigo hacia el flujo OpenSpec.

#### Escenario: Un agente comienza trabajo sobre un cambio relevante

- DADO que un asistente de codigo comienza trabajo en el repositorio
- CUANDO lee las instrucciones del proyecto
- ENTONCES queda orientado a usar la estructura OpenSpec para cambios no triviales
