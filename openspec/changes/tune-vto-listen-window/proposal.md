# Propuesta: ajustar la ventana de escucha del VTO

## Motivacion

En el VTO actual el visitante no escucha de forma confiable el audio reproducido por Asterisk. Eso hace que un saludo o tono del PBX no ayude a la experiencia real y, en cambio, consuma tiempo antes de capturar la voz.

## Alcance

- Priorizar una captura de voz mas inmediata en llamadas reales del VTO
- Extender la ventana de escucha para que el visitante tenga mas tiempo para hablar
- Mantener el modo `hello-only` como diagnostico separado

## No objetivos

- No resolver en este cambio la reproduccion de voz por el parlante del VTO
- No cambiar la politica de decision de acceso
