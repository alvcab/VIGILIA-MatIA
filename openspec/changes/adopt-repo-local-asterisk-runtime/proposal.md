# Propuesta: Adoptar runtime repo-local para Asterisk y artefactos operativos

## Por Que

El prototipo actual depende de una mezcla de artefactos dentro y fuera del repositorio:

- configuraciones activas de Asterisk fuera del repo
- sockets, logs y audios temporales en `/tmp`
- comandos manuales distintos segun la maquina

Eso dificulta portar el proyecto a un Jetson u otra maquina nueva.

## Que Cambia

- Definir un runtime local dentro del repositorio para Asterisk
- Renderizar configuraciones activas desde plantillas del repo
- Mover sockets, logs y audios temporales de VIGILIA a un directorio runtime del proyecto
- Agregar scripts para preparar, iniciar y controlar Asterisk usando ese runtime

## No Objetivos

- Versionar el binario de Asterisk
- Empaquetar todas las dependencias del sistema dentro del repositorio
- Cambiar la politica funcional de acceso por si sola
