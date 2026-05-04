# Diseno: respuestas habladas generadas por IA para visitantes

## Resumen

Se agrega una segunda etapa de modelo despues de la decision de acceso:

1. `query_access_model(...)` sigue clasificando la intencion en `OPEN`, `HOLA` o `ERROR` solo para los casos que aun necesitan modelo
2. `resolve_access_decision(...)` sigue siendo la unica fuente de verdad para abrir o no abrir
3. una nueva funcion `query_spoken_response_model(...)` redacta una frase breve en espanol para el visitante
4. si esa generacion falla o entrega una salida invalida, el sistema usa una respuesta fija de respaldo
5. saludos, paquetes y visitas sin solicitud explicita de apertura pueden resolverse primero con reglas locales, sin depender del token del modelo
6. en modo local por Mac, una visita ambigua puede activar un segundo turno breve para pedir residente o departamento y volver a escuchar

## Reglas

- La respuesta hablada generada por IA nunca cambia `should_open`
- La respuesta debe ser corta, en espanol y pensada para TTS
- El segundo turno local solo se usa en pruebas o ejecucion desde host y no reemplaza todavia el flujo real del VTO
- El flujo puede entregar respuestas como:
  - indicar a quien viene
  - dejar paquete en conserjeria
  - avisar que el acceso fue concedido
  - pedir repetir por audio poco claro
  - pedir un segundo turno local cuando falta residente o departamento

## Resiliencia

- Si la generacion tarda demasiado o falla, se mantiene el mensaje fijo tradicional
- Si el modelo devuelve una respuesta vacia o demasiado larga, se usa el fallback fijo
