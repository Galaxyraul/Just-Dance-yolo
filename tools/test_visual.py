import cv2
import json
import os
import sys
import numpy as np
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.puntuacion import SistemaPuntuacion

NOMBRE_ARCHIVO = "rasputin" 
EXTENSION_VIDEO = ".mp4"

# Nombres de carpetas (Ajusta si tus carpetas se llaman distinto)
DIR_ASSETS = "assets"
DIR_MEDIA = "media"   # Donde están los videos
DIR_COREOS = "coreos" # Donde están los json

UMBRAL_CONFIANZA = 0.65 
INTERVALO = 20


ESQUELETO_CONNECTIONS = [
    (5, 7), (7, 9), (6, 8), (8, 10), (11, 13), (13, 15),
    (12, 14), (14, 16), (5, 6), (11, 12), (5, 11), (6, 12)
]

def ejecutar_test_scoring():
    ruta_script = os.path.abspath(__file__)
    dir_tools = os.path.dirname(ruta_script)
    # Subimos un nivel para llegar a la raíz del proyecto (Practica Final)
    dir_raiz = os.path.dirname(dir_tools)
    
    # Construimos las rutas completas
    vid_path = os.path.join(dir_raiz, DIR_ASSETS, DIR_MEDIA, NOMBRE_ARCHIVO + EXTENSION_VIDEO)
    json_path = os.path.join(dir_raiz, DIR_ASSETS, DIR_COREOS, NOMBRE_ARCHIVO + ".json")

    # Limpiamos las barras para que Windows no se queje
    vid_path = os.path.normpath(vid_path)
    json_path = os.path.normpath(json_path)

    print("🔍 DIAGNÓSTICO DE RUTAS:")
    print(f"   📂 Raíz del proyecto: {dir_raiz}")
    print(f"   🎬 Buscando video en: {vid_path}")
    print(f"   📊 Buscando JSON en:  {json_path}")

    # 2. VERIFICACIÓN ANTES DE CARGAR
    if not os.path.exists(json_path):
        print("\n❌ ERROR CRÍTICO: Python dice que el archivo NO existe.")
        print("   -> Comprueba que la carpeta 'coreos' está dentro de 'assets'")
        print("   -> Comprueba que el archivo se llama 'rasputin.json' y no 'rasputin.json.json'")
        return

    # ... (Resto del código: cargar scorer, cargar video, bucle while...)
    print("✅ Archivo encontrado. Iniciando motor...")
    scorer = SistemaPuntuacion(json_path)
    
    cap = cv2.VideoCapture(vid_path)

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(json_path)
    with open(json_path, 'r') as f:
        json_data = json.load(f)["frames"]

    print(f"▶️ Testeando cada {INTERVALO} frames.")

    frame_idx = 0
    
    # Variables para mantener el texto en pantalla entre evaluaciones
    ultimo_mensaje = "..."
    ultimo_color = (100, 100, 100)
    conf_promedio = 0

    while True:
        ret, frame = cap.read()
        if not ret: break

        tiempo_actual = frame_idx / fps
        user_kpts_simulado = None
        
        # 1. Obtenemos datos del frame actual (para pintar el esqueleto siempre)
        if frame_idx < len(json_data):
            raw_points = json_data[frame_idx]
            if raw_points:
                user_kpts_simulado = np.array(raw_points)

        # 2. EVALUAR SOLO CADA 'X' FRAMES (Simulando el juego)
        if frame_idx % INTERVALO == 0:
            if user_kpts_simulado is not None:
                puntos_ganados, mensaje = scorer.evaluar(tiempo_actual, user_kpts_simulado)
                
                # Actualizamos el mensaje visual solo ahora
                if mensaje: 
                    ultimo_mensaje = mensaje
                    if mensaje == "PERFECTO": ultimo_color = (0, 255, 255)
                    elif mensaje == "BIEN": ultimo_color = (0, 255, 0)
                    elif mensaje == "MISS": ultimo_color = (0, 0, 255)
                else:
                    ultimo_mensaje = "..."
                    ultimo_color = (100, 100, 100)

                # Actualizamos la confianza promedio para mostrarla
                conf_promedio = np.mean([p[2] for p in user_kpts_simulado if p[2] > 0])

        # 3. DIBUJADO (Siempre, para ver el video fluido)
        if user_kpts_simulado is not None:
            px_points = []
            for p in user_kpts_simulado:
                px_points.append((int(p[0]*width), int(p[1]*height), p[2]))

            for a, b in ESQUELETO_CONNECTIONS:
                if a < len(px_points) and b < len(px_points):
                    if px_points[a][2] > UMBRAL_CONFIANZA and px_points[b][2] > UMBRAL_CONFIANZA:
                        cv2.line(frame, px_points[a][:2], px_points[b][:2], (0, 255, 0), 2)
                    else:
                        cv2.line(frame, px_points[a][:2], px_points[b][:2], (0, 0, 255), 1)

        # HUD
        cv2.rectangle(frame, (0,0), (400, 120), (0,0,0), -1)
        cv2.putText(frame, f"SCORE: {scorer.puntuacion_total}", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Usamos 'ultimo_mensaje' para que no parpadee
        cv2.putText(frame, f"EVAL: {ultimo_mensaje}", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, ultimo_color, 2)

        txt_conf = f"Calidad: {conf_promedio:.2f} | Frame: {frame_idx}"
        cv2.putText(frame, txt_conf, (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

        cv2.imshow("TEST DE SCORING", frame)
        
        if cv2.waitKey(int(1000/fps)) & 0xFF == ord('q'):
            break
            
        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ejecutar_test_scoring()