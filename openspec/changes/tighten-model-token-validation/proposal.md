# Propuesta: Endurecer validacion de tokens del modelo

## Por Que

El flujo actual considera positiva cualquier respuesta del modelo que contenga la palabra `OPEN`.
Eso permite aperturas indebidas cuando el modelo devuelve texto libre, eco del prompt o listados de tokens validos.

## Que Cambia

- Aceptar como decision del modelo solo tokens exactos `OPEN`, `ERROR` o `HOLA`
- Tratar cualquier respuesta extensa o fuera de contrato como rechazo seguro
- Endurecer el prompt y el `Modelfile` para sesgar la salida hacia un unico token
- Tolerar errores menores de transcripcion cuando la voz pide apertura y el rostro autorizado coincide dentro de la tolerancia facial
- Mantener un servicio local persistente Whisper-only entre llamadas
- Reintentar una vez el snapshot facial cuando hay una solicitud clara de apertura y el primer matching falla
- Promover frases reales observadas en la base local a repertorio de acceso conocido
- Separar bandas faciales explicitas para distinguir match confiable, borderline y no confiable
- Cubrir el parsing con una prueba automatizada minima

## No Objetivos

- Cambiar la politica hibrida de voz mas rostro
- Agregar un modo dry-run del porton en este cambio

## Criterios de Exito

- Una respuesta extensa del modelo que incluya la palabra `OPEN` no abre el porton
- Las respuestas exactas siguen siendo interpretadas correctamente
- El modelo local queda mejor orientado a responder solo un token
- La ruta hibrida sigue funcionando aunque Whisper deforme ligeramente frases claras de apertura
- El costo de arranque de Whisper se reduce al reutilizar un proceso local, con fallback rapido si el servicio no responde
- El matching facial queda menos sensible a un snapshot puntual malo
- La decision usa mejor los datos reales acumulados en la base local
- El comportamiento queda reflejado en OpenSpec
