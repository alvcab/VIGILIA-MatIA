# Diseno: ventana de escucha mas util para el VTO

## Resumen

El dialplan real del VTO deja de depender de `Playback()` antes de grabar y pasa a capturar la voz casi de inmediato.

## Decisiones

- El flujo normal del VTO omite `vigilia_prompt` y `vigilia_listen`
- La captura SIP/RTSP se mantiene como fuente de audio del visitante
- La ventana de captura aumenta para darle margen real al visitante
- El modo `hello-only` conserva los audios de prueba para diagnostico
