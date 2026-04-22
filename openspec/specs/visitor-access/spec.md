# Especificacion de visitor-access

## Proposito

Definir el comportamiento actual del prototipo de acceso para visitantes del condominio, incluyendo interpretacion de solicitudes, decisiones de acceso y accionamiento del porton.

## Requisitos

### Requisito: Interpretar la intencion del visitante

El sistema DEBE interpretar una solicitud hablada o escrita del visitante para determinar si esta pidiendo acceso.

#### Escenario: Solicitud directa de apertura del porton

- DADO que un visitante pide abrir la puerta o el porton
- CUANDO la solicitud es procesada por el flujo del modelo local o por reglas locales tolerantes a errores menores de transcripcion
- ENTONCES el resultado de decision se trata como una solicitud de acceso

#### Escenario: Entrada de voz vacia o poco clara

- DADO que el audio grabado no produce texto utilizable
- CUANDO el resultado de la transcripcion queda vacio
- ENTONCES el sistema pide al visitante que lo intente nuevamente
- Y el porton permanece cerrado

### Requisito: Restringir la apertura del porton a decisiones positivas

El sistema DEBE abrir el porton solo cuando la capa de decision devuelve un token positivo explicito y exacto.

#### Escenario: Decision positiva exacta del modelo

- DADO que la respuesta del modelo es exactamente el token `OPEN`
- CUANDO el flujo de manejo de comandos evalua la respuesta
- ENTONCES el sistema dispara el comando de apertura del porton

#### Escenario: Decision negativa o no reconocida del modelo

- DADO que la respuesta del modelo no es exactamente el token `OPEN`
- CUANDO el flujo de manejo de comandos evalua la respuesta
- ENTONCES el sistema rechaza la solicitud
- Y el porton permanece cerrado

#### Escenario: Respuesta verbosa o fuera de contrato del modelo

- DADO que la respuesta del modelo incluye texto adicional, eco del prompt o tokens validos dentro de una respuesta mas larga
- CUANDO el flujo de manejo de comandos evalua la respuesta
- ENTONCES el sistema trata la respuesta como invalida
- Y el porton permanece cerrado

#### Escenario: Apertura por voz clara y rostro autorizado dentro de tolerancia

- DADO que la voz contiene una solicitud clara de apertura, incluso si la transcripcion tiene errores menores
- Y el rostro coincide con una persona habilitada dentro de la tolerancia del motor facial
- CUANDO el flujo hibrido evalua la solicitud
- ENTONCES el sistema permite abrir el porton

### Requisito: Entregar retroalimentacion al visitante

El sistema DEBE proporcionar retroalimentacion audible o textual que describa el resultado de la solicitud de acceso.

#### Escenario: Acceso concedido

- DADO que se toma una decision positiva de acceso
- CUANDO se dispara el comando de apertura del porton
- ENTONCES el visitante recibe un mensaje indicando que el acceso fue concedido

#### Escenario: Acceso denegado

- DADO que la solicitud es denegada o no puede ser procesada
- CUANDO el flujo de decision termina
- ENTONCES el visitante recibe un mensaje indicando rechazo o falla temporal
