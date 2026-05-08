# Diseno: Endurecimiento de autorizacion de acceso

## Decision 1: Autorizacion de departamento ligada a estado previo

El watcher y el evaluador deben comprobar que la memoria de sesion este en `waiting_for_department_response` antes de aceptar `approved`, `denied` o `no_response`.
Si la respuesta llega fuera de contexto o con un estado invalido, el evento se archiva como ignorado y el flujo no abre.

## Decision 2: Match facial confiable solo para residentes resolubles

Un match facial confiable deja de ser suficiente por si solo.
La metadata facial debe resolver a un residente existente en `ResidentDirectory`, preferentemente por `resident_id` y, como respaldo, por nombre visible resoluble.
Si no resuelve, el flujo degrada a no-match.

## Decision 3: Parsing de reply con tokens completos

La interpretacion de audio del departamento deja de usar subcadenas crudas.
Los marcadores de aprobacion o rechazo se detectan por frases tokenizadas, para evitar falsos positivos como `visita` conteniendo `si`.
