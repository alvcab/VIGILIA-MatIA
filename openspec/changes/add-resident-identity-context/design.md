# Diseno: Contexto estructurado de residentes

## Objetivo

Separar la identidad operativa del residente de la referencia facial puntual para que el flujo de acceso pueda razonar con:

- nombre formal del residente
- alias hablados o variantes
- unidad o departamento
- relacion entre residente y personas autorizadas por rostro

Esto permite trazabilidad mas fina en `access_events` y habilita decisiones hibridas mas seguras cuando la voz reclama a una persona o unidad concreta.

## Modelo de datos

### Tabla `residents`

Representa la identidad base del condominio. Guarda:

- nombre completo y nombre preferido
- unidad/departamento y edificio
- telefonos y metadatos de operacion
- flags de enrolamiento y habilitacion

La tabla existe aunque un residente todavia no tenga embedding facial cargado.

### Tabla `resident_aliases`

Guarda variantes operativas de referencia al residente:

- alias de nombre hablado
- unidad mencionada por voz
- otras formas normalizadas de identificar a la persona

Cada alias se persiste con una version normalizada para resolver coincidencias robustas sobre transcripciones ruidosas.

### Relacion con `authorized_people`

`authorized_people.resident_id` conecta una cara registrada con una identidad residente reusable.

Esto evita depender del nombre textual de la persona facial para decidir apertura o registrar eventos.

### Enriquecimiento de `access_events`

Cada evento puede guardar:

- `claimed_resident_name`
- `claimed_unit`
- `resolved_resident_id`

Asi se conserva por separado:

- lo que dijo el visitante
- la identidad que el sistema logro resolver
- el resultado final de apertura o rechazo

## Resolucion de contexto desde voz

`puente_vigilia.py` intenta resolver contexto residente antes de persistir o decidir:

1. normaliza la transcripcion
2. busca coincidencias por alias registrados
3. detecta patrones de unidad/departamento
4. determina si existe un `resolved_resident_id` unico
5. reutiliza ese contexto en decision, mensaje al visitante y almacenamiento del evento

Si la resolucion no es unica, el sistema puede conservar nombre o unidad reclamados sin asumir una identidad incorrecta.

## Politica de decision

La capa de decision mantiene el principio de seguridad primero:

- un rostro confiable con `resident_id` conocido puede abrir como residente conocido cuando la voz pide acceso
- un rostro borderline puede reforzarse si coincide con el `resident_id` reclamado
- si la voz reclama un residente distinto del rostro, se rechaza
- si el modelo falla, solo se abre en el fallback cuando hay habla util y un match fuerte de residente conocido

Con esto la voz no abre sola, el rostro no abre solo sin contexto permitido, y los desacoples entre voz y rostro quedan explicitamente registrados.

## Compatibilidad y migracion

La inicializacion de SQLite agrega columnas faltantes con `ALTER TABLE` cuando la base ya existe.

Esto permite:

- conservar instalaciones previas
- habilitar el nuevo contexto sin recrear la base
- poblar residentes iniciales desde planillas mediante `import_residents_xlsx.py`

## Impacto operativo

Este cambio deja lista la base para pasos posteriores como:

- contacto o confirmacion con residente
- reglas diferenciadas por unidad
- auditoria de visitas por identidad reclamada y resuelta
