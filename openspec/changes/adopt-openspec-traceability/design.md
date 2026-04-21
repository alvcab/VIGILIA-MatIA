# Diseno: Adoptar OpenSpec para la trazabilidad del repositorio

## Resumen

Este cambio introduce OpenSpec de una forma amigable para un proyecto ya existente.
En lugar de bloquear el avance esperando la instalacion oficial de la CLI, el repositorio adopta directamente la estructura canonica y sus documentos.

Eso entrega valor inmediato:

- historial persistente de cambios dentro del repo
- separacion mas clara entre comportamiento actual y comportamiento propuesto
- mejor contexto de onboarding para futuras sesiones de trabajo

## Estructura Elegida

El repositorio usara:

- `openspec/specs/` para el comportamiento actual considerado fuente de verdad
- `openspec/changes/<change-id>/` para el trabajo propuesto
- `AGENTS.md` en la raiz para guiar el flujo de Codex

## Dominios Base

El sistema actual se separa en dos dominios iniciales de specs:

- `visitor-access`
- `intercom-routing`

Esto mantiene la primera version pequena y cercana a los limites reales del codigo.

## Tradeoffs

- Pro: no depende de una instalacion externa para empezar a usar el flujo
- Pro: es compatible con las convenciones oficiales de carpetas de OpenSpec
- Contra: la integracion de slash commands de la CLI aun no esta activa
- Contra: las validaciones y el archivado siguen siendo manuales hasta instalar la CLI

## Mejoras Futuras

- Instalar la CLI oficial de OpenSpec y generar integracion de prompts para Codex
- Agregar specs para gestion de secretos y seguridad operacional
- Agregar un proceso de archivado cuando el equipo complete sus primeros cambios trazados
