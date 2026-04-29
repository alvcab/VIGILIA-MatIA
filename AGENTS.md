# VIGILIA MatIA

## Resumen del Proyecto

Este repositorio contiene un prototipo de control de acceso para el porton de un condominio.
El sistema actual combina:

- Scripts en Python para decision y orquestacion
- Configuracion de Asterisk SIP para la ruta del citofono
- Prompts de LLM local a traves de Ollama
- Control HTTP del dispositivo Dahua

El objetivo principal es evolucionar el flujo de acceso de forma segura y trazable.

## Acuerdo de Trabajo

- Usa los artefactos de OpenSpec en `openspec/` antes de hacer cambios no triviales en el codigo.
- Mantiene los requisitos de comportamiento en `openspec/specs/`.
- Mantiene los cambios propuestos en `openspec/changes/<change-id>/`.
- Prefiere actualizar las specs cuando cambie el comportamiento visible externamente.
- Mantiene los detalles de implementacion en `design.md` y los pasos de ejecucion en `tasks.md`.
- Mantiene el codigo fuente en ingles, aunque la documentacion y los artefactos de OpenSpec esten en espanol.

## Notas de Seguridad

- Trata las IP, usuarios y contrasenas de dispositivos como informacion sensible.
- No introduzcas nuevas credenciales hardcodeadas.
- Prefiere variables de entorno o archivos locales de configuracion excluidos de versionado.
- Ten especial cuidado con cualquier cambio que pueda abrir el porton real.

## Puntos de Referencia del Repo

- `v1/vigilia.py`: flujo de comandos por texto
- `v1/puente_vigilia.py`: flujo de audio a decision
- `v1/asterisk/`: configuracion SIP y dialplan
- `test_conserje.py`: prototipo de disparo manual local

## Flujo OpenSpec

Para cambios importantes, sigue este flujo liviano:

1. Crea o actualiza una carpeta de cambio en `openspec/changes/`.
2. Escribe `proposal.md` con alcance, motivacion y no-objetivos.
3. Escribe o actualiza las delta specs en `openspec/changes/<change-id>/specs/`.
4. Documenta las decisiones tecnicas en `design.md`.
5. Divide la implementacion en pasos verificables dentro de `tasks.md`.
6. Implementa el codigo.
7. Integra el comportamiento final en `openspec/specs/` cuando el cambio este completo.

Para ediciones pequenas, typos o refactors claramente internos, el flujo puede ser mas liviano, pero las specs deben seguir reflejando el comportamiento real si este cambia.
