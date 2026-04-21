# Especificacion de intercom-routing

## Proposito

Describir el comportamiento actual de telefonia y enrutamiento del citofono usado por la integracion prototipo con Asterisk.

## Requisitos

### Requisito: Aceptar trafico SIP del dispositivo de citofonia configurado

El sistema DEBE identificar y aceptar trafico SIP proveniente del endpoint VTO configurado.

#### Escenario: IP de origen VTO conocida

- DADO que llega una solicitud SIP desde la direccion IP configurada del VTO
- CUANDO Asterisk evalua la identificacion del endpoint
- ENTONCES la solicitud queda asociada al endpoint VTO

### Requisito: Enrutar llamadas del VTO al contexto del citofono

El sistema DEBE enrutar las llamadas identificadas del VTO al contexto de dialplan configurado.

#### Escenario: Llamada entrante desde el VTO

- DADO que el endpoint VTO fue identificado
- CUANDO la llamada es entregada al dialplan
- ENTONCES Asterisk ejecuta el contexto `from-vto`

### Requisito: Mantener el comportamiento actual del flujo prototipo

El sistema DEBE conservar el flujo minimo actual de manejo de llamadas hasta que se especifique una interaccion de voz mas completa.

#### Escenario: Comportamiento actual del prototipo

- DADO que una llamada llega a la extension `1000` dentro del contexto `from-vto`
- CUANDO el dialplan se ejecuta
- ENTONCES la llamada es contestada
- Y el sistema espera brevemente
- Y el audio es devuelto en eco
