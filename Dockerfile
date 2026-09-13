# SafeShop API - production image for the hosted backend.
FROM python:3.12-slim

WORKDIR /app

# Install only the slim API runtime deps.
COPY deploy/requirements.txt /app/deploy/requirements.txt
RUN pip install --no-cache-dir -r deploy/requirements.txt

# Copy only what the API needs at runtime.
COPY backend /app/backend
COPY ocr_layer /app/ocr_layer
COPY knowledge /app/knowledge
COPY data/catalog.jsonl /app/data/catalog.jsonl

# Hosts (Render/Railway/Cloud Run) inject $PORT; default to 8000 locally.
ENV PORT=8000
ENV SAFESHOP_CATALOG_PATH=/app/data/catalog.jsonl
EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
