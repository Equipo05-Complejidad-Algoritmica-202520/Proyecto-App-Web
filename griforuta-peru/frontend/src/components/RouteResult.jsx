// frontend/src/components/RouteResult.jsx (reemplaza todo el archivo)

import { useState } from 'react';

export default function RouteResult({ ruta }) {
  const [expanded, setExpanded] = useState(true);

  if (!ruta || ruta.error) {
    return (
      <div className="mt-10 p-8 bg-red-50 border-2 border-red-300 rounded-xl text-center">
        <p className="text-xl font-bold text-red-700">
          {ruta?.error || "No se encontró ruta"}
        </p>
      </div>
    );
  }

  const { origen, destino, distancia_km, duracion_estimada_min } = ruta;

  // Tiempo realista (55 km/h promedio en Perú)
  const velocidad = 55;
  const horas = Math.floor(distancia_km / velocidad);
  const minutos = Math.round((distancia_km / velocidad - horas) * 60);

  return (
    <div className="mt-10 p-8 bg-gradient-to-br from-amber-50 to-orange-100 rounded-2xl shadow-2xl border-4 border-amber-400">
      <h2 className="text-4xl font-bold text-center text-amber-900 mb-6">
        Grifo Más Cercano Encontrado
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-xl shadow-lg text-center">
          <p className="text-gray-600 text-sm">Distancia por carretera</p>
          <p className="text-4xl font-black text-amber-700 mt-2">
            {distancia_km.toFixed(1)} km
          </p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-lg text-center">
          <p className="text-gray-600 text-sm">Tiempo estimado</p>
          <p className="text-4xl font-black text-green-700 mt-2">
            {horas > 0 ? `${horas}h ${minutos}min` : `${minutos} min`}
          </p>
          <p className="text-xs text-gray-500 mt-1">≈ {velocidad} km/h promedio</p>
        </div>

        <div className="bg-white p-6 rounded-xl shadow-lg text-center">
          <p className="text-gray-600 text-sm">Combustible aproximado</p>
          <p className="text-4xl font-black text-blue-700 mt-2">
            {Math.round(distancia_km / 12)} L
          </p>
          <p className="text-xs text-gray-500">Auto promedio 12 km/L</p>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-inner p-6">
        <div className="flex items-center justify-center gap-8 mb-4">
          <div className="text-center">
            <div className="text-5xl mb-2">Pin</div>
            <p className="font-bold text-green-700">TU UBICACIÓN</p>
          </div>
          <div className="text-6xl text-amber-600">→</div>
          <div className="text-center max-w-md">
            <div className="text-5xl mb-2">Gas Station</div>
            <p className="text-2xl font-bold text-amber-900">
              {destino["RAZON SOCIAL"]}
            </p>
            <p className="text-gray-700 mt-2">
              {destino["DIRECCION OPERATIVA"] || "Dirección no disponible"}
            </p>
            <p className="text-sm text-gray-600">
              {destino.DISTRITO} • {destino.DEPARTAMENTO}
            </p>
          </div>
        </div>

        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full mt-6 py-4 bg-amber-600 hover:bg-amber-700 text-white font-bold text-lg rounded-xl transition shadow-lg"
        >
          {expanded ? "Ocultar detalles" : "Ver más información"}
        </button>

        {expanded && (
          <div className="mt-6 text-sm space-y-amber-800 bg-amber-50 p-4 rounded-lg">
            <p><strong>Coordenadas destino:</strong> {destino.lat.toFixed(5)}, {destino.lng.toFixed(5)}</p>
            <p><strong>Nota:</strong> Ruta calculada con OSRM usando carreteras reales del Perú.</p>
          </div>
        )}
      </div>

      <p className="text-center text-gray-600 mt-6 text-sm">
        Ruta más corta alcanzable por vehículo • Actualizado 2025
      </p>
    </div>
  );
}