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
GRAPH_FILE = "data/graph_real.json"
USE_INCREMENTAL = False  # Activar para reutilizar aristas existentes


def load_existing_graph():
    """Carga el grafo existente y crea un índice de aristas"""
    if not os.path.exists(GRAPH_FILE):
        print("No se encontró grafo existente. Se creará desde cero.")
        return [], set()

    try:
        with open(GRAPH_FILE, "r", encoding="utf-8") as f:
            edges = json.load(f)

        # Crear índice de pares existentes (bidireccional)
        existing_pairs = set()
        for edge in edges:
            from_id = edge["from"]
            to_id = edge["to"]
            # Guardar ambas direcciones ya que (i,j) = (j,i)
            existing_pairs.add((min(from_id, to_id), max(from_id, to_id)))

        print(f"✓ Grafo existente cargado: {len(edges)} aristas")
        print(f"✓ Pares únicos existentes: {len(existing_pairs)}")
        return edges, existing_pairs

    except Exception as e:
        print(f"⚠ Error al cargar grafo existente: {e}")
        print("Se creará desde cero.")
        return [], set()


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
    print("="*70)
    if USE_INCREMENTAL:
        print("🚀 MODO INCREMENTAL: Reutilizando aristas existentes")
    else:
        print("🔨 MODO COMPLETO: Creando grafo desde cero")
    print("="*70)
    print(f"Construyendo grafo real con OSRM (max {MAX_DISTANCE_KM} km)...")

    # PASO 1: Cargar grafo existente (si modo incremental activado)
    existing_edges = []
    existing_pairs = set()

    if USE_INCREMENTAL:
        existing_edges, existing_pairs = load_existing_graph()

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

    # PASO 2: Filtrar pares que ya existen
    new_pairs = []
    if USE_INCREMENTAL and existing_pairs:
        for i, j in pairs:
            id_i = stations[i]["id"]
            id_j = stations[j]["id"]
            pair_key = (min(id_i, id_j), max(id_i, id_j))

            if pair_key not in existing_pairs:
                new_pairs.append((i, j))

        print(f"\n📊 Estadísticas de optimización:")
        print(f"  • Total de pares candidatos: {len(pairs)}")
        print(f"  • Pares ya existentes reutilizados: {len(pairs) - len(new_pairs)}")
        print(f"  • Pares NUEVOS a consultar: {len(new_pairs)}")
        print(f"  • Tiempo ahorrado: ~{(len(pairs) - len(new_pairs)) * 0.3 / 60:.1f} minutos")

        pairs_to_query = new_pairs
    else:
        pairs_to_query = list(pairs)
        print(f"{len(pairs_to_query)} pares optimizados dentro del rango.")

    # Fin optimización

    print(f"Iniciando descarga de {len(pairs_to_query)} rutas nuevas...")

    edges = []
    if pairs_to_query:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(get_route_between, pair): pair for pair in pairs_to_query}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    edges.append(result)

    print(f"\nPrimera fase: {len(edges)} aristas nuevas creadas")

    # PASO 3: Combinar aristas existentes y nuevas
    if USE_INCREMENTAL:
        all_edges = existing_edges + edges
        print(f"Total con aristas reutilizadas: {len(all_edges)} aristas")
    else:
        all_edges = edges

    # Analizar componentes
    components, never_connected = find_connected_components(all_edges)

    if len(components) > 1:
        print(f"\nSe encontraron {len(components)} componentes separados")
        new_edges = connect_isolated_components(all_edges, components)
        all_edges.extend(new_edges)
        print(f"\n{len(new_edges)} nuevas conexiones agregadas")

        # Verificar nuevamente
        components, never_connected = find_connected_components(all_edges)
        print(f"\nComponentes finales: {len(components)}")

    if never_connected:
        print(f"\nAdvertencia: {len(never_connected)} nodos sin conexion por calles")

    # Guardar
    with open(GRAPH_FILE, "w", encoding="utf-8") as f:
        json.dump(all_edges, f, ensure_ascii=False, indent=2)

    connected_nodes = len(set(e['from'] for e in all_edges) | set(e['to'] for e in all_edges))

    print("\n" + "="*70)
    if USE_INCREMENTAL:
        print("✅ GRAFO ACTUALIZADO (MODO INCREMENTAL)")
        print(f"  • Aristas reutilizadas: {len(existing_edges)}")
        print(f"  • Aristas nuevas: {len(all_edges) - len(existing_edges)}")
    else:
        print("✅ GRAFO CREADO (MODO COMPLETO)")
    print(f"  • Total de aristas: {len(all_edges)}")
    print(f"  • Nodos conectados: {connected_nodes}/{len(stations)}")
    print(f"  • Archivo: {GRAPH_FILE}")
    print("="*70)


if __name__ == "__main__":
    build_real_graph()
