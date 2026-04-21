# Delta de event-persistence

## Requisitos Agregados

### Requisito: Persistir eventos de acceso en una base local

El proyecto DEBE registrar los intentos de acceso en una base SQLite local para permitir auditoria y pruebas.

#### Escenario: Intento procesado

- DADO que el flujo principal procesa un intento de acceso
- CUANDO la evaluacion termina
- ENTONCES el proyecto guarda un evento con la informacion relevante del intento

### Requisito: Crear automaticamente la base de datos local

El proyecto DEBE inicializar automaticamente la base SQLite y su esquema minimo si aun no existen.

#### Escenario: Primera ejecucion

- DADO que la base local no existe
- CUANDO el flujo intenta registrar un evento
- ENTONCES el proyecto crea la base y la tabla necesaria antes de insertar
