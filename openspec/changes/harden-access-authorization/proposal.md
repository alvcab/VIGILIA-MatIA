# Propuesta: Endurecer autorizacion de acceso

## Por Que

El stack actual ya puede abrir por coincidencia facial confiable y por autorizacion de departamento.
Esos caminos deben fallar en cerrado cuando la metadata externa llega incompleta, fuera de contexto o con texto ambiguo.

## Que Cambia

- Exigir que una autorizacion de departamento solo sea aceptada cuando la sesion realmente este esperando esa respuesta
- Requerir que un `face_match_trusted` resuelva a un residente conocido antes de autoabrir
- Endurecer la interpretacion de respuestas habladas del departamento para evitar coincidencias parciales accidentales

## No Objetivos

- Redisenar el flujo completo de telefonia
- Introducir una nueva fuente de verdad de residentes
- Habilitar apertura real adicional
