import cv2
import json
import os
import sys
import numpy as np

# --- CONFIGURACIÓN ---
VIDEO_NAME = "media/rasputin.mp4"
JSON_NAME = "coreos/rasputin.json"
ASSETS_DIR = "../assets"

# --- MAPA DEL ESQUELETO (Conexiones) ---
# Pares de puntos que forman los huesos (Indices estándar de COCO/YOLO)
ESQUELETO = [
    (5, 7), (7, 9),       # Brazo Izquierdo
    (6, 8), (8, 10),      # Brazo Derecho
    (11, 13), (13, 15),   # Pierna Izquierda
    (12, 14), (14, 16),   # Pierna Derecha
    (5, 6),               # Hombros
    (11, 12),             # Caderas
    (5, 11), (6, 12),     # Torso
]

def ver_coreografia():
    # 1. Rutas
    base_dir = os.path.dirname(__file__)
    ruta_video = os.path.join(base_dir, ASSETS_DIR, VIDEO_NAME)
    ruta_json = os.path.join(base_dir, ASSETS_DIR, JSON_NAME)

    # 2. Cargar JSON
    if not os.path.exists(ruta_json):
        print("❌ No encuentro el archivo JSON. Ejecuta primero 'creador_coreografias.py'")
        return

    print("📂 Cargando datos de coreografía...")
    with open(ruta_json, 'r') as f:
        coreo = json.load(f)
    
    frames_data = coreo["frames"]
    fps_json = coreo["meta"]["fps"]

    # 3. Cargar Video
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        print("❌ No se puede abrir el video.")
        return

    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print("▶️ Reproduciendo... Pulsa 'Q' para salir.")

    frame_idx = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # Si tenemos datos para este frame
        if frame_idx < len(frames_data):
            puntos = frames_data[frame_idx]
            
            if puntos:
                # Dibujar Esqueleto
                # Convertimos las coordenadas normalizadas (0.0-1.0) a píxeles reales
                coords_px = []
                for p in puntos:
                    x, y, conf = p
                    px, py = int(x * W), int(y * H)
                    coords_px.append((px, py))

                # 1. Dibujar Huesos (Líneas)
                for i_a, i_b in ESQUELETO:
                    # Chequeamos que existan y tengan confianza > 0.5
                    if puntos[i_a][2] > 0.5 and puntos[i_b][2] > 0.5:
                        pt_a = coords_px[i_a]
                        pt_b = coords_px[i_b]
                        cv2.line(frame, pt_a, pt_b, (255, 0, 255), 4) # Rosa Neón

                # 2. Dibujar Articulaciones (Círculos)
                for i, (px, py) in enumerate(coords_px):
                    conf = puntos[i][2]
                    if conf > 0.5:
                        cv2.circle(frame, (px, py), 6, (0, 255, 0), -1) # Verde

        # Mostrar info frame
        cv2.putText(frame, f"Frame: {frame_idx}", (20, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

        cv2.imshow("VISOR DE DEBUG - COREOGRAFIA", frame)

        # Control de velocidad (esperar según FPS)
        delay = int(1000 / fps_json)
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ver_coreografia()