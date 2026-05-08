# Diseno: Alineacion de intercom-routing

## Decision 1: Especificar el adaptador principal, no el legado

La spec viva debe describir el adaptador principal del stack vigente.
Asterisk puede seguir existiendo como adaptador legado o fino, pero deja de ser el comportamiento base de `intercom-routing`.

## Decision 2: Routing por artefactos de runtime

En el stack actual, el enrutamiento no termina en contestar una extension.
El punto de intercambio observable es el deposito de `WAV` y metadata en `runtime/baresip/inbox`, seguido por artefactos procesados y solicitudes de autorizacion por sesion.

## Decision 3: Incluir el loop de autorizacion de departamento

Como `contact_department` es parte del flujo normal para visitantes no reconocidos, `intercom-routing` debe cubrir tambien el contrato de requests/responses por sesion en `runtime/baresip/department_authorization`.
