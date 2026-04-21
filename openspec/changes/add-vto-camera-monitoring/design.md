# Diseno: Agregar monitoreo de camara del VTO

## Resumen

La implementacion reutilizara herramientas ya disponibles en la maquina:

- `ffplay` para vista en vivo
- `ffmpeg` para capturas

Esto evita agregar nuevas dependencias Python y deja una integracion muy cercana a la prueba que ya fue validada manualmente.

## URL Base del Stream

El flujo de video se obtiene desde:

- `rtsp://<user>:<password>@<ip>:554/cam/realmonitor?channel=1&subtype=0`

Se dejara configurable por constantes y argumentos de linea de comandos.

## API del Modulo

El modulo expondra funciones para:

- construir la URL RTSP
- abrir la vista en vivo
- capturar un snapshot

Tambien tendra una interfaz CLI minima para uso directo desde terminal.

## Tradeoffs

- Pro: no agrega librerias nuevas
- Pro: se apoya en herramientas ya comprobadas en la maquina
- Contra: depende de que `ffplay` y `ffmpeg` esten instalados
- Contra: la vista en vivo se abre como proceso externo, no embebida en una GUI Python
