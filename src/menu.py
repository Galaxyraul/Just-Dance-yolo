import threading
import pygame
import cv2  # <--- IMPORTANTE: Necesario para la cámara en el menú
import sys
import time
import os
import numpy as np
import config
from src.game import MotorJuego
from moviepy.video.io.VideoFileClip import VideoFileClip
from word2number_es import w2n
from config import *
from src.inputs import SistemaVoz
from src.data import GestorBiblioteca
from src.ui import Boton
from src.utils import es_parecido, normalizar_texto

class MenuPrincipal:
    def __init__(self):
        pygame.init()
        
        # 1. Iniciamos en Fullscreen nativo
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Just Dance AI - Fullscreen")
        
        # 2. Obtenemos la resolución real del monitor
        w_real, h_real = self.screen.get_size()
        
        # 3. ACTUALIZAMOS LA CONFIGURACIÓN GLOBAL
        config.ANCHO = w_real
        config.ALTO = h_real
        
        # 4. Sincronizamos variables locales
        global ANCHO, ALTO
        ANCHO = config.ANCHO
        ALTO = config.ALTO
        
        self.clock = pygame.time.Clock()
        
        # Fuentes
        t_big = 60 if ANCHO > 1500 else 40 
        self.font_big = pygame.font.SysFont("Arial Black", t_big)
        self.font_mid = pygame.font.SysFont("Arial", 25)
        self.font_small = pygame.font.SysFont("Consolas", 18)

        self.voz = SistemaVoz()
        self.biblio = GestorBiblioteca()
        
        self.estado = "MODOS" 
        self.datos_juego = {"modo": None, "jugadores": 1, "cancion": None}
        self.botones = []
        
        # RECURSOS PREVIEW
        self.clip = None 
        self.cap = None
        self.archivo_temp_actual = None
        
        self.crear_botones_modos()

    def ir_a_inicio(self):
        """Resetea todo y vuelve a la pantalla de selección de modo"""
        print("🏠 Volviendo al INICIO")
        self.limpiar_recursos_preview()
        
        # Reseteamos datos de la sesión actual
        self.datos_juego["modo"] = None
        self.datos_juego["cancion"] = None
        # (Opcional) self.datos_juego["jugadores"] = 1 
        
        self.estado = "MODOS"
        self.crear_botones_modos()

    def get_boton_volver(self):
        return Boton("VOLVER", 30, 30, 140, 50, GRIS_CLARO, "VOLVER")
    
    # --- GENERADORES DE UI ---
    def crear_botones_modos(self):
        btn_w = int(ANCHO * 0.35)
        btn_h = int(ALTO * 0.3)
        gap = int(ANCHO * 0.05)
        
        cx = ANCHO // 2
        cy = ALTO // 2
        y = cy - (btn_h // 2) - 40
        
        self.botones = [
            Boton("FIESTA", cx - btn_w - (gap//2), y, btn_w, btn_h, NEON_VERDE, "FIESTA"),
            Boton("BATALLA", cx + (gap//2), y, btn_w, btn_h, NEON_ROSA, "BATALLA"),
            Boton("AYUDA / TUTORIAL", cx - (btn_w//2), y + btn_h + 30, btn_w, 60, NEON_AZUL, "AYUDA")
        ]

    def crear_interfaz_ayuda(self):
        self.botones = [self.get_boton_volver()]

    def crear_botones_jugadores(self):
        self.botones = []
        self.botones.append(self.get_boton_volver())
        
        btn_w = int(ANCHO * 0.15)
        btn_h = int(ALTO * 0.15)
        gap_x = int(ANCHO * 0.03)
        gap_y = int(ALTO * 0.05)
        
        total_w = (btn_w * 3) + (gap_x * 2)
        start_x = (ANCHO // 2) - (total_w // 2)
        start_y = (ALTO // 2) - int(ALTO * 0.15) 

        for i in range(6):
            col = i % 3
            row = i // 3
            x = start_x + (col * (btn_w + gap_x))
            y = start_y + (row * (btn_h + gap_y))
            self.botones.append(Boton(f"{i+1} JUGADOR", x, y, btn_w, btn_h, NEON_AZUL, i+1))

    def crear_interfaz_canciones(self):
        self.botones = []
        # Botón Volver (Atrás un paso)
        self.botones.append(self.get_boton_volver())
        
        # --- NUEVO: Botón INICIO (Reset total) ---
        # Lo ponemos arriba a la derecha, al lado del Reset Filtros
        r_w = int(ANCHO * 0.15)
        self.botones.append(Boton("🏠 INICIO", ANCHO - r_w - 30, 90, r_w, 50, GRIS_CLARO, "HOME"))
        # -----------------------------------------

        jugadores = self.datos_juego["jugadores"]
        
        btn_w = int(ANCHO * 0.8)
        btn_h = int(ALTO * 0.12)
        gap = int(ALTO * 0.02)
        
        current_y = int(ALTO * 0.25)
        x_pos = (ANCHO // 2) - (btn_w // 2)
        
        # Mostramos las canciones filtradas
        for i, c in enumerate(self.biblio.canciones_visibles[:5]):
            cap = c.get('capacidad', 1)
            # Color verde si caben los jugadores, amarillo si no
            color = NEON_VERDE if cap >= jugadores else NEON_AMARILLO
            info = f"" if cap >= jugadores else f"[SOLO {cap}]"
            
            # Formato: "1. Rasputin [SOLO 1]"
            texto = f"{i+1}. {c['titulo']} {info}"
            
            self.botones.append(Boton(texto, x_pos, current_y, btn_w, btn_h, color, c))
            current_y += btn_h + gap
            
        # Botón Reset Filtros
        self.botones.append(Boton("RESET FILTROS", ANCHO - r_w - 30, 30, r_w, 50, NEON_ROSA, "RESET"))

    def limpiar_recursos_preview(self):
        """Cierra cámara, video y borra archivos temporales"""
        # 1. Parar música y liberar archivo
        pygame.mixer.music.stop()
        try:
            pygame.mixer.music.unload() # Solo funciona en Pygame 2.0+
        except: pass

        # 2. Cerrar Video y Cámara
        if self.clip: 
            self.clip.close()
            self.clip = None
        
        if self.cap: 
            self.cap.release()
            self.cap = None
            cv2.destroyAllWindows()
            
        # 3. Borrar el archivo mp3 temporal anterior del disco
        if self.archivo_temp_actual and os.path.exists(self.archivo_temp_actual):
            try:
                os.remove(self.archivo_temp_actual)
                print(f"🗑️ Archivo temporal borrado: {self.archivo_temp_actual}")
            except Exception as e:
                print(f"⚠️ No se pudo borrar temp: {e}")
            self.archivo_temp_actual = None

    def configurar_preview(self, cancion):
        # 1. Limpiar recursos anteriores
        self.limpiar_recursos_preview()

        self.datos_juego["cancion"] = cancion
        nombre_video = cancion.get('video')
        
        # Construimos ruta absoluta para evitar fallos
        ruta = os.path.abspath(os.path.join(config.ASSETS_DIR, nombre_video))
        
        # Calculamos altura: 50% de la pantalla
        altura_video = int(ALTO * 0.50)
        
        print(f"--------------------------------------------------")
        print(f"🔍 INTENTANDO CARGAR VIDEO PREVIEW:")
        print(f"   📂 Ruta: {ruta}")
        
        # A. Cargar Video
        if os.path.exists(ruta):
            try:
                # CORRECCIÓN: Usamos .resize() en lugar de .resized()
                # (MoviePy a veces falla con resized en versiones antiguas/nuevas)
                clip_original = VideoFileClip(ruta)
                self.clip = clip_original.resized(height=altura_video)
                
                print(f"   ✅ Video cargado en memoria. Duración: {self.clip.duration}s")
                
                # Intentamos cargar audio (si falla, no rompe el video)
                try:
                    self.clip.audio.write_audiofile("temp_preview.mp3", logger=None)
                    pygame.mixer.music.load("temp_preview.mp3")
                    pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_volume(0.5)
                except Exception as e_audio: 
                    print(f"   ⚠️ Alerta Audio: {e_audio}")
                
                self.start_time = time.time()
                
            except Exception as e:
                print(f"   ❌ ERROR CRÍTICO CARGANDO VIDEO: {e}")
                import traceback
                traceback.print_exc()
                self.clip = None
        else:
            print(f"   ❌ EL ARCHIVO DE VIDEO NO EXISTE EN LA RUTA INDICADA")
            self.clip = None

        print(f"--------------------------------------------------")

        # B. Iniciar Cámara
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        except:
            self.cap = None
        
        self.estado = "PREVIEW"
        
        # Botones
        y_botones = int(ALTO * 0.85)
        btn_w = int(ANCHO * 0.4)
        btn_h = int(ALTO * 0.1)
        cx = ANCHO // 2
        
        self.botones = [
            self.get_boton_volver(),
            Boton("CONFIRMAR (Di 'Empezar')", cx - (btn_w//2), y_botones, btn_w, btn_h, NEON_VERDE, "START")
        ]

    def lanzar_juego(self):
        # 1. ¡CRÍTICO! Liberar recursos del menú antes de abrir el juego
        self.limpiar_recursos_preview()
        
        with self.voz.cola.mutex:
            self.voz.cola.queue.clear()
        
        modo = self.datos_juego.get("modo", "FIESTA")
        jugadores = self.datos_juego["jugadores"]
        cancion = self.datos_juego["cancion"]

        try:
            if modo == "BATALLA":
                print(f"⚔️ MODO BATALLA: {jugadores} Jugadores")
                puntuaciones = []
                for i in range(jugadores):
                    self.mostrar_intersticio_turno(i + 1)
                    
                    juego = MotorJuego(self.screen, cancion, self.voz, 
                                     num_jugadores=1, modo_batalla=True, id_jugador=i+1)
                    puntos = juego.run()
                    
                    if puntos is None: return 
                    puntuaciones.append(puntos)
                    with self.voz.cola.mutex: self.voz.cola.queue.clear()
                
                self.mostrar_podio(puntuaciones)
            else:
                print(f"🎉 MODO FIESTA: {jugadores} Jugadores")
                juego = MotorJuego(self.screen, cancion, self.voz, 
                                 num_jugadores=jugadores, modo_batalla=False)
                juego.run()

        except Exception as e:
            print(f"❌ ERROR FATAL: {e}")
            import traceback
            traceback.print_exc()
        
        with self.voz.cola.mutex:
            self.voz.cola.queue.clear()
            
        print("🏁 Volviendo al menú...")
        self.estado = "CANCIONES"
        self.crear_interfaz_canciones()

    def mostrar_intersticio_turno(self, id_jugador):
        start = time.time()
        font_big = pygame.font.SysFont("Arial Black", 80)
        font_small = pygame.font.SysFont("Arial", 40)
        while time.time() - start < 3:
            self.screen.fill((0,0,0))
            txt1 = font_small.render("TURNO DE", True, (200, 200, 200))
            txt2 = font_big.render(f"JUGADOR {id_jugador}", True, NEON_ROSA)
            cx, cy = ANCHO // 2, ALTO // 2
            self.screen.blit(txt1, (cx - txt1.get_width()//2, cy - 80))
            self.screen.blit(txt2, (cx - txt2.get_width()//2, cy))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
            self.clock.tick(30)

    def dibujar_caja_ayuda(self, x, y, w, h, titulo, lineas, color_borde):
        """Dibuja un recuadro con título y lista de textos"""
        # 1. Fondo semitransparente
        s = pygame.Surface((w, h))
        s.set_alpha(50)
        s.fill(color_borde)
        self.screen.blit(s, (x, y))
        
        # 2. Borde Neón
        pygame.draw.rect(self.screen, color_borde, (x, y, w, h), 2)
        
        # 3. Título de la Sección
        tit = self.font_mid.render(titulo, True, color_borde)
        self.screen.blit(tit, (x + 20, y + 15))
        pygame.draw.line(self.screen, color_borde, (x+20, y+45), (x+w-20, y+45), 1)
        
        # 4. Líneas de texto
        font_info = pygame.font.SysFont("Arial", 20)
        start_text_y = y + 60
        for i, linea in enumerate(lineas):
            txt = font_info.render(f"• {linea}", True, (220, 220, 220))
            self.screen.blit(txt, (x + 25, start_text_y + (i * 30)))
            
    def mostrar_podio(self, puntuaciones):
        resultados = []
        for i, pts in enumerate(puntuaciones):
            resultados.append((f"JUGADOR {i+1}", pts))
        resultados.sort(key=lambda x: x[1], reverse=True)
        
        esperando = True
        font_title = pygame.font.SysFont("Arial Black", 60)
        font_list = pygame.font.SysFont("Arial", 40)
        
        while esperando:
            self.screen.fill((20, 20, 40))
            tit = font_title.render("¡ RESULTADOS !", True, NEON_AMARILLO)
            self.screen.blit(tit, (ANCHO//2 - tit.get_width()//2, 50))
            
            start_y = 180
            for i, (nombre, pts) in enumerate(resultados):
                color = NEON_VERDE if i == 0 else (200, 200, 200)
                prefix = f"{i+1}." 
                txt = f"{prefix} {nombre}:  {pts} pts"
                surf = font_list.render(txt, True, color)
                self.screen.blit(surf, (ANCHO//2 - surf.get_width()//2, start_y + i*60))

            inst = self.font_small.render("Di 'MENÚ' o pulsa ESC para salir", True, (150, 150, 150))
            self.screen.blit(inst, (ANCHO//2 - inst.get_width()//2, ALTO - 60))
            pygame.display.flip()
            
            cmd = self.voz.obtener_comando()
            if cmd and (es_parecido(cmd, "menu") or es_parecido(cmd, "salir")): esperando = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT: sys.exit()
                if event.type == pygame.KEYDOWN and (event.key == pygame.K_ESCAPE): esperando = False
            self.clock.tick(30)

    def procesar_voz(self, texto):
        print(f"🎤 Procesando: {texto}")
        texto_norm = normalizar_texto(texto)
        
        # --- COMANDOS GLOBALES DE VENTANA ---
        if "pantalla completa" in texto_norm: self.cambiar_pantalla("FULL"); return
        if "ventana" in texto_norm: self.cambiar_pantalla("WINDOW"); return

        # --- COMANDOS GLOBALES DE NAVEGACIÓN ---
        if es_parecido(texto, "salir") or es_parecido(texto, "cerrar"): 
            self.voz.running = False
            pygame.quit(); sys.exit()
        
        # NUEVO: Ir al Menú Principal directamente
        if "menu principal" in texto_norm or "al inicio" in texto_norm or "pantalla de titulo" in texto_norm:
            self.ir_a_inicio()
            return

        if es_parecido(texto, "volver") or es_parecido(texto, "atras"):
            self.ir_atras(); return

        # --- LÓGICA POR ESTADOS ---
        if self.estado == "MODOS":
            if es_parecido(texto, "fiesta"): self.set_modo("FIESTA")
            elif es_parecido(texto, "batalla"): self.set_modo("BATALLA")
            elif es_parecido(texto, "ayuda"): 
                self.estado = "AYUDA"
                self.crear_interfaz_ayuda()
            
        elif self.estado == "JUGADORES":
            nums = {"uno": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6}
            for k,v in nums.items():
                if es_parecido(texto, k): self.set_jugadores(v); return
            # Soporte para decir solo el número "1", "2"...
            for digit in ["1", "2", "3", "4", "5", "6"]:
                if digit in texto: self.set_jugadores(int(digit)); return

        elif self.estado == "CANCIONES":
            # 1. Filtros
            if es_parecido(texto, "reiniciar"):
                self.biblio.resetear_filtros()
                self.crear_interfaz_canciones(); return
            
            if "buscar" in texto_norm:
                partes = texto_norm.split("buscar")
                if len(partes) > 1 and partes[1].strip(): self.biblio.aplicar_filtro("BUSCAR", partes[1].strip())

            # 2. SELECCIÓN INTELIGENTE (NOMBRE, ALIAS O NÚMERO)
            
            # A) POR NOMBRE O ALIAS (Prioridad Alta)
            # Recorremos todas las canciones visibles
            if "seleccionar" in texto_norm or "pon" in texto_norm:
                for cancion in self.biblio.canciones_visibles:
                    # 1. Chequear Título exacto
                    titulo_norm = normalizar_texto(cancion["titulo"])
                    if titulo_norm in texto_norm:
                        print(f"🎵 Detectado por Título: {cancion['titulo']}")
                        self.configurar_preview(cancion)
                        return

                    # 2. Chequear Alias (NUEVO)
                    if "alias" in cancion:
                        for alias in cancion["alias"]:
                            alias_limpio = normalizar_texto(alias)
                            if alias_limpio in texto_norm:
                                print(f"🎵 Detectado por Alias '{alias}': {cancion['titulo']}")
                                self.configurar_preview(cancion)
                                return
            
            # Si cambiaron filtros o algo, refrescamos
            self.crear_interfaz_canciones()

        elif self.estado == "PREVIEW":
            if es_parecido(texto, "empezar") or es_parecido(texto, "confirmar") or es_parecido(texto, "dale"): 
                self.lanzar_juego()

    def set_modo(self, modo):
        self.datos_juego["modo"] = modo
        self.estado = "JUGADORES"
        self.crear_botones_jugadores()

    def set_jugadores(self, n):
        self.datos_juego["jugadores"] = n
        self.estado = "CANCIONES"
        self.crear_interfaz_canciones()

    def ir_atras(self):
        self.limpiar_recursos_preview() # Asegurar limpieza
        
        if self.estado == "PREVIEW":
            self.estado = "CANCIONES"
            self.crear_interfaz_canciones()
        elif self.estado == "CANCIONES":
            self.estado = "JUGADORES"
            self.crear_botones_jugadores()
        elif self.estado == "JUGADORES":
            self.estado = "MODOS"
            self.crear_botones_modos()
        elif self.estado == "AYUDA":
            self.estado = "MODOS"
            self.crear_botones_modos()

    def cambiar_pantalla(self, modo):
        global ANCHO, ALTO
        if modo == "FULL": self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else: self.screen = pygame.display.set_mode((1280, 720))
        
        w, h = self.screen.get_size()
        config.ANCHO, config.ALTO = w, h
        ANCHO, ALTO = w, h
        
        # Reconstruir UI según estado
        if self.estado == "MODOS": self.crear_botones_modos()
        elif self.estado == "JUGADORES": self.crear_botones_jugadores()
        elif self.estado == "CANCIONES": self.crear_interfaz_canciones()
        elif self.estado == "PREVIEW": 
            if self.datos_juego["cancion"]: self.configurar_preview(self.datos_juego["cancion"])
        elif self.estado == "AYUDA": self.crear_interfaz_ayuda()

    def run(self):
        while True:
            click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.procesar_voz("salir")
                if event.type == pygame.MOUSEBUTTONDOWN: click = True
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.procesar_voz("salir")
            
            cmd = self.voz.obtener_comando()
            if cmd: self.procesar_voz(cmd)
            
            mx, my = pygame.mouse.get_pos()
            accion = None
            for btn in self.botones:
                btn.check_hover(mx, my)
                if click and btn.hover: accion = btn.data

            if accion:
                if accion == "VOLVER": self.ir_atras()
                elif accion == "HOME": self.ir_a_inicio()
                elif self.estado == "MODOS":
                    if accion == "AYUDA":
                        self.estado = "AYUDA"
                        self.crear_interfaz_ayuda()
                    else: self.set_modo(accion)
                elif self.estado == "JUGADORES": self.set_jugadores(accion)
                elif self.estado == "CANCIONES":
                    if accion == "RESET": 
                        self.biblio.resetear_filtros()
                        self.crear_interfaz_canciones()
                    else: self.configurar_preview(accion)
                elif self.estado == "PREVIEW":
                    if accion == "START": self.lanzar_juego()

            # RENDERIZADO
            self.screen.fill(FONDO)
            y_header = int(ALTO * 0.05)
            
            if self.estado == "AYUDA":
                tit = self.font_big.render("GUÍA DE JUEGO", True, NEON_AMARILLO)
                self.screen.blit(tit, ((ANCHO//2) - (tit.get_width()//2), int(ALTO * 0.05)))
                
                # Definir dimensiones de las cajas
                box_y = int(ALTO * 0.18)
                box_h = int(ALTO * 0.65)
                box_w = int(ANCHO * 0.28) # 3 cajas ocupan ~84% del ancho
                gap = int(ANCHO * 0.03)
                
                start_x = (ANCHO - (box_w * 3 + gap * 2)) // 2
                
                # --- CAJA 1: PREPARACIÓN (Verde) ---
                self.dibujar_caja_ayuda(
                    start_x, box_y, box_w, box_h, 
                    "📷 1. PREPARACIÓN",
                    [
                        "Colócate a 2-3 metros de la cámara.",
                        "Asegúrate de que se te vea entero.",
                        "Evita ropa muy holgada.",
                        "Iluminación frontal (no contraluz).",
                        "Despeja el área de muebles."
                    ],
                    NEON_VERDE
                )

                # --- CAJA 2: CÓMO JUGAR (Rosa) ---
                self.dibujar_caja_ayuda(
                    start_x + box_w + gap, box_y, box_w, box_h, 
                    "💃 2. MECÁNICA",
                    [
                        "Imita al bailarín como un ESPEJO.",
                        "Esqueleto ROSA: Movimiento ideal.",
                        "Esqueleto VERDE: Tu posición.",
                        "MODO FIESTA: Todos bailan a la vez.",
                        "MODO BATALLA: Turnos 1vs1.",
                        "¡Consigue puntos por precisión!"
                    ],
                    NEON_ROSA
                )

                # --- CAJA 3: COMANDOS DE VOZ (Azul) ---
                self.dibujar_caja_ayuda(
                    start_x + (box_w + gap) * 2, box_y, box_w, box_h, 
                    "🎤 3. COMANDOS DE VOZ",
                    [
                        "NAVEGACIÓN: 'Menú', 'Volver', 'Salir'.",
                        "SELECCIÓN: 'Pon Rasputin', 'La uno'.",
                        "JUEGO: 'Pausa', 'Continuar'.",
                        "BATALLA: 'Siguiente' (Saltar turno).",
                        "BUSCAR: 'Buscar Rock', 'Reiniciar'.",
                        "CONFIRMAR: 'Empezar', 'Dale'."
                    ],
                    NEON_AZUL
                )
                
                # Renderizar botón volver
                for btn in self.botones: 
                    btn.dibujar(self.screen, self.font_mid)
            
            else:
                y_content = int(ALTO * 0.15)
                
                # --- RENDERIZADO PREVIEW CON CÁMARA (NUEVO) ---
                if self.estado == "PREVIEW":
                    mitad_w = ANCHO // 2
                    h_util = int(ALTO * 0.50)
                    
                    # 1. VIDEO (LADO IZQUIERDO)
                    if self.clip:
                        elapsed = time.time() - self.start_time
                        if elapsed >= self.clip.duration: self.start_time = time.time(); elapsed = 0
                        try:
                            frame = self.clip.get_frame(elapsed)
                            surf = pygame.surfarray.make_surface(frame.swapaxes(0,1))
                            # Escalamos para que ocupe un buen trozo
                            surf = pygame.transform.scale(surf, (int(mitad_w * 0.8), h_util))
                            
                            # Centramos en la mitad izquierda
                            x_vid = (mitad_w - surf.get_width()) // 2
                            self.screen.blit(surf, (x_vid, y_content))
                            pygame.draw.rect(self.screen, NEON_AZUL, (x_vid-5, y_content-5, surf.get_width()+10, h_util+10), 3)
                        except: pass
                    
                    # 2. CÁMARA (LADO DERECHO)
                    if self.cap and self.cap.isOpened():
                        ret, cam_frame = self.cap.read()
                        if ret:
                            cam_frame = cv2.flip(cam_frame, 1) # Espejo
                            cam_frame = cv2.cvtColor(cam_frame, cv2.COLOR_BGR2RGB)
                            cam_frame = np.rot90(cam_frame)
                            cam_surf = pygame.surfarray.make_surface(cam_frame)
                            
                            # Escalamos igual que el video
                            cam_surf = pygame.transform.scale(cam_surf, (int(mitad_w * 0.8), h_util))
                            
                            # Centramos en la mitad derecha
                            x_cam = mitad_w + (mitad_w - cam_surf.get_width()) // 2
                            self.screen.blit(cam_surf, (x_cam, y_content))
                            pygame.draw.rect(self.screen, NEON_VERDE, (x_cam-5, y_content-5, cam_surf.get_width()+10, h_util+10), 3)
                            
                            # Texto "CHECK"
                            check_txt = self.font_small.render("VERIFICA TU POSICIÓN", True, NEON_VERDE)
                            self.screen.blit(check_txt, (x_cam, y_content - 30))

                # TITULO Y BOTONES (RESTO DE ESTADOS)
                tit_txt = self.datos_juego["cancion"]["titulo"] if self.estado=="PREVIEW" else self.estado
                if self.estado=="MODOS": tit_txt = "SELECCIONA MODO"
                
                tit = self.font_big.render(tit_txt, True, BLANCO)
                self.screen.blit(tit, ((ANCHO//2)-(tit.get_width()//2), y_header))

                if self.estado == "CANCIONES" and self.biblio.filtro_activo != "Ninguno":
                    f_txt = self.font_small.render(f"Filtro: {self.biblio.filtro_activo}", True, NEON_ROSA)
                    self.screen.blit(f_txt, ((ANCHO//2)-(f_txt.get_width()//2), int(ALTO*0.1)))

                for btn in self.botones: btn.dibujar(self.screen, self.font_mid)

            pygame.display.flip()
            self.clock.tick(FPS)