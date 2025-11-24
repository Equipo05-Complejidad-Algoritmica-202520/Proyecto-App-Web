import { useState } from 'react';

export default function SearchBox({ label, onSelect, selected }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);

  const search = async () => {
    if (query.length < 3) {
      setResults([]);
      return;
    }
    const res = await fetch(`http://localhost:8000/search?q=${query}`);
    const data = await res.json();
    setResults(data.results);
    setOpen(true);
  };

  return (
    <div className="relative">
      <label className="block text-sm font-bold mb-2">{label}</label>
      <input
        type="text"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          search();
        }}
        placeholder="Ej: Repsol, Primax, Pecsa, Lima..."
        className="w-full px-4 py-3 border rounded-lg"
      />
      {selected && (
        <div className="mt-2 p-3 bg-green-100 rounded">
          {selected["RAZON SOCIAL"]} - {selected.DISTRITO}
        </div>
      )}
      {open && results.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-64 overflow-y-auto">
          {results.map((s) => (
            <div
              key={s.id}
              className="p-3 hover:bg-gray-100 cursor-pointer border-b"
              onClick={() => {
                onSelect(s);
                setQuery(`${s["RAZON SOCIAL"].slice(0, 30)}...`);
                setOpen(false);
              }}
            >
              <strong>{s["RAZON SOCIAL"]}</strong><br />
              <small>{s["DIRECCION OPERATIVA"]} - {s.DISTRITO}, {s.DEPARTAMENTO}</small>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}