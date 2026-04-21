# Diseno: Agregar base de reconocimiento facial

## Resumen

La primera fase de reconocimiento facial se concentrara en datos y trazabilidad.
Se usara SQLite para guardar:

- personas autorizadas
- rutas de imagen de referencia
- embeddings faciales como texto JSON
- observaciones de rostros detectados en capturas

## Modelo de Datos

Se agregaran dos tablas:

- `authorized_people`
- `face_observations`

`authorized_people` permitira registrar identidades conocidas y asociarles una foto de referencia y, mas adelante, embeddings faciales persistidos.

`face_observations` permitira guardar cada observacion de un rostro detectado en una captura o evento, incluso si aun no existe matching.

## Integracion Futura

La siguiente fase podra usar un motor de reconocimiento facial para:

1. capturar un snapshot del VTO
2. detectar un rostro
3. generar embedding
4. comparar con `authorized_people`
5. guardar el resultado en `face_observations`

## Tradeoffs

- Pro: deja la base lista sin meter dependencias pesadas todavia
- Pro: ayuda a ordenar datos reales antes de automatizar decisiones
- Contra: no entrega reconocimiento efectivo por si solo
- Contra: los embeddings quedaran como texto hasta elegir el motor final
