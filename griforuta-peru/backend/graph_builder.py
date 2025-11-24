# backend/graph_builder.py
import requests
import json
import os
import time
from geopy.distance import geodesic
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from database import stations

os.makedirs("data", exist_ok=True)

MAX_DISTANCE_KM = 40
MAX_WORKERS = 15
TIMEOUT = 15
RETRY_ATTEMPTS = 2
EXTENDED_RANGE_MULTIPLIER = 1.5


def get_route_between(pair, attempt=1):
    i, j = pair
    s1 = stations[i]
    s2 = stations[j]

    dist_km = geodesic((s1['lat'], s1['lng']), (s2['lat'], s2['lng'])).km
    if dist_km > MAX_DISTANCE_KM:
        return None

    coords = f"{s1['lng']},{s1['lat']};{s2['lng']},{s2['lat']}"
    url = f"http://router.project-osrm.org/route/v1/driving/{coords}?overview=full&geometries=geojson"

    try:
        r = requests.get(url, timeout=TIMEOUT)
        if r.status_code == 200:
            data = r.json()
            if data.get("routes"):
                route = data["routes"][0]
                geometry = route["geometry"]["coordinates"]
                polyline = [[coord[1], coord[0]] for coord in geometry]
                distance_km = route["distance"] / 1000

                edge = {
                    "from": s1["id"],
                    "to": s2["id"],
                    "distance_km": round(distance_km, 2),
                    "polyline": polyline
                }
                print(f"Conexion {i}-{j}: {distance_km:.1f} km (intento {attempt})")
                return edge
            else:
                print(f"Sin ruta por calles entre {i}-{j}")
        elif r.status_code == 429:
            time.sleep(2)
            if attempt < RETRY_ATTEMPTS:
                return get_route_between(pair, attempt + 1)
    except requests.exceptions.Timeout:
        print(f"Timeout {i}-{j}, reintentando...")
        if attempt < RETRY_ATTEMPTS:
            time.sleep(1)
            return get_route_between(pair, attempt + 1)
    except Exception as e:
        print(f"Error {i}-{j}: {str(e)[:50]}")

    return None


def find_connected_components(edges):
    """Encuentra todos los componentes conexos en el grafo"""
    graph = defaultdict(set)
    all_nodes = set()

    for edge in edges:
        graph[edge["from"]].add(edge["to"])
        graph[edge["to"]].add(edge["from"])
        all_nodes.add(edge["from"])
        all_nodes.add(edge["to"])

    if not all_nodes:
        return [], []

    components = []
    visited_global = set()

    for start_node in all_nodes:
        if start_node in visited_global:
            continue

        component = set()
        queue = deque([start_node])

        while queue:
            node = queue.popleft()
            if node in component:
                continue
            component.add(node)
            visited_global.add(node)
            for neighbor in graph[node]:
                if neighbor not in component:
                    queue.append(neighbor)

        components.append(component)

    # Ordenar por tamaño (componente principal primero)
    components.sort(key=len, reverse=True)

    # Nodos nunca conectados
    all_station_ids = {s["id"] for s in stations}
    never_connected = all_station_ids - all_nodes

    return components, list(never_connected)


def connect_isolated_components(edges, components):
    """Conecta componentes aislados al componente principal usando rutas por calles"""
    if len(components) <= 1:
        print("Todos los nodos estan en un solo componente")
        return []

    main_component = components[0]
    isolated_components = components[1:]

    print(f"\nComponente principal: {len(main_component)} nodos")
    print(f"Componentes aislados: {len(isolated_components)} grupos")

    id_to_station = {s["id"]: s for s in stations}
    id_to_index = {s["id"]: idx for idx, s in enumerate(stations)}
    new_edges = []

    for component_idx, isolated_component in enumerate(isolated_components, 1):
        print(f"\nConectando componente {component_idx} ({len(isolated_component)} nodos)...")

        # Encontrar pares más cercanos entre componente aislado y principal
        best_connections = []

        for iso_id in isolated_component:
            iso_station = id_to_station.get(iso_id)
            if not iso_station:
                continue

            for main_id in main_component:
                main_station = id_to_station[main_id]
                dist = geodesic(
                    (iso_station['lat'], iso_station['lng']),
                    (main_station['lat'], main_station['lng'])
                ).km

                if dist <= MAX_DISTANCE_KM * EXTENDED_RANGE_MULTIPLIER:
                    best_connections.append((dist, iso_id, main_id))

        # Ordenar por distancia y intentar conectar
        best_connections.sort()

        connected = False
        for dist, iso_id, main_id in best_connections[:10]:  # Intentar top 10
            i = id_to_index[iso_id]
            j = id_to_index[main_id]

            edge = get_route_between((i, j))
            if edge:
                new_edges.append(edge)
                print(f"Componente {component_idx} conectado: {iso_id} -> {main_id} ({dist:.1f} km)")
                main_component.update(isolated_component)  # Fusionar componentes
                connected = True
                break

        if not connected:
            print(f"No se pudo conectar componente {component_idx} por calles")

    return new_edges


