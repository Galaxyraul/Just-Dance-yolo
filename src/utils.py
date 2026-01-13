import unicodedata
from difflib import SequenceMatcher
import os
from moviepy.video.io.VideoFileClip import VideoFileClip

def normalizar_texto(texto):
    """Quita tildes y pone minúsculas."""
    texto = str(texto).lower()
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')

def es_parecido(input_voz, palabra_clave, umbral=0.8):
    """Fuzzy matching para comandos de voz."""
    input_norm = normalizar_texto(input_voz)
    clave_norm = normalizar_texto(palabra_clave)
    
    if clave_norm in input_norm: return True
    
    for palabra in input_norm.split():
        if SequenceMatcher(None, palabra, clave_norm).ratio() >= umbral:
            return True
    return False

def asegurar_audio_preview(ruta_video):
    """Extrae audio mp3 del video si no existe."""
    ruta_audio = ruta_video.replace(".mp4", ".mp3")
    if not os.path.exists(ruta_audio) and os.path.exists(ruta_video):
        try:
            clip = VideoFileClip(ruta_video)
            clip = clip.subclip(0, min(30, clip.duration))
            clip.audio.write_audiofile(ruta_audio, logger=None)
            clip.close()
        except Exception:
            return None
    return ruta_audio