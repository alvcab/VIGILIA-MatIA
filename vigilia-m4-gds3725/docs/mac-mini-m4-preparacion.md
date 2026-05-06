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

## 3. Python y Repo

Clonar el repo y validar que el scaffold corra:

```bash
cd vigilia-m4-gds3725
python3 -m unittest discover -s tests -v
python3 -m app.main --mode sip-preview --caller-id gds-front-door
python3 -m app.main --mode baresip-preview --caller-id gds-front-door
```

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
