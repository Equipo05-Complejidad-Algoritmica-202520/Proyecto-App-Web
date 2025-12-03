// frontend/src/App.jsx (versión final – copia y pega)

import { useState } from 'react';
import Map from './components/Map';
import RouteResult from './components/RouteResult';

function App() {
  const [userLocation, setUserLocation] = useState(null);
  const [rutaCercana, setRutaCercana] = useState(null);
  const [loading, setLoading] = useState(false);

  const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

  const buscarGrifoCercano = async () => {
    if (!userLocation) {
      alert("Haz clic en el mapa para seleccionar tu ubicación");
      return;
    }

    setLoading(true);
    try {
      const res = await fetch(
        `${API_URL}/grifo_cercano?lat=${userLocation.lat}&lng=${userLocation.lng}`
      );
      const data = await res.json();
      setRutaCercana(data);
    } catch (err) {
      alert("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-100">
      <div className="container mx-auto p-6 max-w-7xl">
        <h1 className="text-5xl font-bold text-center mb-3 text-indigo-800">
          GrifoRuta Perú
        </h1>
        <p className="text-center text-xl text-gray-700 mb-10">
          Haz clic en el mapa → Encuentra el grifo más cercano por carretera real
        </p>

        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* Botón grande */}
          <div className="p-8 text-center bg-gradient-to-r from-amber-500 to-orange-600">
            <button
              onClick={buscarGrifoCercano}
              disabled={loading || !userLocation}
              className="px-16 py-7 bg-white text-amber-700 font-black text-3xl rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-105 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Buscando el grifo más cercano..." : "Buscar Grifo Más Cercano"}
            </button>
          </div>

          {/* Info de ubicación seleccionada */}
          {userLocation && (
            <div className="p-4 bg-green-100 text-center font-medium">
              Ubicación seleccionada: {userLocation.lat.toFixed(5)}, {userLocation.lng.toFixed(5)}
              <button
                onClick={() => setUserLocation(null) || setRutaCercana(null)}
                className="ml-4 text-red-600 underline"
              >
                Cambiar
              </button>
            </div>
          )}

          {/* Mapa */}
          <Map userLocation={userLocation} setUserLocation={setUserLocation} rutaCercana={rutaCercana} />

          {/* Resumen debajo del mapa (¡igual que antes!) */}
          <div className="p-8">
            <RouteResult ruta={rutaCercana} />
          </div>
        </div>

        <p className="text-center text-gray-500 mt-8 text-sm">
          Grafo nacional real • Dijkstra + OSRM • 2025
        </p>
      </div>
    </div>
  );
}

export default App;