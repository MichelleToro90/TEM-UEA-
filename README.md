# App Clima UEA

App en Python que consulta temperaturas con **Open-Meteo**, construye una **matriz 3D** `[ciudad][semana][día]` y calcula **promedios semanales** con bucles anidados. Incluye modo opcional de **Guayaquil por hora** con filtros (widgets).

## 🚀 Características
- Entrada interactiva de **ciudades** (geocodificación automática).
- Descarga de **temperaturas diarias promedio** y armado de matriz 3D.
- Cálculo de **promedios semanales por ciudad**, **promedio global** y **máximo** con su ubicación.
- (Opcional) **Visor por hora** de Guayaquil con **widgets** (Streamlit).

## 📦 Requisitos
- Python 3.10+  
- Pip (incluido con Python)

## 🧰 Instalación
```bash
# Crear y activar entorno (Windows)
py -m venv .venv
.\.venv\Scripts\activate

# Actualizar pip e instalar dependencias
python -m pip install --upgrade pip
pip install requests pandas streamlit
