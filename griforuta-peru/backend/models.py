from pydantic import BaseModel
from typing import List, Optional

class Station(BaseModel):
    id: int
    nombre: str
    razon_social: str
    direccion: str
    departamento: str
    provincia: str
    distrito: str
    lat: float
    lng: float
    capacidad: float

class RouteResponse(BaseModel):
    origen: Station
    destino: Station
    distancia_km: float
    ruta: List[Station]
    duracion_estimada_min: float