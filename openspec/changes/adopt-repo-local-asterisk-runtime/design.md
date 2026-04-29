# Diseno: Runtime repo-local de VIGILIA

## Objetivo

Separar el runtime operativo del proyecto del layout instalado de Asterisk en la maquina.

El repositorio pasa a ser la fuente de verdad de:

- configuracion de Asterisk
- dialplan
- prompts y respuestas
- sockets y logs de VIGILIA
- scripts de arranque y control

## Enfoque

### 1. Runtime dentro del repo

Se define `.runtime/` como raiz operativa local. Alli viven:

- `run/` para sockets y pidfiles
- `logs/` para logs
- `audio/` para grabaciones y respuestas
- `asterisk/` para configuracion renderizada y runtime de Asterisk

### 2. Plantillas fuente en el repo

Los archivos fuente de Asterisk permanecen versionados en `v1/asterisk/`.
Un script de preparacion renderiza configuraciones activas con rutas absolutas del repo.

### 3. Asterisk con `-C`

En vez de depender de `/usr/local/asterisk/etc/asterisk`, el arranque usa:

- binario del sistema instalado
- `asterisk.conf` repo-local
- directorios repo-locales para `astetcdir`, `astlogdir`, `astrundir` y similares

### 4. Variables compartidas

Los scripts shell y Python comparten rutas a traves de variables `VIGILIA_*`.
Si no se exportan, se resuelven automaticamente desde el repositorio.

## Beneficios

- menos pasos manuales entre maquinas
- mayor trazabilidad de la configuracion activa
- menor dependencia de `/tmp`
- camino mas limpio para migrar a Jetson
