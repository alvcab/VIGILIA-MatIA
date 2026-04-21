# Diseno: Agregar persistencia SQLite para eventos de acceso

## Resumen

La persistencia se implementara con el modulo estandar `sqlite3` de Python.
Se agregara un modulo dedicado para encapsular:

- inicializacion de base de datos
- creacion de esquema
- insercion de eventos

## Ubicacion

La base se almacenara en:

- `data/vigilia.db`

Esto deja separada la persistencia del codigo y facilita inspeccion manual.

## Esquema Inicial

La tabla `access_events` almacenara:

- `id`
- `created_at`
- `audio_path`
- `transcript`
- `model_response`
- `gate_opened`
- `snapshot_path`
- `error_message`

## Integracion

`puente_vigilia.py` registrara un evento al terminar cada intento relevante.
Si falla la captura de snapshot o la apertura, esa condicion tambien quedara registrada.

## Tradeoffs

- Pro: cero dependencias nuevas
- Pro: facil de inspeccionar con `sqlite3`
- Contra: por ahora solo un flujo escribe a la base
- Contra: no hay aun una capa de consultas o reportes
