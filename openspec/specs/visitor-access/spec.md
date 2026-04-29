# Especificacion de visitor-access

## Proposito

Definir el comportamiento actual del prototipo de acceso para visitantes del condominio, incluyendo interpretacion de solicitudes, decisiones de acceso y accionamiento del porton.

## Requisitos

### Requisito: Interpretar la intencion del visitante

El sistema DEBE interpretar una solicitud hablada o escrita del visitante para determinar si esta pidiendo acceso.

#### Escenario: Solicitud directa de apertura del porton

- DADO que un visitante pide abrir la puerta o el porton
- CUANDO la solicitud es procesada por el flujo del modelo local, por reglas locales tolerantes a errores menores de transcripcion o por frases observadas y aprobadas en la base local
- ENTONCES el resultado de decision se trata como una solicitud de acceso

#### Escenario: Frase observada promovida desde eventos exitosos

- DADO que una transcripcion observada abre repetidamente mediante la politica hibrida
- CUANDO el sistema consulta su repertorio local de acceso
- ENTONCES esa frase puede tratarse como una solicitud conocida de apertura

#### Escenario: Solicitud de apertura con transcripcion parcial o ruidosa

- DADO que la transcripcion contiene palabras de apertura degradadas o incompletas
- CUANDO la politica local detecta suficiente parecido en keywords o tokens de una frase conocida
- ENTONCES el sistema trata la solicitud como un pedido de acceso

#### Escenario: Entrada de voz vacia o poco clara

- DADO que el audio grabado no produce texto utilizable
- CUANDO el resultado de la transcripcion queda vacio
- ENTONCES el sistema pide al visitante que lo intente nuevamente
- Y el porton permanece cerrado

#### Escenario: Timeout o falla de transcripcion local

- DADO que la captura de voz existe pero la transcripcion local falla o excede su timeout
- O la carga local de Whisper/Torch falla o se interrumpe antes de transcribir
- CUANDO el flujo de audio intenta obtener texto del visitante
- ENTONCES el sistema trata el resultado como audio no entendible
- Y responde sin dejar el flujo en error

#### Escenario: Modelo lento o no disponible

- DADO que la politica hibrida no alcanza para decidir por si sola
- Y la consulta al modelo local falla, excede el timeout o no responde
- CUANDO el flujo de audio termina de evaluar la solicitud
- ENTONCES el sistema rechaza la apertura de forma controlada
- Y registra el evento como fallback del modelo

#### Escenario: Modelo no disponible tras una frase no concluyente

- DADO que la politica hibrida no alcanza para decidir por si sola
- Y la consulta al modelo local falla o excede su timeout
- CUANDO el flujo aplica el fallback del modelo
- ENTONCES el sistema rechaza la apertura de forma controlada
- Y no abre solo por rostro conocido ni por habla no concluyente

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

#### Escenario: Apertura por voz clara, contexto residente y rostro autorizado dentro de tolerancia

- DADO que la voz contiene una solicitud clara de apertura, incluso si la transcripcion tiene errores menores
- Y la voz identifica un residente o una unidad que el sistema puede reclamar como contexto
- Y el rostro coincide con una persona habilitada vinculada a ese mismo contexto residente dentro de la tolerancia del motor facial
- CUANDO el flujo hibrido evalua la solicitud
- ENTONCES el sistema permite abrir el porton

#### Escenario: Apertura de residente conocido por rostro confiable

- DADO que la voz contiene una solicitud clara de apertura
- Y el rostro coincide con una persona habilitada vinculada a un `resident_id`
- Y no existe contexto reclamado adicional en la voz
- CUANDO el flujo hibrido evalua la solicitud como residente conocido
- ENTONCES el sistema puede permitir abrir el porton

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

#### Escenario: Reintento facial ante una solicitud clara de apertura

- DADO que la voz contiene una solicitud clara de apertura
- Y el primer snapshot facial no logra una coincidencia confiable
- CUANDO el flujo hibrido realiza un reintento acotado de snapshot y matching
- ENTONCES el sistema usa el mejor resultado disponible antes de decidir

#### Escenario: Cara no detectable por luz o posicion

- DADO que la voz contiene una solicitud clara de apertura
- Y el sistema no logra extraer una cara usable del snapshot
- CUANDO falla el matching facial incluso tras reintentos acotados
- ENTONCES el sistema orienta al visitante a acercarse y mirar la camara antes de reintentar

#### Escenario: Interrupcion o falla del reconocimiento facial

