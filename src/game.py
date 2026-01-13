import pygame
import cv2
import time
import numpy as np
import os
import sys

# --- CONFIGURACIÓN ---
try:
    import config 
    from src.utils import es_parecido
except ImportError:
    class config:
        ASSETS_DIR = "assets"
        FONDO = (0, 0, 0)
        NEON_VERDE = (0, 255, 0)
        NEON_AZUL = (0, 0, 255)
        NEON_ROSA = (255, 0, 255)
        NEON_AMARILLO = (255, 255, 0) # Nuevo color para Rank S
    def es_parecido(a, b): return a in b

# --- IMPORTS ---
try:
    from src.detector import DetectorPose
    from moviepy.video.io.VideoFileClip import VideoFileClip
except Exception as e:
    print(f"❌ [JUEGO] Error librerías: {e}")

try:
    from src.puntuacion import SistemaPuntuacion
except ImportError:
    class SistemaPuntuacion:
        def __init__(self, r): self.puntuacion_total=0; self.mensaje_actual=""; self.racha=0; self.color_mensaje=(255,255,255)
        def evaluar(self, t, k): return 0, ""
        def obtener_esqueleto_actual(self, t): return None

# --- MAPA DE HUESOS (VISUAL) ---
CONNECTIONS = [
    (5, 7), (7, 9), (6, 8), (8, 10), (11, 13), (13, 15),
    (12, 14), (14, 16), (5, 6), (11, 12), (5, 11), (6, 12)
]

