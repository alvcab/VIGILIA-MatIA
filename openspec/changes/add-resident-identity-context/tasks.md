# Tareas

## 1. Contexto Estructurado de Residentes

- [x] 1.1 Definir spec delta para identidad residente y aliases
- [x] 1.2 Agregar tablas SQLite `residents` y `resident_aliases`
- [x] 1.3 Vincular `authorized_people` con `resident_id`
- [x] 1.4 Enriquecer `access_events` con `claimed_resident_name`, `claimed_unit` y `resolved_resident_id`
- [x] 1.5 Crear utilidades Python minimas para consultar residentes y aliases
- [x] 1.6 Validar inicializacion y compatibilidad con la base existente
- [x] 1.7 Importar padron inicial desde Excel a `residents` y `resident_aliases`
- [x] 1.8 Resolver nombre/unidad reclamados desde la transcripcion y persistirlos en `access_events`
- [x] 1.9 Enriquecer mensajes de rechazo con residente o unidad reclamados cuando existan
- [x] 1.10 Usar `resident_id` reclamado como refuerzo acotado para matches faciales borderline
