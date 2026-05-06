# Proposal: Create `vigilia-m4-gds3725` Repository Skeleton

## Why

El prototipo actual de VIGILIA fue afinado alrededor de Dahua, RTSP y Asterisk.
Ese trabajo sirvio para aprender sobre latencia, diagnostico de audio y politicas de acceso, pero ya no es una base limpia para la siguiente etapa del sistema.

La siguiente plataforma objetivo es:

- `Mac mini M4` como host principal
- `Grandstream GDS3725` como intercom / door station
- servicios desacoplados para audio, transcripcion, decision y apertura

Para esa etapa conviene separar desde ya un repositorio nuevo, pensado sin Asterisk como requisito estructural.

## Scope

- Crear un scaffold inicial de `vigilia-m4-gds3725`
- Documentar una arquitectura base sin Asterisk como capa obligatoria
- Definir modos de prueba seguros como `audio-only`, `decision-only` y `dry-run`
- Incluir una base minima ejecutable para policy y simulacion

## Non-Goals

- Migrar inmediatamente el flujo operativo actual
- Integrar apertura real del porton en el nuevo scaffold
- Implementar de inmediato una pila SIP completa
- Reemplazar el prototipo Dahua actual
