# Delta de face-recognition

## Requisitos Agregados

### Requisito: Persistir identidades autorizadas para reconocimiento facial

El proyecto DEBE poder registrar personas autorizadas para futuras comparaciones faciales.

#### Escenario: Alta de persona autorizada

- DADO que una persona administradora quiere registrar una identidad
- CUANDO ingresa nombre y una imagen de referencia o embedding disponible
- ENTONCES el proyecto guarda la identidad en la base local

### Requisito: Persistir observaciones faciales

El proyecto DEBE poder guardar observaciones de rostros detectados o preparados para matching futuro.

#### Escenario: Observacion facial registrada

- DADO que existe una captura del VTO o una imagen procesada
- CUANDO el sistema registra una observacion facial
- ENTONCES guarda la observacion en la base local con su referencia de imagen y datos asociados
