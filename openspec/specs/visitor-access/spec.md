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

#### Escenario: Solicitud no orientada a apertura resuelta sin modelo

- DADO que la transcripcion contiene un saludo, una visita informativa o un contexto como paquete o departamento
- Y la voz no pide explicitamente abrir el porton
- CUANDO el flujo evalua la solicitud
- ENTONCES el sistema puede resolver la no-apertura mediante reglas locales
- Y no depende del token del modelo para responder de forma segura

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

#### Escenario: Token negativo exacto del modelo

- DADO que la respuesta del modelo es exactamente `HOLA` o exactamente `ERROR`
- CUANDO el flujo de manejo de comandos evalua la respuesta
- ENTONCES el sistema trata esa respuesta como una no-apertura valida
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

#### Escenario: Apertura inmediata por rostro confiable al presionar el boton del VTO

- DADO que un residente conocido presiona el boton del VTO
- Y el sistema puede capturar un snapshot antes de iniciar la escucha larga
- CUANDO el rostro coincide de forma confiable o dentro de una banda extendida acotada para un residente conocido habilitado
- ENTONCES el sistema abre de inmediato
- Y termina la llamada sin exigir frase adicional

#### Escenario: Continuacion al flujo de voz cuando no hay match facial confiable

- DADO que entra una llamada del VTO
- Y la verificacion facial rapida inicial no logra un match confiable habilitado
- CUANDO la llamada continua
- ENTONCES el sistema pasa al flujo normal de escucha
- Y espera que el visitante diga a que residente o departamento viene

#### Escenario: Snapshot rapido prioriza captura HTTP

- DADO que entra una llamada del VTO y el sistema necesita un snapshot rapido para rostro
- CUANDO el equipo soporta captura JPEG por HTTP autenticado
- ENTONCES el sistema puede intentar primero ese snapshot HTTP
- Y si falla, continua con captura RTSP sin abortar la llamada

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
- ENTONCES el sistema puede reproducir un saludo inicial corto
- Y si el VTO no reproduce el audio de retorno de forma confiable, el saludo puede salir por los parlantes locales del iMac para confirmar que el sistema esta escuchando

#### Escenario: Captura preferente de voz por RTSP del VTO

- DADO que el VTO puede entregar audio confiable por RTSP aunque su uplink SIP no sea util
- CUANDO el flujo Asterisk deriva la llamada al procesamiento de VIGILIA
- ENTONCES el sistema prefiere capturar un clip de voz desde RTSP del VTO
- Y usa el audio SIP grabado solo como fallback si la captura RTSP falla o queda vacia

#### Escenario: Captura inmediata de voz en el flujo real del VTO

- DADO que el VTO real no reproduce de forma confiable el audio entrante desde Asterisk
- CUANDO el sistema atiende una llamada real del VTO
- ENTONCES el flujo puede omitir el saludo y tono del PBX antes de grabar
- Y prioriza una ventana de escucha mas inmediata y mas larga para captar la voz del visitante

#### Escenario: Respuesta hablada local cuando el VTO no sirve como retorno

- DADO que el VTO real no reproduce de forma confiable el audio de respuesta enviado por SIP
- CUANDO el flujo decide informar rechazo, aclaracion o confirmacion al visitante
- ENTONCES el sistema puede reproducir esa respuesta por los parlantes locales del iMac
- Y no depende de `Playback(...)` hacia el VTO para completar el flujo audible

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

#### Escenario: Respuesta hablada generada por IA para una visita no autorizada

- DADO que el sistema ya decidio no abrir el porton
- Y existe una transcripcion util del visitante
- CUANDO el flujo genera la respuesta hablada
- ENTONCES el sistema puede usar un modelo local para redactar una frase breve en espanol
- Y esa respuesta no altera la decision de apertura

#### Escenario: Repartidor o paquete sin autorizacion de apertura

- DADO que el visitante indica que viene a dejar un paquete o encargo
- Y el sistema no ha decidido abrir el porton
- CUANDO genera la respuesta hablada al visitante
- ENTONCES la respuesta puede orientar a dejar el paquete en conserjeria
- Y el porton permanece cerrado

#### Escenario: Fallback de respuesta hablada cuando la IA falla

- DADO que el sistema ya decidio abrir o no abrir
- Y la generacion de respuesta hablada por IA falla, excede su timeout o devuelve una salida invalida
- CUANDO el flujo necesita hablarle al visitante
- ENTONCES el sistema usa una respuesta fija de respaldo
- Y mantiene la misma decision de acceso ya tomada

#### Escenario: Reproduccion local de la respuesta en el host

- DADO que el flujo se ejecuta en un host local con reproduccion local habilitada
- Y el sistema logra sintetizar el audio de respuesta
- CUANDO termina de construir el WAV de salida
- ENTONCES el sistema reproduce esa respuesta por los parlantes del host
- Y mantiene el archivo listo para reutilizacion por Asterisk

#### Escenario: Segundo turno local para aclarar residente o departamento

- DADO que el flujo corre localmente en el host
- Y el visitante entrega un saludo o una visita ambigua sin pedir apertura
- CUANDO el sistema necesita aclarar a que residente o departamento viene
- ENTONCES puede emitir una pregunta corta al visitante
- Y volver a capturar una segunda respuesta antes de cerrar la interaccion

#### Escenario: Falla la sintesis de voz

- DADO que el sistema debe reproducir una respuesta al visitante
- Y la sintesis de voz local o su conversion de audio falla
- CUANDO el flujo intenta construir el audio de respuesta
- ENTONCES el sistema genera una salida silenciosa de respaldo
- Y evita terminar la llamada con traceback
