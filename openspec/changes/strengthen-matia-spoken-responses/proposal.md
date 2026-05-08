# Propuesta: Fortalecer respuestas habladas de MatIA

## Por Que

El stack actual ya puede generar respuestas habladas para visitantes, pero la salida todavia depende demasiado de texto libre del backend.
Necesitamos respuestas mas claras, cortas y estables para TTS, con fallback cuando el modelo devuelva eco del prompt, texto vacio o mensajes demasiado largos.

## Que Cambia

- Hacer mas explicitas las instrucciones de redaccion para respuestas habladas
- Sanitizar la salida generada para que sea breve, clara y apta para TTS
- Caer a fallback determinista cuando la salida del modelo no cumpla el contrato esperado

## No Objetivos

- Cambiar la decision de apertura
- Agregar un nuevo proveedor de modelo
- Redisenar el flujo de autorizacion
