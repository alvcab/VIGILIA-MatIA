# Propuesta: Alinear intercom-routing con el stack actual

## Por Que

La spec viva de `intercom-routing` todavia describe el prototipo minimo con Asterisk y eco de audio.
El comportamiento actual del stack nuevo ya usa `baresip`, `MatIA` y VIGILIA como contrato principal, por lo que la documentacion de routing debe reflejar esa realidad.

## Que Cambia

- Reemplazar la descripcion centrada en Asterisk por el contrato operativo actual del stack `GDS3725 -> baresip -> MatIA -> VIGILIA`
- Documentar el inbox de audio y metadata como punto de integracion de llamadas entrantes
- Documentar el runtime de autorizacion de departamento por sesion como parte del enrutamiento conversacional

## No Objetivos

- Implementar una nueva integracion SIP real
- Eliminar el prototipo legacy en `v1/`
- Redefinir la policy de acceso
