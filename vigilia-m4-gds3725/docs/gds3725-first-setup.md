# GDS3725 First Setup

Guia corta para la primera prueba de `GDS3725 -> baresip -> VIGILIA` sin Asterisk.

## Objetivo

Levantar una primera llamada SIP simple entre el `GDS3725` y el `Mac mini M4`, minimizando variables.

## Supuestos Iniciales

- `Mac mini M4`: `192.168.100.50`
- `GDS3725`: `192.168.100.60`
- cuenta local VIGILIA / `baresip`: `vigilia`
- cuenta del dispositivo: `door`
- transporte inicial: `UDP`

## 1. Preparar el lado VIGILIA

En el `Mac mini`:

```bash
cd vigilia-m4-gds3725
cp .env.example .env
./scripts/prepare_baresip_runtime.sh
./scripts/run_baresip_local.sh
```

Verifica que el archivo [runtime/baresip/accounts](/Users/alvaroc/Proyectos/VIGILIA-MatIA/vigilia-m4-gds3725/runtime/baresip/accounts:1) contenga una linea parecida a esta:

```text
<sip:vigilia@192.168.100.50:5060;transport=udp>;regint=0
```

## 2. Configurar el GDS3725

Usa estos valores como primera prueba:

- `Account Active`: `Yes`
- `SIP Server`: `192.168.100.50`
- `Outbound Proxy`: vacio
- `SIP User ID`: `door`
- `Authenticate ID`: `door`
- `Authenticate Password`: define una clave fuerte y guardala
- `Name`: `GDS3725 Front Door`
- `SIP Transport`: `UDP`
- `Local SIP Port`: `5060`
- `NAT Traversal`: `No`
- `SRTP`: `Disabled`
- `TLS`: `Disabled`
- `DTMF`: `RFC2833`

## 3. Codecs Recomendados Para La Primera Prueba

Orden sugerido:

1. `G.722`
2. `G.711u`
3. `G.711a`

## 4. Primera Prueba

- deja corriendo `baresip`
- inicia la llamada desde el `GDS3725`
- confirma si el `Mac mini` recibe intento SIP
- si no hay audio, prueba primero con `G.711u`

## 5. Mantener La Prueba Simple

Para la primera iteracion:

- no usar `TLS`
- no usar `SRTP`
- no usar `Outbound Proxy`
- no usar NAT traversal si ambos estan en la misma LAN
- no abrir porton real

## 6. Resultado Esperado

La meta de la primera prueba no es abrir el porton.

La meta es confirmar:

- que el `GDS3725` llama a la cuenta correcta
- que `baresip` recibe la sesion
- que la ruta `GDS3725 -> Mac mini` funciona sin Asterisk

## 7. Proximo Paso

Una vez confirmada la sesion SIP:

- capturar el audio
- conectarlo a la capa de transcripcion
- dejar `dry-run` para la decision
- recien despues evaluar apertura real
