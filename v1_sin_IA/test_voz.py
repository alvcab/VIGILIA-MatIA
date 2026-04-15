import whisper
import os

print("Cargando modelo... (esto puede tardar la primera vez)")
model = whisper.load_model("tiny") # Usamos el 'tiny' por velocidad
print("Modelo cargado.")

# Aquí puedes poner la ruta de cualquier audio .wav que tengas, 
# o simplemente deja que el script falle después de cargar el modelo 
# para confirmar que las librerías están OK.