class MotorJuego:
    # MODIFICACIÓN 1: Añadidos parámetros modo_batalla e id_jugador
    def __init__(self, screen, cancion_data, sistema_voz=None, num_jugadores=1, modo_batalla=False, id_jugador=1):
        self.screen = screen
        self.W, self.H = self.screen.get_size()
        
        self.cancion_data = cancion_data
        self.voz = sistema_voz
        self.num_jugadores = num_jugadores
        self.modo_batalla = modo_batalla # Guardamos el modo
        self.id_jugador = id_jugador     # Guardamos quién juega
        
        self.clock = pygame.time.Clock()
        
        # CÁMARA
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # IA
        self.detector = None
        try: self.detector = DetectorPose()
        except: pass

        # VIDEO
        self.clip = None
        nombre_video = cancion_data.get('video')
        ruta_video = os.path.abspath(os.path.join(config.ASSETS_DIR, "media", os.path.basename(nombre_video)))
        
        if os.path.exists(ruta_video):
            try:
                self.clip = VideoFileClip(ruta_video)
                # Audio temporal
                try:
                    self.clip.audio.write_audiofile("temp_game.mp3", logger=None)
                except: pass
            except: self.clip = None

        # PUNTUACIÓN
        nombre_sin_ext = os.path.splitext(os.path.basename(nombre_video))[0]
        ruta_json = os.path.abspath(os.path.join(config.ASSETS_DIR, "coreos", nombre_sin_ext + ".json"))
        self.scorer_ref = SistemaPuntuacion(ruta_json) # Referencia para resetear

    def resetear_estado(self):
        """Reinicia variables para volver a jugar sin recargar todo"""
        self.start_time = time.time()
        self.pausa = False
        self.inicio_pausa_temp = 0
        self.tiempo_pausado_total = 0
        self.running = True
        
        # Reiniciar Puntuación (Truco: Reinstanciamos o limpiamos variables)
        self.scorer_ref.puntuacion_total = 0
        self.scorer_ref.racha = 0
        self.scorer_ref.mensaje_actual = ""
        self.frame_count = 0
        self.intervalo_puntuacion = 15
        
        # Reiniciar Música
        if self.clip:
            pygame.mixer.music.load("temp_game.mp3")
            pygame.mixer.music.play()

    def run(self):
        """Bucle Maestro: Jugar -> Resultados -> Jugar"""
        jugando_sesion = True
        nota_final = 0
        
        while jugando_sesion:
            self.resetear_estado()
            
            # --- 1. FASE DE JUEGO ---
            self.bucle_principal_juego()
            
            # Si el usuario cerró la ventana a la fuerza, salimos del todo
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

            nota_final = self.scorer_ref.puntuacion_total

            # --- 2. FASE DE RESULTADOS (LÓGICA SPLIT) ---
            
            # CASO A: MODO BATALLA (Devolvemos nota y salimos)
            if self.modo_batalla:
                self.mostrar_pantalla_final_batalla()
                jugando_sesion = False # Terminamos este turno
                
            # CASO B: MODO NORMAL (Bucle de repetir)
            else:
                accion = self.mostrar_pantalla_final()
                
                if accion == "menu":
                    jugando_sesion = False
                elif accion == "repetir":
                    pass # El bucle while se repite y llama a resetear_estado()
                elif accion == "salir":
                    return None

        # Limpieza final al salir al menú
        self.cap.release()
        try: pygame.mixer.music.stop()
        except: pass
        if self.clip: self.clip.close()
        
        return nota_final

    def bucle_principal_juego(self):
        """El bucle frame a frame del baile"""
        while self.running:
            # 1. COMANDOS DE VOZ
            comando = None
            if self.voz:
                try: comando = self.voz.obtener_comando()
                except: pass
            
            if comando:
                print(f"🎤 Comando en juego: {comando}")
                
                # Comandos Generales
                if es_parecido(comando, "salir") or es_parecido(comando, "terminar"):
                    self.running = False # Termina el baile y va a resultados
                elif es_parecido(comando, "pausa"): self.activar_pausa()
                elif es_parecido(comando, "continuar"): self.desactivar_pausa()
                
                # --- NUEVO: COMANDO PARA SALTAR TURNO (SOLO BATALLA) ---
                if self.modo_batalla:
                    if es_parecido(comando, "siguiente") or es_parecido(comando, "saltar") or es_parecido(comando, "pasa"):
                        print(f"⏭️ JUGADOR {self.id_jugador} SALTÓ SU TURNO")
                        self.running = False # Corta el bucle inmediatamente

            # 2. EVENTOS TECLADO
            for event in pygame.event.get():
                if event.type == pygame.QUIT: 
                    self.running = False
                    return # Salida forzada
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE: self.running = False
                    if event.key == pygame.K_SPACE:
                        if self.pausa: self.desactivar_pausa()
                        else: self.activar_pausa()
                    # Tecla rápida para saltar turno también (S)
                    if self.modo_batalla and event.key == pygame.K_s:
                        self.running = False

            # Resto del bucle (Pausa, Tiempo, Renderizado...) permanece igual
            if self.pausa:
                self.dibujar_pantalla_pausa()
                self.clock.tick(10)
                continue

            # TIEMPO
            tiempo_actual = (time.time() - self.start_time) - self.tiempo_pausado_total
            if self.clip and tiempo_actual >= self.clip.duration:
                self.running = False

            # RENDERIZADO (Copia exacta de tu lógica de renderizado anterior)
            self.screen.fill(config.FONDO)
            mitad_ancho = self.W // 2
            
            # ... (Toda la lógica de Cámara, Video, IA y UI que ya tienes) ...
            # ... Para no repetir todo el código de renderizado, mantén lo que tenías aquí ...
            
            # --- RENDERIZADO (Resumido para copiar/pegar si lo necesitas) ---
            # CAMARA
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                if self.detector:
                    try:
                        results = self.detector.model(frame, verbose=False, max_det=self.num_jugadores, device=0)
                        frame = results[0].plot()
                        self.frame_count += 1
                        if self.frame_count % self.intervalo_puntuacion == 0:
                            if len(results[0].keypoints) > 0:
                                kpts = results[0].keypoints.xyn[0]
                                confs = results[0].keypoints.conf[0].unsqueeze(1)
                                user_keypoints = np.concatenate((kpts.cpu(), confs.cpu()), axis=1)
                                self.scorer_ref.evaluar(tiempo_actual, user_keypoints)
                    except: pass
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = np.rot90(frame)
                surf_cam = pygame.surfarray.make_surface(frame)
                surf_cam = pygame.transform.scale(surf_cam, (mitad_ancho, self.H))
                self.screen.blit(surf_cam, (mitad_ancho, 0))

            # VIDEO
            if self.clip:
                try:
                    frame_vid = self.clip.get_frame(tiempo_actual)
                    surf_vid = pygame.surfarray.make_surface(frame_vid.swapaxes(0,1))
                    surf_vid = pygame.transform.scale(surf_vid, (mitad_ancho, self.H))
                    esqueleto_guia = self.scorer_ref.obtener_esqueleto_actual(tiempo_actual)
                    if esqueleto_guia: self.dibujar_esqueleto_pygame(surf_vid, esqueleto_guia, (mitad_ancho, self.H))
                    self.screen.blit(surf_vid, (0, 0))
                except: pass

            # UI
            pygame.draw.line(self.screen, config.NEON_AZUL, (mitad_ancho, 0), (mitad_ancho, self.H), 5)
            score_txt = pygame.font.SysFont("Arial Black", 50).render(f"{self.scorer_ref.puntuacion_total}", True, (255, 255, 255))
            self.screen.blit(score_txt, (self.W//2 - score_txt.get_width()//2, 20))

            if self.scorer_ref.mensaje_actual:
                fb_txt = pygame.font.SysFont("Arial Black", 60).render(self.scorer_ref.mensaje_actual, True, self.scorer_ref.color_mensaje)
                self.screen.blit(fb_txt, (int(self.W * 0.75) - fb_txt.get_width()//2, self.H - 150))
            
            if self.modo_batalla:
                 font = pygame.font.SysFont("Arial", 30)
                 txt_p = font.render(f"JUGADOR {self.id_jugador}", True, config.NEON_AMARILLO)
                 self.screen.blit(txt_p, (20, 20))

            pygame.display.flip()
            self.clock.tick(30)

    # --- PANTALLAS FINALES ---

    def mostrar_pantalla_final(self):
        """Bucle de la pantalla de puntuación final con corrección de capas (MODO NORMAL)"""
        pygame.mixer.music.stop()
        
        # Calcular Ranking
        puntos = self.scorer_ref.puntuacion_total
        rank = "C"
        color_rank = (200, 200, 200)
        comentario = "¡INTÉNTALO DE NUEVO!"

        if puntos > 5000: 
            rank = "S"
            color_rank = config.NEON_AMARILLO
            comentario = "¡ERES UNA LEYENDA!"
        elif puntos > 3000:
            rank = "A"
            color_rank = config.NEON_VERDE
            comentario = "¡INCREÍBLE!"
        elif puntos > 1000:
            rank = "B"
            color_rank = config.NEON_AZUL
            comentario = "¡BUEN TRABAJO!"

        # Overlay
        overlay = pygame.Surface((self.W, self.H))
        overlay.set_alpha(220)
        overlay.fill((0,0,0))
        
        esperando_decision = True
        
        # Fuentes
        font_title = pygame.font.SysFont("Arial Black", 50)
        font_rank = pygame.font.SysFont("Arial Black", 180) # Letra más grande
        font_score = pygame.font.SysFont("Arial Black", 60)
        font_com = pygame.font.SysFont("Arial", 40)
        font_inst = pygame.font.SysFont("Arial", 30)

        # Pre-renderizado de textos
        cx, cy = self.W // 2, self.H // 2
        
        txt_fin = font_title.render("BAILE TERMINADO", True, (255, 255, 255))
        txt_rank = font_rank.render(rank, True, color_rank)
        txt_pts = font_score.render(f"PUNTUACIÓN: {puntos}", True, config.NEON_ROSA)
        txt_com = font_com.render(comentario, True, (255,255,255))
        txt_inst = font_inst.render("🎤 Di 'REPETIR' o 'MENÚ'", True, (150, 150, 150))

        while esperando_decision:
            # 1. DIBUJAR CAPAS (Orden Importante: De atrás hacia adelante)
            
            # Capa 0: Fondo (Juego congelado + Oscuridad)
            self.screen.blit(overlay, (0,0))
            
            # Capa 1: Título (Arriba del todo)
            self.screen.blit(txt_fin, (cx - txt_fin.get_width()//2, 40))
            
            # Capa 2: La Letra del Rank (Al Fondo, en el centro)
            # La subimos un poco (cy - 60) para dejar sitio al número abajo
            self.screen.blit(txt_rank, (cx - txt_rank.get_width()//2, cy - 250))
            
            # Capa 3: La Puntuación (ENCIMA de la letra o justo debajo)
            # La dibujamos DESPUÉS del rank para que si se tocan, el número se vea encima
            self.screen.blit(txt_pts, (cx - txt_pts.get_width()//2, cy + 60))
            
            # Capa 4: Comentario y Ayuda (Abajo)
            self.screen.blit(txt_com, (cx - txt_com.get_width()//2, cy + 230))
            self.screen.blit(txt_inst, (cx - txt_inst.get_width()//2, self.H - 60))
            
            pygame.display.flip()
            
            # 2. LOGICA DE VOZ Y TECLADO
            comando = None
            if self.voz:
                try: comando = self.voz.obtener_comando()
                except: pass
                
            if comando:
                if any(x in comando for x in ["repetir", "otra", "nuevo"]): return "repetir"
                if any(x in comando for x in ["menú", "salir", "inicio", "volver"]): return "menu"

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "salir"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r: return "repetir"
                    if event.key == pygame.K_m or event.key == pygame.K_SPACE: return "menu"
            
            self.clock.tick(15)
            
        return "menu"
    
    def mostrar_pantalla_final_batalla(self):
        """Pantalla simplificada para transición de batalla (MODO BATALLA)"""
        pygame.mixer.music.stop()
        
        start = time.time()
        font_big = pygame.font.SysFont("Arial Black", 50)
        font_med = pygame.font.SysFont("Arial", 40)
        
        puntos = self.scorer_ref.puntuacion_total
        
        # Esperamos 5 segundos o comando de voz
        while time.time() - start < 5: 
            self.screen.fill((0,0,0))
            
            cx, cy = self.W // 2, self.H // 2
            
            txt_j = font_big.render(f"JUGADOR {self.id_jugador} TERMINADO", True, (255,255,255))
            txt_p = font_big.render(f"PUNTUACIÓN: {puntos}", True, config.NEON_ROSA)
            txt_i = font_med.render("Siguiente turno en breve...", True, (150,150,150))
            
            self.screen.blit(txt_j, (cx - txt_j.get_width()//2, cy - 80))
            self.screen.blit(txt_p, (cx - txt_p.get_width()//2, cy))
            self.screen.blit(txt_i, (cx - txt_i.get_width()//2, cy + 100))
            
            pygame.display.flip()
            
            # Permitir saltar con voz
            cmd = None
            if self.voz: 
                try: cmd = self.voz.obtener_comando()
                except: pass
            if cmd and (es_parecido(cmd, "siguiente") or es_parecido(cmd, "vale") or es_parecido(cmd, "ok")): 
                break

            for event in pygame.event.get(): 
                if event.type == pygame.QUIT: sys.exit()
            
            self.clock.tick(10)

    # --- AUXILIARES ---
    def dibujar_esqueleto_pygame(self, superficie, puntos_normalizados, tamano):
        W, H = tamano
        coords = []
        for p in puntos_normalizados:
            coords.append((int(p[0]*W), int(p[1]*H), p[2]))
            
        for a, b in CONNECTIONS:
            if a < len(coords) and b < len(coords):
                if coords[a][2] > 0.5 and coords[b][2] > 0.5:
                    pygame.draw.line(superficie, config.NEON_ROSA, coords[a][:2], coords[b][:2], 3)

    def activar_pausa(self):
        self.pausa = True
        pygame.mixer.music.pause()
        self.inicio_pausa_temp = time.time()

    def desactivar_pausa(self):
        self.pausa = False
        pygame.mixer.music.unpause()
        self.tiempo_pausado_total += (time.time() - self.inicio_pausa_temp)

    def dibujar_pantalla_pausa(self):
        overlay = pygame.Surface((self.W, self.H))
        overlay.set_alpha(100)
        overlay.fill((0,0,0))
        self.screen.blit(overlay, (0,0))
        txt = pygame.font.SysFont("Arial Black", 80).render("PAUSA", True, config.NEON_ROSA)
        self.screen.blit(txt, (self.W//2 - txt.get_width()//2, self.H//2 - 100))
        pygame.display.flip()