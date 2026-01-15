# 🕺Just Dance YOLO
### Sistema de Baile Multimodal con Visión Artificial

![Status](https://img.shields.io/badge/Status-Playable-brightgreen)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![License](https://img.shields.io/badge/License-Educational-orange)

**AI Dance Revolution** es un videojuego de baile ("exergame") desarrollado en Python que utiliza visión artificial para puntuar tus movimientos en tiempo real.

El sistema es **totalmente "Touchless"**: se controla mediante la **voz** y los **gestos**, eliminando la necesidad de mandos, alfombras de baile o contacto con el teclado, lo que permite una experiencia higiénica y cómoda a distancia.

---

## 📑 Índice de Contenidos

- [🕺Just Dance YOLO](#just-dance-yolo)
    - [Sistema de Baile Multimodal con Visión Artificial](#sistema-de-baile-multimodal-con-visión-artificial)
  - [📑 Índice de Contenidos](#-índice-de-contenidos)
  - [🚀 Características Principales](#-características-principales)
  - [📂 Estructura del Proyecto](#-estructura-del-proyecto)
  - [🛠️ Instalación y Requisitos](#️-instalación-y-requisitos)
    - [Prerrequisitos](#prerrequisitos)
    - [Pasos de Instalación](#pasos-de-instalación)
  - [🎮 Manual de Juego](#-manual-de-juego)
    - [Iniciar el Juego](#iniciar-el-juego)
    - [Comandos de Voz](#comandos-de-voz)
      - [1. Navegación General](#1-navegación-general)
      - [2. Selección de Modo y Jugadores](#2-selección-de-modo-y-jugadores)
      - [3. Selección de Canciones](#3-selección-de-canciones)
      - [4. Previsualización (Preview)](#4-previsualización-preview)
      - [5. Durante el Baile (In-Game)](#5-durante-el-baile-in-game)
    - [Modos de Juego](#modos-de-juego)
  - [🎵 Guía para Añadir Canciones](#-guía-para-añadir-canciones)
    - [Paso 1: Preparar el Video](#paso-1-preparar-el-video)
    - [Paso 2: Generar los Datos (JSON)](#paso-2-generar-los-datos-json)
    - [Paso 3: Registrar en la Biblioteca](#paso-3-registrar-en-la-biblioteca)
  - [🐛 Solución de Problemas](#-solución-de-problemas)
  - [👥 Autores](#-autores)

---

## 🚀 Características Principales

* **🕹️ Interacción Multimodal:** Navegación completa por menús usando comandos de voz naturales (SpeechRecognition).
* **📷 Visión Artificial:** Detección de esqueleto en tiempo real (Pose Estimation con MediaPipe) para comparar la biomecánica del usuario con la del bailarín profesional.
* **🧠 Puntuación Vectorial:** Algoritmo basado en **Similitud del Coseno** que evalúa la precisión de los ángulos, ignorando diferencias de altura o distancia a la cámara.
* **⚔️ Modos Flexibles:** Soporte para juego cooperativo (Fiesta) y competitivo por turnos (Batalla).
* **🗣️ Búsqueda Inteligente:** Selección de canciones por título, número de lista o alias fonéticos (ej: *"Pon la de Måneskin"*).

---

## 📂 Estructura del Proyecto

El repositorio sigue una arquitectura modular separando código (`src`), recursos (`assets`) y herramientas (`tools`).

```text
ai-dance-revolution/
│
├── src/                        # CÓDIGO FUENTE
│   ├── menu.py                 # Punto de entrada (Main). Gestiona UI y Estados.
│   ├── game.py                 # Motor de juego (Loop principal, renderizado y lógica).
│   ├── detector.py             # Lógica de Visión Artificial (MediaPipe).
│   ├── inputs.py               # Sistema de reconocimiento de voz (Hilos).
│   ├── puntuacion.py           # Algoritmo de comparación (Similitud del Coseno).
│   ├── data.py                 # Gestor de JSON y base de datos de canciones.
|   ├── ui.py                   # Wrapper de un botón de pygames para personalizarlo
│   └── utils.py                # Funciones auxiliares.
│
├── assets/                     # RECURSOS MULTIMEDIA
│   ├── media/                  # Videos MP4 de las canciones.
│   │   ├── rasputin.mp4
│   │   └── ...
│   │
│   ├── coreos/                 # Datos de movimiento pre-calculados (.json).
│   │   ├── rasputin.json       # Debe llamarse IGUAL que el video.
│   │   └── ...
│   │
│   └── biblioteca.json         # Archivo maestro de configuración.
│
├── tools/                      # HERRAMIENTAS DE DESARROLLO
│   └── creador_coreografias.py # Script para procesar videos nuevos.
│   └── visor_coreografias.py   # Script para comprobar el esqueleto generado respecto a la fuente original
│
├── requirements.txt            # Dependencias del proyecto.
├── README.md                   # Este archivo.
├── config.py                   # Configuración de las rutas y modelos a emplear
└── main.py                     # Archivo principal de ejecución

```

---

## 🛠️ Instalación y Requisitos

### Prerrequisitos

* **Sistema Operativo:** Windows,Linux o Mac.
* **Python:** Versión 3.10 o superior.
* **Hardware:** Webcam y Micrófono funcionales.
* **Software Externo:** FFmpeg (necesario para el procesamiento de audio de MoviePy).

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/Galaxyraul/Just-Dance-yolo.git
cd Just-Dance-yolo

```


2. **Crear un entorno virtual (Recomendado):**
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Mac/Linux:
source venv/bin/activate

```


3. **Instalar dependencias:**
```bash
pip install -r requirements.txt

```


*Si no dispones del archivo, instala manualmente:*

*¡Hay que instalar torch compatible con GPU!*
```bash
pip install pygame opencv-python ultralytics moviepy vosk numpy word2number-es torch torchvideo torchaudio 

```



---

## 🎮 Manual de Juego

### Iniciar el Juego

Ejecuta el archivo principal desde la terminal:

```bash
python main.py

```

### Comandos de Voz

El sistema utiliza reconocimiento de lenguaje natural. No necesitas usar frases robóticas, pero aquí tienes las palabras clave que activan acciones:

#### 1. Navegación General

* **Salir / Cerrar:** Cierra la aplicación desde cualquier pantalla.
* **Volver / Atrás:** Regresa a la pantalla anterior.
* **Menú Principal / Inicio:** Vuelve instantáneamente a la selección de modo (Fiesta/Batalla).
* **Pantalla Completa / Ventana:** Cambia el modo de visualización.

#### 2. Selección de Modo y Jugadores

* *"Modo Fiesta"*, *"Modo Batalla"*.
* *"Ayuda"*, *"Tutorial"*.
* *"Uno"*, *"Dos"*, *"Tres"*...

#### 3. Selección de Canciones

Puedes pedir canciones de tres formas:

* **Por Título:** *"Pon Rasputin"*, *"Quiero bailar la de Eminem"*.
* **Por Alias:** *"Pon la del gorila"*, *"Pon la de Måneskin"*.
* **Filtros:** *"Buscar Rock"*, *"Música de los 80"*, *"Reiniciar filtros"*.

#### 4. Previsualización (Preview)

* *"Empezar"*, *"Confirmar"*, *"Dale"*, *"Seleccionar"*.
* *Nota:* Aquí verás tu cámara a la derecha. Verifica que el esqueleto verde aparece y te cubre entero.

#### 5. Durante el Baile (In-Game)

* **Pausa:** *"Pausa"*, *"Pausar"*.
* **Continuar:** *"Continuar"*, *"Sigue"*.
* **Salir:** *"Salir"*, *"Terminar"*.
* **Saltar Turno (Solo Batalla):** *"Siguiente"*, *"Saltar"*, *"Pasa"*.

### Modos de Juego

1. **🎉 FIESTA (Cooperativo / Solo):**
* Todos bailan a la vez.
* El sistema intenta detectar a todos los esqueletos presentes.
* Ideal para jugar solo o para divertirse en grupo sin competición estricta.


2. **⚔️ BATALLA (Competitivo):**
* Se juega por turnos estrictos (Jugador 1 -> Jugador 2...).
* Cada jugador baila la misma canción individualmente.
* Al final de la ronda, se muestra un **Podio** con el ganador y las puntuaciones.



---

## 🎵 Guía para Añadir Canciones

Para ampliar la biblioteca, necesitas generar el video y los datos de la coreografía.

### Paso 1: Preparar el Video

* Consigue el video en formato `.mp4`.
* Guárdalo en `assets/media/` (ej. `assets/media/despacito.mp4`).

### Paso 2: Generar los Datos (JSON)

El juego necesita pre-calcular la posición de los huesos. Usa la herramienta incluida:

```bash
python tools/creador_coreografias.py

```

* Selecciona el video cuando te lo pida. El script generará automáticamente un archivo `.json` en `assets/coreos/`.

### Paso 3: Registrar en la Biblioteca

Edita el archivo `assets/biblioteca.json` y añade la entrada:

```json
{
    "id": 5,
    "titulo": "Despacito",
    "artista": "Luis Fonsi",
    "anio": 2017,
    "genero": "Latino",
    "dificultad": "Fácil",
    "capacidad": 4,             
    "video": "media/despacito.mp4",
    "alias": [
        "despasito", 
        "luis fonsi", 
        "la de puerto rico"
    ]
}

```

* **`capacidad`**: Número máximo de bailarines en el video.
* **`alias`**: Variaciones fonéticas para que la voz lo reconozca fácil.

---

## 🐛 Solución de Problemas

| Problema | Causa Probable | Solución |
| --- | --- | --- |
| **Error "Permission Denied" en audio** | Windows bloquea el archivo MP3 temporal. | El sistema ya usa nombres dinámicos. Si persiste, borra manualmente los archivos `temp_*.mp3` de la carpeta raíz. |
| **Pantalla Roja/Negra en Preview** | No se encuentra el video. | Verifica que la ruta en `biblioteca.json` coincide exactamente con el nombre del archivo en `assets/media/`. |
| **La cámara no se abre** | Otra app la está usando. | Cierra Zoom, Teams, Discord u otras apps que usen la webcam. |
| **Reconocimiento de voz lento** | Ruido ambiente o micrófono mal configurado. | Habla cerca del micro y ajusta la sensibilidad en el sistema operativo. |
| **"Video no encontrado"** | El juego no encuentra la ruta. | Asegúrate de ejecutar el juego desde la raíz: `python src/menu.py`, NO desde dentro de `src`. |

---

## 👥 Autores

Proyecto desarrollado como parte de la asignatura **Interfaces de Usuario Multimodales**.

* **Desarrolladores Principal:**  Raúl Gómez Téllez - rgt00024 y Rubén Ramírez Peña - rrp00041
* **Institución:** Universidad de Jaén
* **Año:** 2025-2026
