# pip install requests
import requests
from datetime import date, timedelta

# ---------- Configuración ----------
NUM_SEMANAS = 4
TZ = "America/Guayaquil"

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


# ---------- Utilidades de geocodificación ----------
def geocodificar_opciones(nombre, count=5, lang="es"):
    """
    Devuelve una lista de posibles coincidencias para 'nombre'.
    Cada item es un dict con name, country, admin1, latitude, longitude.
    """
    params = {"name": nombre, "count": count, "language": lang, "format": "json"}
    r = requests.get(GEOCODE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])


def elegir_ciudad(nombre_busqueda):
    """
    Muestra opciones al usuario si hay varias coincidencias y retorna:
    (etiqueta_mostrable, lat, lon)
    """
    opciones = geocodificar_opciones(nombre_busqueda)
    if not opciones:
        raise ValueError(f"No encontré coordenadas para: {nombre_busqueda}")

    # Si hay una sola, la tomamos directo
    if len(opciones) == 1:
        o = opciones[0]
        etiqueta = construir_etiqueta(o)
        return etiqueta, o["latitude"], o["longitude"]

    # Varias opciones: listar y pedir elección
    print(f"\nSe encontraron varias coincidencias para '{nombre_busqueda}':")
    for i, o in enumerate(opciones, start=1):
        print(f"  {i}. {construir_etiqueta(o)}  (lat={o['latitude']}, lon={o['longitude']})")

    while True:
        sel = input("Elige un número (Enter = 1): ").strip()
        if sel == "":
            idx = 1
        else:
            if not sel.isdigit():
                print("Ingresa un número válido.")
                continue
            idx = int(sel)
        if 1 <= idx <= len(opciones):
            o = opciones[idx - 1]
            etiqueta = construir_etiqueta(o)
            return etiqueta, o["latitude"], o["longitude"]
        print("Fuera de rango, intenta de nuevo.")


def construir_etiqueta(o):
    """Crea una etiqueta legible tipo 'Guayaquil, Guayas, Ecuador'."""
    partes = [o.get("name")]
    if o.get("admin1"):
        partes.append(o["admin1"])
    if o.get("country"):
        partes.append(o["country"])
    return ", ".join([p for p in partes if p])


# ---------- Temperaturas diarias (histórico) ----------
def temps_diarias_promedio(lat, lon, start, end, tz=TZ):
    """Devuelve lista de temperaturas diarias promedio (°C) entre start y end."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "temperature_2m_mean",
        "timezone": tz,
        "temperature_unit": "celsius",
    }
    r = requests.get(ARCHIVE_URL, params=params, timeout=30)
    r.raise_for_status()
    d = r.json()
    daily = d.get("daily", {})
    vals = daily.get("temperature_2m_mean")
    if not vals:
        raise RuntimeError("La API no devolvió 'temperature_2m_mean' para ese rango.")
    return vals  # lista de floats


def pedir_ciudades():
    """
    Pide al usuario una o varias ciudades.
    Sugerencia: separar ciudades con ';'
    """
    print("Ingresa una o varias ciudades. Ejemplo:")
    print("  Quito, Ecuador; Guayaquil, Ecuador; Cuenca, Ecuador")
    entrada = input("Ciudades: ").strip()

    if not entrada:
        # Predeterminadas si no escribe nada
        return ["Quito, Ecuador", "Guayaquil, Ecuador", "Cuenca, Ecuador"]

    # Si el usuario usó ';' o '|', separamos; si no, tomamos una sola ciudad
    if ";" in entrada or "|" in entrada:
        brutos = [c.strip() for c in entrada.replace("|", ";").split(";")]
        return [c for c in brutos if c]
    else:
        return [entrada]


def main():
    # --- Rango de fechas: últimas 4 semanas completas (histórico suele retrasarse unos días) ---
    hoy = date.today()
    end_date = hoy - timedelta(days=5)  # margen por retraso del histórico
    start_date = end_date - timedelta(days=7 * NUM_SEMANAS - 1)

    # --- Pedir ciudades al usuario y resolver coordenadas ---
    ciudades_ingresadas = pedir_ciudades()
    seleccionadas = []  # [(etiqueta, lat, lon), ...]

    for nombre in ciudades_ingresadas:
        etiqueta, lat, lon = elegir_ciudad(nombre)
        seleccionadas.append((etiqueta, lat, lon))

    # --- Construir matriz 3D [ciudad][semana][día] ---
    temperaturas = []  # por ciudad: lista de semanas; por semana: 7 valores
    etiquetas = []

    for etiqueta, lat, lon in seleccionadas:
        diarias = temps_diarias_promedio(lat, lon, start_date, end_date, TZ)

        # Asegura múltiplos de 7 días y toma las últimas NUM_SEMANAS semanas
        dias_utiles = (len(diarias) // 7) * 7
        diarias = diarias[-dias_utiles:]
        semanas = []
        for w in range(len(diarias) // 7):
            semana = diarias[w * 7:(w + 1) * 7]
            semanas.append(semana)
        semanas = semanas[-NUM_SEMANAS:]  # recorta a NUM_SEMANAS
        temperaturas.append(semanas)
        etiquetas.append(etiqueta)

    # --- Cálculo de promedios con bucles anidados ---
    promedios = []  # [ciudad][semana] -> promedio
    for i_ciudad in range(len(etiquetas)):
        proms_ciudad = []
        for i_semana in range(len(temperaturas[i_ciudad])):
            suma = 0.0
            for i_dia in range(len(temperaturas[i_ciudad][i_semana])):
                suma += temperaturas[i_ciudad][i_semana][i_dia]
            prom = round(suma / len(temperaturas[i_ciudad][i_semana]), 2)
            proms_ciudad.append(prom)
        promedios.append(proms_ciudad)

    # --- Mostrar resultados ---
    for i_ciudad, nombre in enumerate(etiquetas):
        print(f"\nPromedios semanales de {nombre}:")
        for i_sem, valor in enumerate(promedios[i_ciudad], start=1):
            print(f"  Semana {i_sem}: {valor} °C")


if __name__ == "__main__":
    main()
