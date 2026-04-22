# Delta de visitor-access

## Requisitos Modificados

### Requisito: Restringir la apertura del porton a decisiones positivas

El sistema DEBE abrir el porton solo cuando la capa de decision devuelve un token positivo explicito y exacto.

#### Escenario: Decision positiva exacta del modelo

- DADO que la respuesta del modelo es exactamente el token `OPEN`
- CUANDO el flujo de manejo de comandos evalua la respuesta
- ENTONCES el sistema dispara el comando de apertura del porton

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
