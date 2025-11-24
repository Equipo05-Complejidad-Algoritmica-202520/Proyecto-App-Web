# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os
from database import get_station_by_name_partial, get_station_by_id, get_all_stations
from algorithms import dijkstra

app = FastAPI()

# CORS (para que el frontend funcione)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CARGAR GRAFO REAL (una sola vez)
GRAPH_PATH = os.path.join(os.path.dirname(__file__), "data", "graph_real.json")
if os.path.exists(GRAPH_PATH):
    with open(GRAPH_PATH, "r", encoding="utf-8") as f:
        REAL_GRAPH = json.load(f)
else:
    REAL_GRAPH = []


@app.get("/")
def root():
    return {"message": "GrifoRuta Perú – Grafo real con rutas por carretera"}


@app.get("/search")
def search(q: str = ""):
    if len(q) < 2:
        return {"results": []}
    return {"results": get_station_by_name_partial(q)}


@app.get("/ruta")
def ruta(start: int, end: int):
    origen = get_station_by_id(start)
    destino = get_station_by_id(end)
    if not origen or not destino:
        return {"error": "Estación no encontrada"}

    path_ids, _ = dijkstra(start, end)
    if not path_ids:
        return {"error": "No hay ruta"}

    ruta_estaciones = [get_station_by_id(i) for i in path_ids]

    # Usar OSRM para ruta real entre todos los puntos de la ruta
    coords = ";".join([f"{s['lng']},{s['lat']}" for s in ruta_estaciones])
    osrm_url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"

    try:
        import requests
        r = requests.get(osrm_url, timeout=15)
        if r.status_code == 200:
            data = r.json()
            if data["routes"]:
                route = data["routes"][0]
                polyline = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
                return {
                    "origen": origen,
                    "destino": destino,
                    "distancia_km": round(route["distance"] / 1000, 2),
                    "duracion_estimada_min": round(route["duration"] / 60),
                    "ruta": ruta_estaciones,
                    "polyline": polyline
                }
    except:
        pass

    # Fallback: línea recta
    return {
        "origen": origen,
        "destino": destino,
        "distancia_km": 0,
        "duracion_estimada_min": 0,
        "ruta": ruta_estaciones,
        "polyline": [[s['lat'], s['lng']] for s in ruta_estaciones]
    }


@app.get("/graph")
def get_graph():
    return {"edges": REAL_GRAPH}

@app.get("/grifos")
def get_all_grifos():
    return {"grifos": get_all_stations()}