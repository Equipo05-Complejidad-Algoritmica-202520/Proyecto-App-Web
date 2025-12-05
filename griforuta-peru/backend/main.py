# backend/main.py
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json
import os
from database import get_station_by_name_partial, get_station_by_id, get_all_stations
from algorithms import dijkstra
from fastapi.responses import FileResponse
from pathlib import Path


app = FastAPI()

# CORS (para que el frontend funcione)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    "https://grifos-peru-api.onrender.com"],
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
    osrm_url = (f"http://router.project-osrm.org/route/v1/driving/{coords}?overview="
                f"full&geometries=geojson")

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

@app.get("/grifo_cercano")
def grifo_cercano(lat: float, lng: float):
    from geopy.distance import geodesic
    from database import get_all_stations
    import requests
    import time

    user_coord = (lat, lng)
    stations = get_all_stations()

    # 1. Filtrar candidatos cercanos en línea recta (rápido)
    candidatos = []
    for s in stations:
        dist = geodesic(user_coord, (s['lat'], s['lng'])).kilometers
        if dist < 50:  # Solo grifos a menos de 50 km en línea recta
            candidatos.append((dist, s))

    if not candidatos:
        return {"error": "No hay grifos a menos de 50 km"}

    # Ordenar por distancia aérea
    candidatos.sort(key=lambda x: x[0])
    candidatos = candidatos[:10]  # Tomar solo los 10 más cercanos

    best_grifo = None
    best_distance = float('inf')
    best_polyline = None
    best_duration = 0

    print(f"Probando {len(candidatos)} candidatos cercanos...")

    for _, station in candidatos:
        coords = f"{lng},{lat};{station['lng']},{station['lat']}"
        url = (f"http://router.project-osrm.org/route/v1/driving/{coords}?overview="
               f"full&geometries=geojson")

        try:
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if data.get("routes"):
                    route = data["routes"][0]
                    dist_km = route["distance"] / 1000
                    if dist_km < best_distance:
                        best_distance = dist_km
                        best_grifo = station
                        best_polyline = [[c[1], c[0]] for c in route["geometry"]["coordinates"]]
                        best_duration = round(route["duration"] / 60)
                    # Salir temprano si ya encontramos uno muy bueno
                    if dist_km < 2:
                        break
        except:
            continue

    if not best_grifo:
        return {"error": "No se encontró ruta por carretera a ningún grifo cercano"}

    return {
        "origen": {"lat": lat, "lng": lng},
        "destino": best_grifo,
        "distancia_km": round(best_distance, 2),
        "duracion_estimada_min": best_duration,
        "polyline": best_polyline
    }


# ... tu código existente ...

@app.get("/graph/simplified")
async def get_simplified_graph():
    """Servir grafo simplificado en formato GeoJSON"""
    geojson_path = Path(__file__).parent / "data" / "graph_simplified.geojson"

    if not geojson_path.exists():
        return {"error": "Grafo no generado"}

    return FileResponse(
        path=geojson_path,
        media_type="application/geo+json",
        headers={"Cache-Control": "public, max-age=86400"}  # Cache de 24h
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))  # Render usa $PORT o 10000 por default
    uvicorn.run(
        "main:app", 
        host="0.0.0.0",  # Obligatorio para Render
        port=port, 
        log_level="info",
        reload=False  # Desactiva reload en producción
    )