- DADO que el flujo ya capturo audio y snapshot
- Y la invocacion del reconocimiento facial falla, excede su timeout o se interrumpe
- CUANDO el sistema intenta clasificar el rostro del visitante
- ENTONCES el flujo degrada de forma controlada a un resultado facial no disponible
- Y evita terminar la llamada con traceback

#### Escenario: Interrupcion o falla del snapshot

- DADO que el flujo intenta capturar una imagen del VTO para reconocimiento facial
- Y la captura de snapshot falla, excede su timeout o se interrumpe
- CUANDO el sistema prepara la etapa facial de la llamada
- ENTONCES el flujo degrada de forma controlada a snapshot no disponible
- Y evita terminar la llamada con traceback

#### Escenario: Operacion nocturna con modo monocromo

- DADO que el acceso se usa de noche o con iluminacion IR
- Y el VTO entrega mejor consistencia facial en modo monocromo
- CUANDO el sistema opera con `Dia/Noche` configurado en `Black/White`
- ENTONCES el matching facial nocturno puede resultar mas estable que en modo automatico o color

#### Escenario: Coincidencia facial borderline

- DADO que la voz contiene una solicitud clara de apertura
- Y el rostro coincide pero queda apenas fuera de la tolerancia configurada
- CUANDO el flujo clasifica el resultado facial
- ENTONCES el sistema registra el caso como borderline
- Y no abre con ese resultado por si solo

#### Escenario: Residente conocido con rostro apenas fuera de tolerancia

- DADO que la voz contiene una solicitud clara de apertura
- Y el rostro corresponde a un residente conocido habilitado
- Y la distancia facial queda apenas fuera de tolerancia pero dentro de la banda borderline
- CUANDO el flujo hibrido evalua la solicitud sin contexto reclamado adicional
- ENTONCES el sistema puede permitir abrir como residente conocido borderline

#### Escenario: Residente conocido en banda extendida nocturna

- DADO que el acceso opera en condiciones nocturnas o monocromas del VTO
- Y el rostro corresponde a un residente conocido habilitado
- Y la distancia facial supera la banda borderline normal pero permanece dentro de una banda extendida acotada para residente conocido
- CUANDO la voz contiene una solicitud clara de apertura
- ENTONCES el sistema puede permitir abrir como residente conocido en banda extendida

### Requisito: Entregar retroalimentacion al visitante

El sistema DEBE proporcionar retroalimentacion audible o textual que describa el resultado de la solicitud de acceso.

#### Escenario: Saludo inicial antes de escuchar al visitante

- DADO que el visitante presiona el boton del citofono
- CUANDO Asterisk contesta la llamada entrante del VTO
- ENTONCES el sistema reproduce un saludo inicial corto
- Y solo despues comienza a esperar y grabar la respuesta del visitante

#### Escenario: Captura preferente de voz por RTSP del VTO

- DADO que el VTO puede entregar audio confiable por RTSP aunque su uplink SIP no sea util
- CUANDO el flujo Asterisk deriva la llamada al procesamiento de VIGILIA
- ENTONCES el sistema prefiere capturar un clip de voz desde RTSP del VTO
- Y usa el audio SIP grabado solo como fallback si la captura RTSP falla o queda vacia

#### Escenario: Refuerzo de audio bajo antes de transcribir

- DADO que el clip de voz capturado existe pero llega con volumen bajo
- CUANDO el sistema prepara el audio para la transcripcion
- ENTONCES aplica un refuerzo acotado de volumen antes de enviarlo al motor de voz

#### Escenario: Acceso concedido

- DADO que se toma una decision positiva de acceso
- CUANDO se dispara el comando de apertura del porton
- ENTONCES el visitante recibe un mensaje indicando que el acceso fue concedido

#### Escenario: Acceso denegado

- DADO que la solicitud es denegada o no puede ser procesada
- CUANDO el flujo de decision termina
- ENTONCES el visitante recibe un mensaje indicando rechazo o falla temporal

#### Escenario: Reproduccion local de la respuesta en el host

- DADO que el flujo se ejecuta en un host local con reproduccion local habilitada
- Y el sistema logra sintetizar el audio de respuesta
- CUANDO termina de construir el WAV de salida
- ENTONCES el sistema reproduce esa respuesta por los parlantes del host
- Y mantiene el archivo listo para reutilizacion por Asterisk

#### Escenario: Falla la sintesis de voz

- DADO que el sistema debe reproducir una respuesta al visitante
- Y la sintesis de voz local o su conversion de audio falla
- CUANDO el flujo intenta construir el audio de respuesta
- ENTONCES el sistema genera una salida silenciosa de respaldo
- Y evita terminar la llamada con traceback
