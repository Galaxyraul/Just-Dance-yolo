
import pygame
import cv2
import time
import numpy as np
from moviepy.video.io.VideoFileClip import VideoFileClip
import os

from src.utils import es_parecido
from config import *
from src.detector import DetectorPose


class GameEngine:
    def __init__(self, screen, cancion_data, sistema_voz):
        print("🔧 [JUEGO] Inicializando MotorJuego...")
        self.screen = screen
        self.cancion_data = cancion_data
        self.voz = sistema_voz
        self.running = True
        self.pausa = False
        self.clock = pygame.time.Clock()
        
        # 1. CÁMARA
        print("📷 [JUEGO] Abriendo cámara (índice 0)...")
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("⚠️ [JUEGO] ¡AVISO! No se pudo abrir la cámara.")
        else:
            print("✅ [JUEGO] Cámara abierta correctamente.")
        
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # 2. IA
        print("🧠 [JUEGO] Cargando DetectorPose...")
        self.detector = DetectorPose()
        
        # 3. VIDEO
        nombre_video = cancion_data.get('video', 'baile.mp4')
        ruta_video = os.path.join(ASSETS_DIR, nombre_video)
        print(f"🎬 [JUEGO] Buscando video en: {ruta_video}")
        
        if os.path.exists(ruta_video):
            try:
                self.clip = VideoFileClip(ruta_video).resized(height=ALTO)
                print(f"✅ [JUEGO] Video cargado. Duración: {self.clip.duration} segundos.")
                # Audio logic
                try:
                    self.clip.audio.write_audiofile("temp_game.mp3", logger=None)
                    pygame.mixer.music.load("temp_game.mp3")
                    print("✅ [JUEGO] Audio extraído y cargado.")
                except Exception as e:
                    print(f"⚠️ [JUEGO] Fallo en audio: {e}")
            except Exception as e:
                print(f"❌ [JUEGO] Error cargando video clip: {e}")
                self.clip = None
        else:
            print("❌ [JUEGO] EL ARCHIVO DE VIDEO NO EXISTE.")
            self.clip = None

    def convertir_cv2_a_pygame(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = np.rot90(frame)
        return pygame.surfarray.make_surface(frame)

    def run(self):
        print("🚀 [JUEGO] Arrancando bucle principal (run)...")
        if pygame.mixer.music.get_busy():
             pygame.mixer.music.stop()
             
        # Solo reproducimos si hay audio cargado
        try:
            pygame.mixer.music.play()
            print("🎵 [JUEGO] Música play.")
        except:
            print("⚠️ [JUEGO] No hay música para reproducir.")

        self.start_time = time.time()
        tiempo_pausado_total = 0 
        inicio_pausa = 0

        # --- BUCLE ---
        while self.running:
            # Check de seguridad de eventos
            pygame.event.pump()
            
            # 1. VOZ
            try:
                comando = self.voz.obtener_comando()
                if comando:
                    print(f"🎤 [JUEGO] Comando recibido: '{comando}'")
                    if es_parecido(comando, "salir"):
                        print("🛑 [JUEGO] Saliendo por comando de voz.")
                        self.running = False
            except Exception as e:
                print(f"⚠️ [JUEGO] Error voz: {e}")

            # 2. TECLADO / SALIDA
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    print("🛑 [JUEGO] Saliendo por QUIT (X ventana).")
                    self.running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    print("🛑 [JUEGO] Saliendo por ESCAPE.")
                    self.running = False

            # 3. TIEMPO Y FINALIZACIÓN
            tiempo_actual = (time.time() - self.start_time) - tiempo_pausado_total
            
            if self.clip:
                # DEBUG DEL TIEMPO (Imprimimos cada segundo para no saturar)
                if int(tiempo_actual) % 2 == 0 and int(tiempo_actual * 100) % 5 == 0:
                     # print(f"⏱️ Tiempo: {tiempo_actual:.2f} / {self.clip.duration}")
                     pass

                if tiempo_actual >= self.clip.duration:
                    print("🏁 [JUEGO] El video ha terminado. Cerrando juego.")
                    self.running = False
            else:
                # Si no hay video, salimos inmediatamente para evitar pantalla negra eterna
                # print("⚠️ [JUEGO] No hay video cargado, cerrando.")
                # self.running = False 
                pass # Comenta las dos líneas de arriba si quieres probar solo la cámara

            # 4. RENDER (Simplificado para debug)
            self.screen.fill((0,0,0))
            
            # Cámara
            ret, frame = self.cap.read()
            if ret:
                frame_pintado = self.detector.procesar_frame(frame) # YOLO
                surf = self.convertir_cv2_a_pygame(frame_pintado)
                surf = pygame.transform.scale(surf, (ANCHO//2, ALTO))
                self.screen.blit(surf, (ANCHO//2, 0))
            
            # Video
            if self.clip:
                try:
                    frame_vid = self.clip.get_frame(tiempo_actual)
                    surf_vid = pygame.surfarray.make_surface(frame_vid.swapaxes(0,1))
                    surf_vid = pygame.transform.scale(surf_vid, (ANCHO//2, ALTO))
                    self.screen.blit(surf_vid, (0,0))
                except: pass

            pygame.display.flip()
            self.clock.tick(30)

        # FIN
        print("👋 [JUEGO] Saliendo de MotorJuego.run()")
        self.cap.release()

# ==========================================
# ZONA DE PRUEBAS (UNIT TESTING)
# ==========================================
if __name__ == "__main__":
    print("🧪 INICIANDO MODO PRUEBA DE JUEGO AISLADO")
    
    # 1. Configuración Dummy (Falsa)
    pygame.init()
    
    # Forzamos una resolución estándar para la prueba
    TEST_W, TEST_H = 1280, 720
    screen = pygame.display.set_mode((TEST_W, TEST_H))
    pygame.display.set_caption("PRUEBA UNITARIA - MOTOR JUEGO")
    
    # IMPORTANTE: Sobrescribimos las globales de config para esta prueba
    ANCHO = TEST_W
    ALTO = TEST_H
    
    # 2. Mock de Voz (Una clase falsa que no hace nada para que no moleste)
    class VozFalsa:
        def obtener_comando(self):
            return None # Nunca dice nada
            
    voz_dummy = VozFalsa()
    
    # 3. Datos de canción falsa
    # ¡ASEGÚRATE DE QUE ESTE VIDEO EXISTA EN TU CARPETA ASSETS!
    cancion_test = {
        "titulo": "CANCION DE PRUEBA",
        "video": "media/baile.mp4", # <--- CAMBIA ESTO SI TU VIDEO SE LLAMA DISTINTO
        "artista": "Tester"
    }
    
    # 4. Lanzamiento
    try:
        print("⚡ Instanciando MotorJuego...")
        # Pasamos la pantalla, la canción falsa y la voz falsa
        juego = GameEngine(screen, cancion_test, voz_dummy)
        
        print("⚡ Ejecutando run()...")
        juego.run()
        
    except Exception as e:
        print("\n❌ CRASH EN PRUEBA:")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🧪 Prueba terminada.")
        pygame.quit()