# Propuesta: Agregar contexto estructurado de residentes

## Por Que

El prototipo ya registra eventos, snapshots, matching facial y decisiones de acceso.
Para robustecer la IA y reducir ambiguedades, el sistema necesita una capa estructurada de identidad residencial: nombres, aliases hablados, unidades/departamentos y relacion entre una persona residente y sus referencias faciales.

## Que Cambia

- Agregar una tabla `residents` en SQLite para identidad operativa del condominio
- Agregar una tabla `resident_aliases` para nombres hablados, variantes y referencias a departamentos
- Vincular `authorized_people` con `resident_id`
- Enriquecer `access_events` con contexto reclamado y resuelto de residente/unidad
- Exponer utilidades Python minimas para consultar este contexto

## No Objetivos

- Implementar todavia confirmacion por llamada al residente
- Migrar toda la whitelist facial a un modelo nuevo en un solo cambio
- Reentrenar o reemplazar el modelo local

## Criterios de Exito

- Existe una identidad residente separada de la referencia facial
- El proyecto puede registrar aliases y unidad/departamento por residente
- Los eventos de acceso pueden guardar nombre/unidad reclamados y residente resuelto
- El contexto queda disponible para futuras decisiones de IA
