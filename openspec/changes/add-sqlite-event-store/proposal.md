# Propuesta: Agregar persistencia SQLite para eventos de acceso

## Por Que

El proyecto ya puede transcribir audio, consultar el modelo, abrir el porton y capturar snapshots del VTO.
Falta una capa de persistencia local para registrar de forma trazable cada intento de acceso y poder revisar pruebas reales.

## Que Cambia

- Agregar una base SQLite local en `data/vigilia.db`
- Crear una tabla de eventos de acceso
- Registrar desde `puente_vigilia.py` la transcripcion, respuesta del modelo, resultado de apertura y snapshot

## No Objetivos

- Agregar una base de datos cliente-servidor
- Implementar dashboards o reportes
- Migrar todos los scripts del proyecto a usar SQLite en este cambio

## Criterios de Exito

- El proyecto puede crear automaticamente la base de datos local
- Cada intento procesado desde `puente_vigilia.py` queda registrado
- Los eventos guardan suficiente informacion para auditar una prueba
