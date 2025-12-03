FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Verificar y generar grafo
RUN test -f data/graph_real.json || (echo "ERROR: graph_real.json no encontrado" && exit 1)
RUN python simplify_graph.py
RUN test -f data/graph_simplified.geojson || (echo "ERROR: No se generó el grafo" && exit 1)

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
