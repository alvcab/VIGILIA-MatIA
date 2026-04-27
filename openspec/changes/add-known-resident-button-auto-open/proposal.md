# Propuesta: Autoapertura por boton para residente conocido

## Por Que

El flujo actual ya puede abrir para residentes conocidos cuando existe una solicitud de apertura por voz y el rostro coincide.
Para el uso diario del condominio, el caso mas natural del residente es simplemente presionar el boton del VTO, escuchar el saludo y esperar que el sistema reconozca su cara sin exigir una frase adicional.

## Que Cambia

- Permitir autoapertura cuando el VTO recibe una llamada desde el boton y el sistema detecta un rostro confiable de un residente conocido habilitado
- Permitir el mismo comportamiento cuando el audio resultante esta vacio o contiene solo un saludo corto
- Registrar estos eventos con una razon explicita de autoapertura por residente conocido

## No Objetivos

- Abrir para rostros borderline o extendidos sin voz
- Eliminar las verificaciones faciales existentes
- Habilitar apertura silenciosa para visitantes no vinculados a un residente conocido
