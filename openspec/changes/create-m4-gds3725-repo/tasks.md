## 1. Traceability

- [x] Crear propuesta y diseno para el nuevo repo `vigilia-m4-gds3725`
- [x] Definir una spec inicial de arquitectura y modos de prueba

## 2. Scaffold

- [x] Crear la carpeta `vigilia-m4-gds3725/`
- [x] Agregar `README.md`, `pyproject.toml` y configuracion base
- [x] Agregar servicios minimos para decision, `dry-run` y TTS canned
- [x] Agregar scripts simples de prueba

## 3. Validation

- [x] Agregar tests minimos para la policy inicial
- [x] Verificar que el scaffold corra en modo `decision-only`
- [x] Ampliar la policy inicial para casos basicos de intercom en espanol
- [x] Agregar reglas de autorizacion por residente
- [x] Preparar contexto de segundo turno y capa base de prompts
- [x] Agregar historial de conversacion por sesion
- [x] Conectar `audio-file` a la capa hibrida end-to-end
- [x] Agregar backends configurables de transcripcion

## 4. No-Asterisk Interface

- [x] Agregar contratos iniciales de SIP/audio sin Asterisk
- [x] Agregar una ingesta local desde WAV para simular sesiones reales
- [x] Agregar un preview de endpoint SIP para planificar la integracion real con `GDS3725`
- [x] Agregar un contrato de transporte SIP y una implementacion fake para pruebas
- [x] Agregar un adaptador inicial de `baresip` para la ruta recomendada sin Asterisk
- [x] Agregar scaffold de runtime y scripts de `baresip`
- [x] Agregar inbox de `baresip` para procesar llamadas externas en el pipeline de IA
- [x] Agregar watcher de una pasada para procesar el inbox de `baresip`
- [x] Documentar a `MatIA` como agente conversacional principal sobre la base SIP/audio sin Asterisk
- [x] Agregar una interfaz Python interna por turno para que `MatIA` consulte la policy de VIGILIA
- [x] Agregar un atajo de apertura inmediata por rostro confiable para residentes conocidos
- [x] Agregar flujo de llamada al departamento con resultados `approved`, `denied` y `no_response`
- [x] Agregar fallback de visita registrada con codigo de 4 digitos cuando el departamento no responde
- [x] Agregar runtime `requests/responses/processed` para la respuesta del departamento por sesion
- [x] Agregar operaciones para listar solicitudes pendientes y responder una sesion de departamento
- [x] Agregar una interfaz Python directa para que `MatIA` entregue la respuesta del departamento sin pasar por CLI
- [x] Agregar una capa de perfil de voz de `MatIA` y un `call_plan_for_matia` para la llamada al departamento
- [x] Agregar un preview de llamada saliente por `baresip` usando el URI SIP del departamento
- [x] Agregar un preview operativo del ejecutor de llamada saliente por `baresip`