def build_real_graph():
    print(f"Construyendo grafo real con OSRM (max {MAX_DISTANCE_KM} km)...")

    # Optimización K-Nearest Neighbors
    # En lugar de todos contra todos, buscamos solo los K vecinos más cercanos
    # Esto reduce drásticamente las conexiones en zonas densas (ej. Lima)
    K_NEIGHBORS = 8  # Número de conexiones por nodo
    pairs = set()
    n = len(stations)
    
    # Pre-cachear coordenadas para velocidad
    coords = [(s['lat'], s['lng']) for s in stations]
    
    print(f"Calculando los {K_NEIGHBORS} vecinos más cercanos para cada estación...")
    
    for i in range(n):
        # Lista temporal de candidatos para el nodo i
        candidates = []
        for j in range(n):
            if i == j: continue
            
            # Filtro rápido euclidiano (más rápido que geodesic para ordenamiento simple)
            # No es exacto en km, pero sirve para encontrar los "más cercanos"
            d_lat = coords[i][0] - coords[j][0]
            d_lng = coords[i][1] - coords[j][1]
            dist_sq = d_lat*d_lat + d_lng*d_lng
            
            # Solo consideramos si está "razonablemente" cerca para no llenar memoria
            # 0.5 grados es aprox 55km
            if dist_sq < 0.5**2:
                candidates.append((dist_sq, j))
        
        # Ordenar por distancia y tomar los K más cercanos
        candidates.sort()
        
        for _, j in candidates[:K_NEIGHBORS]:
            # Verificar distancia real geodésica
            dist = geodesic(coords[i], coords[j]).km
            if dist <= MAX_DISTANCE_KM:
                # Guardar par ordenado para evitar duplicados (i,j) == (j,i)
                pair = tuple(sorted((i, j)))
                pairs.add(pair)

    pairs = list(pairs)
    # Fin optimización

    print(f"{len(pairs)} pares optimizados dentro del rango. Iniciando descarga...")

    edges = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(get_route_between, pair): pair for pair in pairs}
        for future in as_completed(futures):
            result = future.result()
            if result:
                edges.append(result)

    print(f"\nPrimera fase: {len(edges)} aristas creadas")

    # Analizar componentes
    components, never_connected = find_connected_components(edges)

    if len(components) > 1:
        print(f"\nSe encontraron {len(components)} componentes separados")
        new_edges = connect_isolated_components(edges, components)
        edges.extend(new_edges)
        print(f"\n{len(new_edges)} nuevas conexiones agregadas")

        # Verificar nuevamente
        components, never_connected = find_connected_components(edges)
        print(f"\nComponentes finales: {len(components)}")

    if never_connected:
        print(f"\nAdvertencia: {len(never_connected)} nodos sin conexion por calles")

    # Guardar
    with open("data/graph_real.json", "w", encoding="utf-8") as f:
        json.dump(edges, f, ensure_ascii=False, indent=2)

    connected_nodes = len(set(e['from'] for e in edges) | set(e['to'] for e in edges))
    print(f"\nGrafo construido: {len(edges)} aristas")
    print(f"Nodos conectados: {connected_nodes}/{len(stations)}")
    print("Guardado en data/graph_real.json")


if __name__ == "__main__":
    build_real_graph()
