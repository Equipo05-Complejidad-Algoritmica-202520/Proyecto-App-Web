// frontend/src/components/Map.jsx
import { MapContainer, TileLayer, GeoJSON, Polyline, CircleMarker, Popup, useMapEvents } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';

// Componente que detecta el clic y llama a setUserLocation
function ClickHandler({ setUserLocation }) {
  useMapEvents({
    click(e) {
      setUserLocation({
        lat: e.latlng.lat,
        lng: e.latlng.lng
      });
    }
  });
  return null;
}

export default function Map({ userLocation, setUserLocation, rutaCercana }) {
  const [stations, setStations] = useState([]);
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  useEffect(() => {
    // Cargar grafo desde backend
    fetch(`${API_URL}/graph/simplified`)
      .then(res => res.json())
      .then(data => {
        setGraphData(data);
        // Agregar al mapa con Leaflet
        L.geoJSON(data, {
          style: feature => feature.properties
        }).addTo(map);
      })
      .catch(err => console.error('Error cargando grafo:', err));
  }, []);

  const center = userLocation || [-12.0, -77.0];

  return (
    <div className="mt-8 rounded-xl overflow-hidden shadow-2xl border-4 border-indigo-600 relative">
      <MapContainer center={center} zoom={userLocation ? 14 : 6} style={{ height: '680px', width: '100%' }}>
        {/* Aquí pasamos correctamente la función */}
        <ClickHandler setUserLocation={setUserLocation} />

        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />

        {/* Grafo nacional de fondo */}
        {graphData && (
          <GeoJSON
            data={graphData}
            style={() => ({
              color: "#389dfc",
              weight: 3,
              opacity: 0.7
            })}
          />
        )}

        {/* Ruta al grifo más cercano */}
        {rutaCercana?.polyline && (
          <Polyline
            positions={rutaCercana.polyline}
            color="#ef4444"
            weight={9}
            opacity={1}
            dashArray="12, 12"
          />
        )}

        {/* Marcador de TU UBICACIÓN */}
        {userLocation && (
          <CircleMarker
            center={[userLocation.lat, userLocation.lng]}
            radius={15}
            fillColor="#10b981"
            color="#fff"
            weight={5}
            fillOpacity={1}
          >
            <Popup>Tú estás aquí</Popup>
          </CircleMarker>
        )}

        {/* Grifo más cercano */}
        {rutaCercana?.destino && (
          <CircleMarker
            center={[rutaCercana.destino.lat, rutaCercana.destino.lng]}
            radius={16}
            fillColor="#f59e0b"
            color="#fff"
            weight={6}
            fillOpacity={1}
          >
            <Popup>
              <strong className="text-lg">GRIFO MÁS CERCANO</strong><br />
              {rutaCercana.destino["RAZON SOCIAL"]}<br />
              {rutaCercana.distancia_km.toFixed(1)} km
            </Popup>
          </CircleMarker>
        )}

        {/* Todos los grifos (fondo) */}
        {stations.map(s => (
          <CircleMarker
            key={s.id}
            center={[s.lat, s.lng]}
            radius={5}
            fillColor="#64748b"
            color="#fff"
            weight={1}
            fillOpacity={0.7}
          />
        ))}
      </MapContainer>

      {/* Texto flotante con tu ubicación */}
      {userLocation && (
        <div className="absolute top-4 left-4 bg-white/95 p-4 rounded-lg shadow-2xl z-10 text-sm font-medium backdrop-blur">
          <strong>Tu ubicación:</strong><br />
          {userLocation.lat.toFixed(5)}, {userLocation.lng.toFixed(5)}
        </div>
      )}

      {loading && (
        <div className="absolute inset-0 bg-white/90 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-16 w-16 border-8 border-indigo-600 border-t-transparent mb-4"></div>
            <p className="text-xl font-bold">Cargando red nacional de grifos...</p>
          </div>
        </div>
      )}
    </div>
  );
}