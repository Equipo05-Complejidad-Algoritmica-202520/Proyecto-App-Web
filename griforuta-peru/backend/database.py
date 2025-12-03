# backend/database.py
import pandas as pd
import os

# Ruta al archivo CSV de datos
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "grifos_costa_peruana.csv")

# Carga y limpia TODO lo que pueda causar NaN
df = pd.read_csv(DATA_PATH, sep=",")

# Elimina filas sin coordenadas
df = df.dropna(subset=['lat', 'lng']).reset_index(drop=True)

# Rellena TODOS los NaN con valores seguros (cadena vacía o 0)
df = df.fillna({
    col: "" for col in df.select_dtypes(include=['object']).columns
})
df = df.fillna({
    col: 0 for col in df.select_dtypes(include=['float64', 'int64']).columns
})

# Añade ID único
df['id'] = df.index

# Convierte a lista de diccionarios (limpio)
stations = df.to_dict(orient="records")

def get_station_by_name_partial(query: str):
    query = query.lower().strip()
    if len(query) < 2:
        return []
    matches = [
        s for s in stations
        if query in str(s.get("RAZON SOCIAL", "")).lower()
        or query in str(s.get("DIRECCION OPERATIVA", "")).lower()
        or query in str(s.get("DISTRITO", "")).lower()
        or query in str(s.get("DEPARTAMENTO", "")).lower()
    ]
    return matches[:20]

def get_station_by_id(id: int):
    return next((s for s in stations if s["id"] == id), None)

def get_all_stations():
    return stations