# Instalacion De Baresip En macOS

Guia corta para preparar `baresip` en el `Mac mini M4` antes de la primera prueba con `GDS3725`.

## Objetivo

Confirmar que `baresip` existe, arranca y puede usar el runtime generado por VIGILIA.

## 1. Antes De Instalar

Primero valida que el repo esta sano:

```bash
cd vigilia-m4-gds3725
python3 -m unittest discover -s tests -v
./scripts/prepare_baresip_runtime.sh
```

## 2. Opciones De Instalacion

La idea del repo no es casarse con una unica forma de instalar `baresip`.

Opciones razonables:

- `Homebrew`, si tienes una formula disponible en tu entorno
- `MacPorts`, si prefieres una ruta mas tradicional
- compilacion manual, si luego necesitas ajustar modulos

## 3. Validacion Minima

Una vez instalado:

```bash
baresip -h
```

La meta aqui no es que ya llame al `GDS3725`, sino confirmar que el binario existe y responde.

## 4. Validacion Con VIGILIA

Con el repo preparado:

```bash
cd vigilia-m4-gds3725
./scripts/run_baresip_local.sh
```

Ese script:

- prepara el runtime si hace falta
- usa [runtime/baresip/config](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/config:1)
- usa [runtime/baresip/accounts](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/accounts:1)

## 5. Que Revisar Si Falla

- que `VIGILIA_BARESIP_BINARY` apunte al binario correcto
- que el archivo `runtime/baresip/config` exista
- que el archivo `runtime/baresip/accounts` exista
- que el puerto SIP local no este ocupado
- que el firewall del Mac no bloquee la prueba

## 6. Que No Optimizar Todavia

En esta etapa no hace falta obsesionarse con:

- `TLS`
- `SRTP`
- NAT traversal
- audio perfecto
- integracion con apertura real

Primero queremos:

- binario presente
- runtime valido
- arranque local correcto

## 7. Resultado Esperado

La instalacion esta suficientemente bien cuando:

- `baresip -h` funciona
- `./scripts/run_baresip_local.sh` arranca sin error trivial
- el runtime generado por VIGILIA coincide con la cuenta SIP esperada

## 8. Proximo Paso

Una vez validado `baresip`:

- configurar el `GDS3725`
- probar la primera llamada SIP real
- capturar observaciones
