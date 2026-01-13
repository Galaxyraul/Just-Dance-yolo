import json
import math
import os
import numpy as np

# Pares de puntos que forman los huesos principales (Indices YOLO)
# (Punto Inicial, Punto Final)
HUESOS_EVALUAR = [
    (5, 7),   # Hombro Izq -> Codo Izq
    (7, 9),   # Codo Izq -> Muñeca Izq
    (6, 8),   # Hombro Der -> Codo Der
    (8, 10),  # Codo Der -> Muñeca Der
    (11, 13), # Cadera Izq -> Rodilla Izq
    (13, 15), # Rodilla Izq -> Tobillo Izq
    (12, 14), # Cadera Der -> Rodilla Der
    (14, 16), # Rodilla Der -> Tobillo Der
    (5, 6),   # Hombros (Para ver si el torso está girado)
    (11, 12)  # Caderas
]

class SistemaPuntuacion:
    def __init__(self, ruta_json):
        self.datos = None
        self.fps = 30
        self.puntuacion_total = 0
        self.racha = 0
        self.mensaje_actual = ""
        self.color_mensaje = (255, 255, 255)

        if os.path.exists(ruta_json):
            try:
                with open(ruta_json, 'r') as f:
                    self.datos = json.load(f)
                self.fps = self.datos["meta"].get("fps", 30)
                self.total_frames = len(self.datos["frames"])
                print(f"✅ Coreografía cargada: {self.total_frames} frames (Modo Vectores).")
            except Exception as e:
                print(f"⚠️ Error leyendo JSON: {e}")
        else:
            print("⚠️ No hay archivo .json de coreografía.")

    def obtener_esqueleto_actual(self, tiempo_actual):
        if self.datos is None: return None
        frame_idx = int(tiempo_actual * self.fps)
        if frame_idx >= self.total_frames: return None
        return self.datos["frames"][frame_idx]

    def calcular_similitud_coseno(self, v1, v2):
        """
        Devuelve un valor entre 0 (idénticos) y 2 (opuestos).
        0.0 -> Vectores paralelos (Mismo ángulo) ✅
        1.0 -> Vectores perpendiculares (90 grados error) ❌
        2.0 -> Vectores opuestos (180 grados error) ❌
        """
        # Convertir a numpy para facilitar matemáticas
        v1 = np.array(v1)
        v2 = np.array(v2)
        
        # Producto punto
        dot_product = np.dot(v1, v2)
        
        # Magnitud (longitud) de los vectores
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        # Evitar división por cero
        if norm_v1 == 0 or norm_v2 == 0:
            return 1.0 # Error neutro
            
        # Similitud Coseno (-1 a 1)
        similarity = dot_product / (norm_v1 * norm_v2)
        
        # Acotamos por errores de flotante
        similarity = np.clip(similarity, -1.0, 1.0)
        
        # Convertimos a "Distancia de Coseno" (0 es perfecto, 2 es opuesto)
        return 1.0 - similarity

    def evaluar(self, tiempo_actual, esqueleto_usuario):
        # Protecciones básicas
        if self.datos is None or esqueleto_usuario is None: return 0, ""
        if len(esqueleto_usuario) == 0: return 0, ""

        frame_idx = int(tiempo_actual * self.fps)
        if frame_idx >= self.total_frames: return 0, "FIN"

        esqueleto_ref = self.datos["frames"][frame_idx]
        if not esqueleto_ref: return 0, "..." 

        error_acumulado = 0
        huesos_comparados = 0

        # Iteramos sobre los HUESOS (Vectores), no los puntos
        for idx_a, idx_b in HUESOS_EVALUAR:
            # Puntos del Usuario
            if idx_a >= len(esqueleto_usuario) or idx_b >= len(esqueleto_usuario): continue
            
            u_start = esqueleto_usuario[idx_a] # [x, y, conf]
            u_end = esqueleto_usuario[idx_b]
            
            # Puntos de la Referencia
            r_start = esqueleto_ref[idx_a]
            r_end = esqueleto_ref[idx_b]

            # Solo comparamos si la confianza es buena en AMBOS extremos del hueso
            if u_start[2] > 0.5 and u_end[2] > 0.5 and r_start[2] > 0.5 and r_end[2] > 0.5:
                # Crear Vectores (Final - Inicial)
                # Solo usamos X e Y (índices 0 y 1)
                vec_usuario = [u_end[0] - u_start[0], u_end[1] - u_start[1]]
                vec_ref = [r_end[0] - r_start[0], r_end[1] - r_start[1]]
                
                distancia_angular = self.calcular_similitud_coseno(vec_usuario, vec_ref)
                
                error_acumulado += distancia_angular
                huesos_comparados += 1

        if huesos_comparados < 3: 
            return 0, "..." # No se ve suficiente esqueleto

        # Promedio del error angular
        error_promedio = error_acumulado / huesos_comparados
        
        # --- NUEVOS UMBRALES (Basados en Coseno) ---
        # 0.00 = Ángulo idéntico (0 grados de diferencia)
        # 0.05 = Muy pequeño error
        # 0.15 = Error aceptable
        # > 0.20 = Pose incorrecta
        
        ganancia = 0
        msg = ""
        print(f"Error promedio:{error_promedio}")
        if error_promedio < 0.08: # Umbral estricto (aprox 20 grados error promedio)
            ganancia = 100
            msg = "PERFECTO"
            self.color_mensaje = (0, 255, 255) # Cyan
            self.racha += 1
        elif error_promedio < 0.4: # Umbral medio (aprox 40 grados error promedio)
            ganancia = 50
            msg = "BIEN"
            self.color_mensaje = (0, 255, 0) # Verde
            self.racha += 1
        else:
            msg = "MISS"
            self.color_mensaje = (255, 0, 0) # Rojo
            self.racha = 0

        # Bonus racha
        if self.racha > 10: ganancia += 50
        elif self.racha > 5: ganancia += 20

        self.puntuacion_total += ganancia
        
        if ganancia > 0 or msg == "MISS":
            self.mensaje_actual = msg
        elif ganancia == 0 and msg == "":
            self.mensaje_actual = ""
        
        return ganancia, msg