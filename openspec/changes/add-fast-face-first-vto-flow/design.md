# Diseno: rostro primero en llamadas del VTO

## Resumen

Antes de grabar audio del visitante, el dialplan ejecuta una verificacion facial rapida. Si el resultado indica residente conocido habilitado con match confiable, el sistema abre y termina la llamada. Si no, continua con la ventana normal de escucha.

## Decisiones

- La verificacion rapida no depende de transcripcion ni de modelo
- La apertura rapida usa la misma logica de puerta, pero sin esperar sintetizar una respuesta
- El evento de autoapertura por rostro queda registrado con una razon explicita
- Si el rostro no da match confiable, la llamada sigue al flujo normal
- La verificacion rapida puede hacer varios snapshots cortos para mejorar la probabilidad de detectar la cara real al presionar el boton
- El reconocimiento facial rapido reutiliza un servicio persistente por socket UNIX cuando esta disponible, y cae al proceso por llamada solo como respaldo
- La captura de snapshot rapido puede priorizar un endpoint HTTP/JPEG del VTO y caer a RTSP si ese camino falla
