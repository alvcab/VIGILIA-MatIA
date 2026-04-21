# Propuesta: Agregar monitoreo de camara del VTO

## Por Que

El proyecto ya puede abrir el porton y ahora tambien tiene una URL RTSP funcional para la camara del VTO.
Hace falta una forma simple de consumir ese stream desde el propio repositorio para pruebas, monitoreo local y futuras integraciones.

## Que Cambia

- Agregar un modulo Python para abrir la vista en vivo del VTO
- Agregar soporte para capturar snapshots desde el stream RTSP
- Documentar el comportamiento esperado como una nueva spec base de monitoreo

## No Objetivos

- Implementar analitica visual o reconocimiento de personas
- Integrar la vista de camara directamente a Asterisk en este cambio
- Agregar dependencias nuevas como OpenCV si no son necesarias

## Criterios de Exito

- Existe un script o modulo local reutilizable para abrir el stream del VTO
- Existe una forma simple de guardar una imagen del stream
- El comportamiento queda documentado en OpenSpec
