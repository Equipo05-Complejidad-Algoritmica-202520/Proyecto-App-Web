// frontend/src/components/Map.jsx
import { MapContainer, TileLayer, GeoJSON, Polyline, CircleMarker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';

function LayerOrderFixer() {
  const map = useMap();
  useEffect(() => {
    if (!map) return;
    const panes = {
      graphPane: 400,
      routePane: 600,
      markersPane: 650,
      highlightPane: 680,
      glowPane: 690
    };
    Object.entries(panes).forEach(([name, zIndex]) => {
      if (!map.getPane(name)) {
        map.createPane(name);
        map.getPane(name).style.zIndex = zIndex;
      }
    });
  }, [map]);
  return null;
}

export default function Map({ ruta }) {
  const [stations, setStations] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch("http://localhost:8000/grifos").then(r => r.json()),
      fetch("/graph_simplified.geojson").then(r => r.json()).catch(() => null)
    ])
      .then(([stationsData, geojson]) => {
        setStations(stationsData.grifos || []);
        setGraphData(geojson);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const center = ruta?.polyline
    ? ruta.polyline[Math.floor(ruta.polyline.length / 2)]
    : [-12.0, -77.0];

  const origenId = ruta?.origen?.id;
  const destinoId = ruta?.destino?.id;
  const rutaIds = ruta ? new Set(ruta.ruta.map(s => s.id)) : new Set();

  const normalStations = stations.filter(s => s.id !== origenId && s.id !== destinoId);
  const highlightStations = stations.filter(s => s.id === origenId || s.id === destinoId);

  return (
    <div className="mt-8 rounded-xl overflow-hidden shadow-2xl border-4 border-indigo-600 relative">
      <MapContainer center={center} zoom={ruta ? 7 : 6} style={{ height: '680px', width: '100%' }}>
        <LayerOrderFixer />
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Grafo simplificado de fondo */}
        {graphData && (
          <GeoJSON
            data={graphData}
            style={() => ({
              color: "#389dfc",
              weight: 3,
              opacity: 0.7
            })}
            pane="graphPane"
          />
        )}

        {/* Ruta principal (gruesa y brillante) */}
        {ruta && ruta.polyline && (
          <Polyline
            positions={ruta.polyline}
            color="#4f46e5"
            weight={10}
            opacity={0.98}
            lineCap="round"
            pane="routePane"
          />
        )}

        {/* Nodos normales (grises y azules en ruta) */}
        {normalStations.map(s => (
          <CircleMarker
            key={`n-${s.id}`}
            center={[s.lat, s.lng]}
            radius={rutaIds.has(s.id) ? 11 : 6}
            fillColor={rutaIds.has(s.id) ? "#6366f1" : "#64748b"}
            color="#ffffff"
            weight={rutaIds.has(s.id) ? 5 : 2}
            fillOpacity={0.9}
            pane="markersPane"
          >
            <Popup>
              <div className="text-sm">
                <strong>{s["RAZON SOCIAL"]}</strong><br />
                {s.DISTRITO}, {s.DEPARTAMENTO}
              </div>
            </Popup>
          </CircleMarker>
        ))}

        {/* ORIGEN Y DESTINO */}
        {highlightStations.map(s => {
          const isOrigen = s.id === origenId;
          return (
            <CircleMarker
              key={`h-${s.id}`}
              center={[s.lat, s.lng]}
              radius={10}
              fillColor={isOrigen ? "#10b981" : "#ef4444"}
              fillOpacity={1}
              color="#ffffff"
              weight={3}
              opacity={1}
              pane="highlightPane"

            >
              <Popup>
                <div className="text-center font-bold p-3 bg-white rounded-lg shadow-2xl border-2 border-gray-300">
                  <div style={{
                    color: isOrigen ? "#10b981" : "#ef4444",
                    fontSize: "1.6em",
                    fontWeight: "900"
                  }}>
                    {isOrigen ? "ORIGEN" : "DESTINO"}
                  </div>
                  <div className="text-lg mt-2 text-gray-800">{s["RAZON SOCIAL"]}</div>
                  <div className="text-sm text-gray-600 mt-1">
                    {s.DISTRITO} • {s.DEPARTAMENTO}
                  </div>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      {/* Loading */}
      {loading && (
        <div className="absolute inset-0 bg-white bg-opacity-95 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-8 border-indigo-600 border-t-transparent mb-6"></div>
            <p className="text-2xl font-bold text-indigo-700">Cargando red nacional de grifos...</p>
            <p className="text-gray-600 mt-2">1500+ estaciones • Rutas reales por OSRM</p>
          </div>
        </div>
      )}

      {/* Leyenda final */}
      <div className="text-center mt-4">
        <p className="text-2xl font-bold text-indigo-700">
          {ruta
            ? "Ruta óptima calculada • Verde = Origen • Rojo = Destino"
            : "Red nacional de estaciones de servicio del Perú"}
        </p>
        <p className="text-sm text-gray-600 mt-2">
          Grafo real con calles del Perú • Algoritmo Dijkstra + OSRM
        </p>
      </div>
    </div>
  );
}