# Preparacion Del Mac mini M4

Guia corta para dejar el `Mac mini M4` listo antes de conectar el `GDS3725`.

## Objetivo

Llegar al primer dia de pruebas con el host preparado, con menos friccion y menos variables.

## 1. Red

Definir una IP fija o una reserva DHCP para el `Mac mini`.

Ejemplo:

- `Mac mini M4`: `192.168.100.50`
- `GDS3725`: `192.168.100.60`

La primera prueba debe hacerse idealmente:

- en la misma LAN
- sin VPN
- sin NAT entre ambos
- sin proxy SIP

## 2. Nombre Del Host

Usar un nombre simple y estable.

Ejemplo:

- `vigilia-m4`

Esto ayuda para logs, mDNS y diagnostico local, aunque la primera prueba conviene hacerla por IP.

## 2.1 Antigravity

Antigravity se instala manualmente porque es una aplicacion de escritorio con
login, permisos de macOS y configuracion de editor.

En el Mac mini:

1. Descargar desde la pagina oficial:

```text
https://antigravity.google/download
```

2. Abrir el `.dmg`.
3. Arrastrar `Antigravity` a `Applications`.
4. Abrir la app y permitirla en `System Settings -> Privacy & Security` si macOS
   la bloquea en el primer arranque.
5. Iniciar sesion con Gmail.
6. Abrir el repo:

```text
/Users/vigilia/VIGILIA-MatIA
```

7. Instalar o habilitar la extension de navegador solo si se va a usar el
   agente para tareas web. Para VIGILIA/GDS no es obligatoria.

Antigravity no reemplaza el servicio local de MatIA. El servicio real sigue
corriendo con:

```bash
./scripts/matia_gds_service.sh
```

Antigravity queda como IDE/agente para editar, revisar logs y operar el repo.

## 3. Python y Repo

Clonar el repo y validar que el scaffold corra:

```bash
cd vigilia-m4-gds3725
./scripts/bootstrap_mac_mini.sh
```

Ese bootstrap crea `.env` si falta, prepara `.venv`, instala dependencias de
Python, valida `ffmpeg`, `baresip` y `say`, prepara runtime y corre la suite.

## 4. Variables De Entorno

Copiar el ejemplo:

```bash
cp .env.example .env
```

Y revisar al menos:

- `VIGILIA_SIP_LOCAL_DOMAIN`
- `VIGILIA_SIP_DEVICE_DOMAIN`
- `VIGILIA_BARESIP_BINARY`

## 5. Runtime De Baresip

Preparar el runtime:

```bash
./scripts/prepare_baresip_runtime.sh
```

Eso debe dejar creados:

- [runtime/baresip/config](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/config:1)
- [runtime/baresip/accounts](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/accounts:1)

## 6. Audio Del Mac

Antes de probar SIP real:

- confirmar que el `Mac mini` tiene salida de audio funcional
- confirmar si el microfono local sera usado o no
- dejar desactivadas mejoras raras de terceros si existen

Para la primera prueba SIP, el objetivo es:

- recibir sesion
- confirmar routing

No hace falta obsesionarse aun con calidad final de audio.

## 7. Firewall

Revisar que el `Mac mini` no bloquee la primera prueba local.

En especial:

- puerto SIP local
- trafico UDP en la LAN

## 8. Baresip

Si `baresip` ya esta instalado, validar:

```bash
baresip -h
```

Y luego:

```bash
./scripts/run_baresip_local.sh
```

Si todavia no esta instalado, no bloquea el trabajo del repo, pero si bloquea la primera llamada real.

## 9. Meta De La Primera Prueba

Antes de pensar en IA, TTS o apertura real, confirmar solo esto:

- el `GDS3725` puede llamar al `Mac mini`
- `baresip` recibe la sesion
- el `Mac mini` no introduce una latencia absurda

## 10. Proximo Paso

Una vez que el `Mac mini` este listo:

- configurar el `GDS3725`
- hacer la primera llamada SIP
- capturar resultados
- recien despues conectar transcripcion y decision

## 11. Servicio Local De MatIA

Para dejar a MatIA esperando llamadas del GDS en loop:

```bash
./scripts/matia_gds_service.sh
```

Ese servicio ejecuta el flujo guardado:

```bash
./scripts/abrir_con_rostro_identificable.sh
```

Los logs quedan en:

```text
runtime/logs/matia-gds-service.log
```

Para correr solo un ciclo:

```bash
VIGILIA_SERVICE_RUN_ONCE=1 ./scripts/matia_gds_service.sh
```

Hay una plantilla de `launchd` en:

```text
launchd/com.vigilia.matia-gds.plist.example
```

En el Mac mini final hay que ajustar las rutas de esa plantilla al path real
del repo antes de instalarla.
