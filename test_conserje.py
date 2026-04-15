import os
import subprocess
import time

# --- CONFIGURACIÓN ---
VTO_IP = "192.168.100.108"
VTO_USER = "admin"
VTO_PASS = "Splitreset6901"

def abrir_y_hablar():
    inicio = time.time()
    
    # 1. DISPARO DEL PORTÓN (Fondo)
    comando_vto = f'curl -s --digest -u {VTO_USER}:{VTO_PASS} "http://{VTO_IP}/cgi-bin/accessControl.cgi?action=openDoor&channel=1" &'
    os.system(comando_vto)
    
    # 2. AUDIO INSTANTÁNEO (Sin esperar a la IA)
    # Mandamos el audio al fondo también para que el script quede listo de inmediato
    mensaje = "Abriendo portón."
    print(f">>> [ACCION] {mensaje}")
    os.system(f'espeak-ng -v es -s 160 "{mensaje}" &')
    
    fin = time.time()
    print(f"Tiempo de ejecución interna: {round(fin - inicio, 4)}s")

if __name__ == "__main__":
    print("--- VIGILIA: MODO RESPUESTA INSTANTÁNEA ---")
    print("Presiona ENTER para abrir (Ctrl+C para salir)")
    
    try:
        while True:
            input("\n[LISTO] Esperando visitante...")
            abrir_y_hablar()
    except KeyboardInterrupt:
        print("\nApagando...")
