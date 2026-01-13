import cv2
import json
import os
import sys
from ultralytics import YOLO

# Ajustes
VIDEO_NAME = "media/begging.mp4" # El nombre del video en tu carpeta assets
OUTPUT_NAME = "coreos/begging.json" # Como se llamará el archivo de coreografía
ASSETS_DIR = "../assets"   # Ruta relativa a la carpeta assets

def extraer_coreografia():
    # 1. Rutas
    ruta_video = os.path.join(os.path.dirname(__file__), ASSETS_DIR, VIDEO_NAME)
    ruta_salida = os.path.join(os.path.dirname(__file__), ASSETS_DIR, OUTPUT_NAME)

    if not os.path.exists(ruta_video):
        print(f"❌ Error: No encuentro el video en {ruta_video}")
        return

    # 2. Cargar Modelo (Usamos el Nano, o el Medium 'yolov8m-pose.pt' si quieres más precisión para el mapa)
    print("🧠 Cargando IA...")
    model = YOLO('assets/models/yolo/yolov8l-pose.pt') 
    model.cuda()
    # 3. Leer Video
    cap = cv2.VideoCapture(ruta_video)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"🎬 Procesando: {VIDEO_NAME}")
    print(f"📊 Info: {width}x{height} a {fps} FPS. Total frames: {total_frames}")

    # Estructura de datos
    data_coreo = {
        "meta": {
            "fps": fps,
            "resolution": [width, height],
            "total_frames": total_frames,
            "version": "1.0"
        },
        "frames": [] # Aquí guardaremos los esqueletos
    }

    frame_idx = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # Detectar (Solo 1 persona, el "Profesor")
        results = model(frame, verbose=False, max_det=1)
        
        # Extraer keypoints
        # result.keypoints.xyn da coordenadas normalizadas (0 a 1)
        # result.keypoints.conf da la confianza
        
        frame_data = None
        
        if len(results[0].keypoints) > 0:
            # Obtenemos los keypoints de la primera persona
            # Convertimos a lista de Python para que sea compatible con JSON
            kpts = results[0].keypoints.xyn[0].tolist() 
            confs = results[0].keypoints.conf[0].tolist() if results[0].keypoints.conf is not None else []
            
            # Formato compacto: Lista de [x, y, conf] para cada punto (nariz, hombros, etc)
            puntos_compactos = []
            for i in range(len(kpts)):
                x, y = kpts[i]
                c = confs[i] if i < len(confs) else 0.0
                # Redondeamos a 4 decimales para ahorrar espacio (0.1234 es suficiente precisión)
                puntos_compactos.append([round(x, 4), round(y, 4), round(c, 2)])
            
            frame_data = puntos_compactos

        # Guardamos (si no detecta a nadie, guardamos None para mantener el tiempo)
        data_coreo["frames"].append(frame_data)

        # Barra de progreso simple
        if frame_idx % 50 == 0:
            progreso = (frame_idx / total_frames) * 100
            print(f"⏳ Progreso: {progreso:.1f}% ({frame_idx}/{total_frames})")
        
        frame_idx += 1

    cap.release()

    # 4. Guardar JSON
    print(f"💾 Guardando coreografía en {OUTPUT_NAME}...")
    with open(ruta_salida, 'w') as f:
        json.dump(data_coreo, f) # No usamos indent para que ocupe menos espacio
    
    print("✅ ¡Terminado! Archivo generado con éxito.")

if __name__ == "__main__":
    extraer_coreografia()