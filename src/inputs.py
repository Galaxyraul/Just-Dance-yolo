import threading
import json
import queue
import pyaudio
import os
import sys
from src.puntuacion import SistemaPuntuacion
from vosk import Model, KaldiRecognizer
from config import MODEL_VOSK_PATH

class SistemaVoz:
    def __init__(self):
        self.cola = queue.Queue()
        self.running = True
        self.disponible = False
        
        print("\n" + "="*30)
        print("🔍 DIAGNÓSTICO DE VOZ")
        print(f"📂 Ruta esperada del modelo: {MODEL_VOSK_PATH}")
        
        # 1. Chequeo de ruta
        if not os.path.exists(MODEL_VOSK_PATH):
            print("❌ ERROR CRÍTICO: No encuentro la carpeta del modelo.")
            print(f"   Asegúrate de que la carpeta 'model' está dentro de 'assets'.")
            print(f"   Estructura correcta: JustDanceAI -> assets -> model")
            print("="*30 + "\n")
            return

        print("✅ Carpeta encontrada. Cargando modelo (esto tarda un poco)...")

        # 2. Carga del Modelo
        try:
            self.model = Model(MODEL_VOSK_PATH)
            self.disponible = True
            print("✅ Modelo Vosk cargado correctamente en memoria.")
        except Exception as e:
            print(f"❌ ERROR Cargando Vosk: {e}")
            return
        
        # 3. Inicio del Hilo
        if self.disponible:
            print("🚀 Iniciando hilo de escucha...")
            self.thread = threading.Thread(target=self._escuchar, daemon=True)
            self.thread.start()
        print("="*30 + "\n")

    def _escuchar(self):
        try:
            # 4. Configuración de PyAudio
            p = pyaudio.PyAudio()
            
            # Listar micrófonos para debug
            info = p.get_host_api_info_by_index(0)
            numdevices = info.get('deviceCount')
            # Descomenta esto si quieres ver tus micros:
            # for i in range(numdevices):
            #     print(f"Micro {i}: {p.get_device_info_by_host_api_device_index(0, i).get('name')}")

            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
            stream.start_stream()
            
            rec = KaldiRecognizer(self.model, 16000)
            print("🎤 MICROFONO ABIERTO. Di 'Hola' o algo para probar.")
            
            while self.running:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    res = json.loads(rec.Result())
                    texto = res.get("text", "")
                    if texto:
                        print(f"🗣️ ESCUCHADO: '{texto}'") # Debug directo
                        self.cola.put(texto.lower())
                        
        except Exception as e:
            print(f"❌ ERROR EN BUCLE DE AUDIO: {e}")

    def obtener_comando(self):
        try:
            return self.cola.get_nowait()
        except queue.Empty:
            return None