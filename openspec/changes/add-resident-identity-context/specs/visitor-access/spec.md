# Delta de visitor-access

## Requisitos Agregados

### Requisito: Mantener identidad estructurada de residentes

El sistema DEBE poder representar residentes del condominio como entidades separadas de sus referencias faciales.

#### Escenario: Residente registrado con unidad

- DADO que una persona administradora registra a un residente
- CUANDO guarda su nombre y unidad/departamento
- ENTONCES el sistema persiste una identidad residente reutilizable

### Requisito: Mantener aliases operativos de residentes

El sistema DEBE poder asociar aliases hablados o variantes de identificacion a un residente.

#### Escenario: Alias hablado asociado a un residente

- DADO que un residente puede ser referido por una variante hablada de su nombre o unidad
- CUANDO esa variante se registra como alias
- ENTONCES el sistema la asocia a la identidad residente correspondiente

### Requisito: Trazar residente reclamado y resuelto en eventos de acceso

El sistema DEBE poder registrar el residente o unidad reclamados por el visitante y la identidad residente resuelta por el sistema.

#### Escenario: Evento enriquecido con contexto residente

- DADO que un intento de acceso produce texto utilizable o matching relevante
- CUANDO el sistema registra el evento en SQLite
- ENTONCES el evento puede guardar nombre reclamado, unidad reclamada e identidad residente resuelta

#### Escenario: Resolver alias o unidad mencionados en la voz

- DADO que existen residentes y aliases cargados en SQLite
- CUANDO la transcripcion menciona un nombre o una unidad reconocibles
- ENTONCES el sistema intenta resolver `claimed_resident_name`, `claimed_unit` y `resolved_resident_id` antes de persistir el evento

#### Escenario: Respuesta de rechazo enriquecida con contexto residente

- DADO que la transcripcion menciona un residente o una unidad reconocibles
- Y el sistema no puede autorizar la apertura
- CUANDO genera la respuesta al visitante
- ENTONCES puede mencionar el residente o la unidad reclamados sin abrir el porton

#### Escenario: Contexto residente refuerza un match facial borderline

- DADO que la voz reclama un residente o una unidad que el sistema resuelve a una identidad residente unica
- Y el mejor match facial pertenece a una persona autorizada vinculada a ese mismo `resident_id`
- Y la distancia facial queda apenas fuera de la tolerancia configurada
- CUANDO el flujo hibrido evalua la solicitud
- ENTONCES el contexto residente puede reforzar la apertura sin depender del modelo

#### Escenario: No abrir sin contexto residente reclamado

- DADO que la voz pide abrir el porton
- Y existe un match facial confiable
- Y la persona facial no corresponde a un residente conocido vinculado a `resident_id`
- PERO la voz no reclama un residente ni una unidad reconocibles
- CUANDO el flujo hibrido evalua la solicitud
- ENTONCES el sistema no abre solo con el rostro
- Y solicita al visitante indicar a que residente o departamento viene
