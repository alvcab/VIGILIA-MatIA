# Propuesta: flujo VTO con rostro primero

## Motivacion

El uso deseado tiene dos caminos claros:

1. si el sistema reconoce inmediatamente al residente por rostro, debe abrir sin esperar una frase
2. si no lo reconoce, debe pasar al flujo de voz para que el visitante diga a que departamento viene

## Alcance

- Agregar una verificacion facial rapida al inicio de la llamada del VTO
- Abrir de inmediato cuando exista match facial confiable de residente habilitado
- Caer al flujo normal de escucha cuando ese match no exista

## No objetivos

- No resolver en este cambio la reproduccion del mensaje de pregunta por el parlante del VTO
- No reemplazar la politica hibrida de voz + rostro para visitantes no reconocidos
