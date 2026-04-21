# Propuesta: Adoptar OpenSpec para la trazabilidad del repositorio

## Por Que

El proyecto hoy evoluciona directamente a traves de cambios en codigo y configuracion, lo que dificulta seguir la intencion, el alcance y el impacto funcional a lo largo del tiempo.

OpenSpec le dara al repositorio una capa liviana de planificacion y trazabilidad para que los futuros cambios puedan revisarse como:

- propuesta
- delta spec
- diseno
- tareas

## Que Cambia

- Agregar un espacio de trabajo `openspec/` al repositorio
- Capturar el comportamiento base actual como specs vivas
- Definir un flujo estandar de cambios para trabajo futuro
- Agregar guias para agentes de modo que Codex use este flujo por defecto

## No Objetivos

- Reescribir la implementacion existente en Python o Asterisk en este cambio
- Instalar herramientas externas o cambiar la configuracion global de la maquina
- Resolver los problemas actuales de seguridad del prototipo como parte de este paso

## Criterios de Exito

- El repositorio tiene una estructura `openspec/` utilizable
- El comportamiento actual del sistema esta representado en specs base
- Los futuros cambios tienen un lugar claro donde documentar intencion antes de tocar codigo
