# Especificacion de vto-monitoring

## Proposito

Definir el comportamiento del monitoreo local de la camara del VTO mediante el stream RTSP ya validado en el entorno.

## Requisitos

### Requisito: Abrir una vista en vivo del VTO

El proyecto DEBE ofrecer una forma local y reutilizable de abrir la transmision RTSP de la camara del VTO.

#### Escenario: Vista en vivo solicitada

- DADO que el stream RTSP del VTO esta disponible
- CUANDO una persona ejecuta la herramienta de monitoreo
- ENTONCES el proyecto abre una vista en vivo del stream usando una herramienta local compatible

### Requisito: Capturar un snapshot del VTO

El proyecto DEBE permitir guardar una imagen fija tomada desde el stream RTSP del VTO.

#### Escenario: Snapshot solicitado

- DADO que el stream RTSP del VTO esta disponible
- CUANDO una persona ejecuta la captura de snapshot
- ENTONCES el proyecto guarda una imagen del stream en una ruta local elegida
