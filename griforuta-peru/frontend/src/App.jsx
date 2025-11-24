// frontend/src/App.jsx
import { useState } from 'react';
import SearchBox from './components/SearchBox';
import RouteResult from './components/RouteResult';
import Map from './components/Map';

function App() {
  const [origen, setOrigen] = useState(null);
  const [destino, setDestino] = useState(null);
  const [ruta, setRuta] = useState(null);
  const [loading, setLoading] = useState(false);

  const buscarRuta = async () => {
    if (!origen || !destino) return;
    setLoading(true);
    const res = await fetch(
      `http://localhost:8000/ruta?start=${origen.id}&end=${destino.id}`
    );
    const data = await res.json();
    setRuta(data);
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-cyan-100">
      <div className="container mx-auto p-6">
        <h1 className="text-5xl font-bold text-center mb-2 text-indigo-800">
          GrifoRuta Perú
        </h1>
        <p className="text-center text-gray-700 mb-8 text-lg">
          Ruta óptima entre estaciones de servicio usando Dijkstra + OSRM
        </p>

        <div className="max-w-5xl mx-auto bg-white rounded-2xl shadow-2xl p-8">
          {/* Buscadores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            <SearchBox label="Origen" onSelect={setOrigen} selected={origen} />
            <SearchBox label="Destino" onSelect={setDestino} selected={destino} />
          </div>

          {/* Botón centrado */}
          <div className="text-center mb-10">
            <button
              onClick={buscarRuta}
              disabled={!origen || !destino || loading}
              className="px-12 py-5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold text-xl rounded-full shadow-2xl hover:shadow-3xl transform hover:scale-105 transition disabled:opacity-50"
            >
              {loading ? "Calculando ruta real..." : "Buscar Ruta Más Corta"}
            </button>
          </div>

          {/* MAPA SIEMPRE VISIBLE (grafo completo) */}
          <div className="mb-10">
            <Map ruta={ruta} /> {/* ← AQUÍ ESTÁ EL SECRETO */}
          </div>

          {/* Resultado solo cuando hay ruta */}
          {ruta && (
            <div className="mt-10">
              <RouteResult ruta={ruta} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;