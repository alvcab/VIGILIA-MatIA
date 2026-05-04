## MODIFIED Requirements

### Requisito: Restringir la apertura del porton a decisiones positivas

#### Escenario: Apertura inmediata por rostro confiable al presionar el boton del VTO

- DADO que un residente conocido presiona el boton del VTO
- Y el sistema puede capturar uno o mas snapshots antes de iniciar la escucha larga
- CUANDO el rostro coincide de forma confiable o dentro de una banda extendida acotada para un residente conocido habilitado
- ENTONCES el sistema abre de inmediato
- Y termina la llamada sin exigir frase adicional

#### Escenario: Continuacion al flujo de voz cuando no hay match facial confiable

- DADO que entra una llamada del VTO
- Y la verificacion facial rapida inicial no logra un match confiable habilitado
- CUANDO la llamada continua
- ENTONCES el sistema pasa al flujo normal de escucha
- Y espera que el visitante diga a que residente o departamento viene
