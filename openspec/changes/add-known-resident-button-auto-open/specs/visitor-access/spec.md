# Delta de visitor-access

## Requisitos Modificados

### Requisito: Restringir la apertura del porton a decisiones positivas

#### Escenario: Autoapertura silenciosa para residente conocido al presionar el boton

- DADO que un residente conocido presiona el boton del VTO
- Y el sistema logra un match facial confiable con una persona habilitada vinculada a un `resident_id`
- Y el audio posterior queda vacio o no aporta texto util
- CUANDO el flujo hibrido evalua la llamada
- ENTONCES el sistema puede abrir el porton sin exigir una solicitud verbal adicional

#### Escenario: Autoapertura con saludo corto para residente conocido

- DADO que un residente conocido presiona el boton del VTO
- Y el sistema logra un match facial confiable con una persona habilitada vinculada a un `resident_id`
- Y el audio posterior contiene solo un saludo breve sin pedir explicitamente abrir
- CUANDO el flujo hibrido evalua la llamada
- ENTONCES el sistema puede abrir el porton como residente conocido
