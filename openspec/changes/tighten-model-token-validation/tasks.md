# Tareas

## 1. Endurecimiento del parser de decisiones

- [x] 1.1 Documentar el cambio en OpenSpec
- [x] 1.2 Aceptar solo tokens exactos del modelo en el pipeline principal
- [x] 1.3 Alinear el script legado `vigilia.py`
- [x] 1.4 Agregar una prueba automatizada para respuestas verbosas
- [x] 1.5 Endurecer prompt y `Modelfile` para respuestas de un solo token
- [x] 1.6 Tolerar solicitudes de apertura con errores menores de transcripcion usando la ruta hibrida
- [x] 1.7 Superponer transcripcion y rama snapshot-rostro para reducir latencia operativa
- [x] 1.8 Ejecutar reconocimiento facial inline para evitar el costo de subproceso y la advertencia OMP
- [x] 1.9 Reaislar el reconocimiento facial con timeout al detectar cuelgues en la ejecucion inline
- [x] 1.10 Cachear encodings de referencia por ruta y fecha de modificacion para evitar recomputo innecesario
- [x] 1.11 Reducir la resolucion usada para embeddings faciales manteniendo el snapshot completo para trazabilidad
- [x] 1.12 Agregar un servicio local persistente para transcripcion y reconocimiento facial con autoarranque desde `run_vigilia.sh`
- [x] 1.13 Limitar el servicio persistente a transcripcion al detectar timeouts en reconocimiento facial
- [x] 1.14 Simplificar el servicio persistente a Whisper-only con fallback rapido y sin health-check bloqueante
- [x] 1.15 Reintentar una vez el snapshot facial en solicitudes claras de apertura cuando el primer matching no es confiable
- [x] 1.16 Promover frases observadas en la base local y bandas faciales explicitas a la politica de decision
- [x] 1.17 Aprender automaticamente frases de acceso desde eventos exitosos repetidos
- [x] 1.18 Distinguir ausencia de cara detectable y responder con una guia operativa al visitante
