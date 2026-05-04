# Propuesta: respuestas habladas generadas por IA para visitantes

## Motivacion

Hoy VIGILIA puede decidir apertura o rechazo, pero la respuesta audible al visitante sigue siendo fija y muy limitada. Eso impide entregar mensajes utiles en escenarios comunes como:

- visitas que solo saludan
- repartidores que vienen a dejar un paquete
- visitantes que no dicen a que residente vienen

El sistema ya corre en el Mac con reproduccion local, por lo que ahora es viable enriquecer la respuesta hablada sin depender del parlante del VTO.

## Alcance

- Mantener la decision de apertura separada y segura
- Agregar una segunda consulta al modelo para redactar una respuesta corta en espanol
- Reproducir esa respuesta generada por IA usando el flujo TTS ya existente
- Mantener mensajes de respaldo deterministas cuando el modelo no responda bien

## No objetivos

- No permitir que el texto generado por IA influya en la apertura del porton
- No reemplazar la politica hibrida actual de reconocimiento facial y contexto residente
- No resolver en este cambio la reproduccion por parlante del VTO
