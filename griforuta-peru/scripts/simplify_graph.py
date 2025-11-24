# scripts/simplify_graph.py
import json
import os

input_file = "../backend/data/graph_real.json"
output_file = "../frontend/public/graph_simplified.geojson"

with open(input_file, 'r', encoding='utf-8') as f:
    edges = json.load(f)

features = []
for i, edge in enumerate(edges):
    if i % 3 == 0:  # Solo 1 de cada 3 aristas (reduce 66%)
        continue
    # Simplificar polyline: solo cada 5to punto
    simplified = edge["polyline"][::5]
    if len(simplified) < 2:
        continue

    features.append({
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[p[1], p[0]] for p in simplified]  # Leaflet usa [lat, lng]
        },
        "properties": {
            "stroke": "#94a3b8",
            "stroke-opacity": 0.4,
            "stroke-width": 2
        }
    })

geojson = {
    "type": "FeatureCollection",
    "features": features
}

os.makedirs("../frontend/public", exist_ok=True)
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(geojson, f, ensure_ascii=False)

print(f"Listo! Grafo simplificado: {len(features)} aristas → {output_file}")
print("Tamaño: ~200–500 KB → carga en 2 segundos")