from ultralytics import YOLO
from config import MODEL_YOLO_PATH


class DetectorPose:
    def __init__(self):
        print("🧠 Cargando modelo YOLO-Pose...")
        # Usamos 'yolov8n-pose.pt' (Nano) para que vaya rápido en CPU
        # Se descargará solo la primera vez
        self.model = YOLO(MODEL_YOLO_PATH)
        print("✅ Modelo cargado.")

    def procesar_frame(self, frame, limite_personas=1):
        """
        Detecta personas con un límite dinámico.
        """
        # Pasamos el número de jugadores a max_det
        results = self.model(frame, verbose=False, conf=0.5, max_det=limite_personas)
        
        # Pintamos los esqueletos encontrados
        annotated_frame = results[0].plot()
        
        return annotated_frame