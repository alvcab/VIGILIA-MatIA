# Propuesta: Agregar base de reconocimiento facial

## Por Que

El proyecto ya dispone de camara VTO, snapshots y persistencia local de eventos.
Para avanzar hacia reconocimiento facial hace falta una base estructural que permita registrar personas autorizadas, almacenar referencias de rostros y dejar observaciones listas para futuras comparaciones.

## Que Cambia

- Agregar tablas SQLite para identidades autorizadas y observaciones faciales
- Crear un modulo Python base para administrar personas y registros faciales
- Dejar el dominio documentado en OpenSpec

## No Objetivos

- Instalar motores de reconocimiento facial en este cambio
- Hacer matching biometrico real en esta etapa
- Abrir el porton automaticamente usando reconocimiento facial todavia

## Criterios de Exito

- Existe una estructura de datos para personas autorizadas
- Existe una estructura de datos para observaciones faciales
- El proyecto queda listo para conectar un motor de embeddings en una siguiente fase
