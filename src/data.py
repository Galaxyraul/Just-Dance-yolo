import json
from config import JSON_PATH

class GestorBiblioteca:
    def __init__(self):
        try:
            with open(JSON_PATH, 'r') as f:
                self.canciones_base = json.load(f)
        except:
            self.canciones_base = [] 

        self.canciones_visibles = self.canciones_base.copy()
        self.filtro_activo = "Ninguno"

    def aplicar_filtro(self, tipo, valor):
        valor = str(valor).lower().strip()
        self.filtro_activo = f"{tipo}: {valor}"
        
        nueva_lista = []
        for c in self.canciones_base:
            match = False
            
            # Obtenemos la lista de apodos (tanto de canción como de artista)
            lista_alias = c.get('alias', [])
            
            # --- LÓGICA DE COINCIDENCIA ---

            if tipo == "ARTISTA":
                # 1. Mira nombre real
                if valor in c['artista'].lower(): match = True
                # 2. Mira si el valor está en los alias (ej: "parque" para Linkin Park)
                for alias in lista_alias:
                    if valor in alias: match = True

            elif tipo == "BUSCAR":
                # 1. Mira Título y Artista
                if (valor in c['titulo'].lower() or valor in c['artista'].lower()):
                    match = True
                # 2. Mira Alias (sirve para "Nam" o para "Linkin")
                for alias in lista_alias:
                    if valor in alias: match = True
            
            elif tipo == "GENERO":
                if valor in c['genero'].lower(): match = True
            
            elif tipo == "ANIO":
                if valor in str(c['anio']): match = True
            
            elif tipo == "CAPACIDAD":
                if str(c['capacidad']) == valor: match = True
            
            if match: nueva_lista.append(c)
        
        self.canciones_visibles = nueva_lista

    def resetear_filtros(self):
        self.canciones_visibles = self.canciones_base.copy()
        self.filtro_activo = "Ninguno"