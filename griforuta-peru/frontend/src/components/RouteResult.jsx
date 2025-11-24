// frontend/src/components/RouteResult.jsx
import { useState } from 'react';

export default function RouteResult({ ruta }) {
  const [expanded, setExpanded] = useState(false);

  if (!ruta) return null;

  const {
    origen,
    destino,
    distancia_km,
    duracion_estimada_min,
    ruta: estacionesRuta
  } = ruta;

  // Tiempo promedio realista: 55 km/h en carretera peruana
  const velocidadPromedio = 55; // km/h
  const tiempoHoras = distancia_km / velocidadPromedio;
  const horas = Math.floor(tiempoHoras);
  const minutos = Math.round((tiempoHoras - horas) * 60);

  return (
    <div className="mt-6 p-5 bg-gradient-to-br from-blue-50 to-indigo-100 rounded-xl shadow-lg border border-blue-200">
      <h3 className="text-2xl font-bold text-indigo-800 mb-4">
        Ruta Más Corta Encontrada
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-5">
        <div className="bg-white p-4 rounded-lg shadow text-center">
          <p className="text-sm text-gray-600">Distancia Total</p>
          <p className="text-3xl font-bold text-blue-700">
            {distancia_km.toFixed(1)} km
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow text-center">
          <p className="text-sm text-gray-600">Tiempo Estimado</p>
          <p className="text-3xl font-bold text-green-700">
            {horas > 0 ? `${horas}h ${minutos}min` : `${minutos} min`}
          </p>
          <p className="text-xs text-gray-500 mt-1">≈ {velocidadPromedio} km/h promedio</p>
        </div>

        <div className="bg-white p-4 rounded-lg shadow text-center">
          <p className="text-sm text-gray-600">Estaciones en Ruta</p>
          <p className="text-3xl font-bold text-purple-700">
            {estacionesRuta.length}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <div>
          <span className="text-sm font-semibold text-gray-700">Origen:</span>
          <p className="font-medium text-indigo-900">
            {origen["RAZON SOCIAL"] || "Estación sin nombre"}
          </p>
          <p className="text-xs text-gray-600">
            {origen.DISTRITO}, {origen.DEPARTAMENTO}
          </p>
        </div>
        <div className="text-3xl text-indigo-600">→</div>
        <div className="text-right">
          <span className="text-sm font-semibold text-gray-700">Destino:</span>
          <p className="font-medium text-indigo-900">
            {destino["RAZON SOCIAL"] || "Estación sin nombre"}
          </p>
          <p className="text-xs text-gray-600">
            {destino.DISTRITO}, {destino.DEPARTAMENTO}
          </p>
        </div>
      </div>

      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full mt-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg transition shadow-md"
      >
        {expanded ? "Ocultar" : "Mostrar"} todos los {estacionesRuta.length} grifos de la ruta
      </button>

      {expanded && (
        <div className="mt-4 max-h-96 overflow-y-auto bg-white rounded-lg shadow-inner">
          <ol className="divide-y divide-gray-200">
            {estacionesRuta.map((station, index) => (
              <li
                key={station.id}
                className={`p-4 hover:bg-gray-50 transition ${
                  index === 0 || index === estacionesRuta.length - 1
                    ? "bg-gradient-to-r from-green-50 to-green-100 font-semibold"
                    : ""
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <span className="text-lg font-medium text-gray-900">
                      {index + 1}. {station["RAZON SOCIAL"] || "Grifo sin razón social"}
                    </span>
                    <p className="text-sm text-gray-600">
                      {station["DIRECCION OPERATIVA"] || "Dirección no disponible"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {station.DISTRITO}, {station.PROVINCIA} - {station.DEPARTAMENTO}
                    </p>
                  </div>
                  {index === 0 && <span className="ml-4 px-3 py-1 bg-green-600 text-white text-xs rounded-full">INICIO</span>}
                  {index === estacionesRuta.length - 1 && <span className="ml-4 px-3 py-1 bg-red-600 text-white text-xs rounded-full">FIN</span>}
                </div>
              </li>
            ))}
          </ol>
        </div>
      )}

      <p className="text-xs text-gray-500 text-center mt-5">
        Ruta calculada con Dijkstra sobre grafo completo de {estacionesRuta.length} estaciones reales del Perú.
      </p>
    </div>
  );
}