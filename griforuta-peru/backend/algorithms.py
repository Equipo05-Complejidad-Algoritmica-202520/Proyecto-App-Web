# backend/algorithms.py
import numpy as np
from geopy.distance import geodesic
from database import stations
import math
import heapq

print(f"Cargando {len(stations)} grifos... Construyendo matriz de distancias (esto toma ~60 segundos con 500 grifos)")


# Pre-calcular matriz de distancias (solo una vez al iniciar)
def build_distance_matrix():
    n = len(stations)
    dist = np.full((n, n), float('inf'))
    for i in range(n):
        dist[i][i] = 0
        for j in range(i + 1, n):
            d = geodesic(
                (stations[i]['lat'], stations[i]['lng']),
                (stations[j]['lat'], stations[j]['lng'])
            ).kilometers
            dist[i][j] = dist[j][i] = d
    return dist


DIST_MATRIX = build_distance_matrix()
print("¡Matriz de distancias lista!")


def dijkstra(start_id: int, end_id: int):
    n = len(stations)
    distances = [float('inf')] * n
    previous = [-1] * n
    distances[start_id] = 0
    pq = [(0, start_id)]

    while pq:
        cost, u = heapq.heappop(pq)
        if cost > distances[u]:
            continue
        for v in range(n):
            if DIST_MATRIX[u][v] < float('inf'):
                alt = cost + DIST_MATRIX[u][v]
                if alt < distances[v]:
                    distances[v] = alt
                    previous[v] = u
                    heapq.heappush(pq, (alt, v))

    # Reconstruir ruta
    path = []
    current = end_id
    while current != -1:
        path.append(current)
        current = previous[current]
    path.reverse()

    if path[0] != start_id:
        return None, None

    return path, distances[end_id]