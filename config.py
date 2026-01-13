import os

# DIMENSIONES
ANCHO = 1280
ALTO = 720
FPS = 60

# RUTAS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODEL_YOLO_PATH = os.path.join(ASSETS_DIR,"models/yolo/yolov8l-pose.pt")
MODEL_VOSK_PATH = os.path.join(ASSETS_DIR, "models/voice/small")
JSON_PATH = os.path.join(ASSETS_DIR, "biblioteca.json")

# COLORES (R, G, B)
FONDO = (15, 15, 30)
NEON_AZUL = (0, 255, 255)
NEON_ROSA = (255, 0, 128)
NEON_VERDE = (50, 255, 50)
NEON_AMARILLO = (255, 255, 0)
BLANCO = (255, 255, 255)
GRIS_CLARO = (180, 180, 180)