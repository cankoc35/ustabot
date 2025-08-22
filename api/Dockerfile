# api/Dockerfile
FROM python:3.11-slim

# System deps (only what you actually need)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Optional: make these overridable at runtime via compose
ENV OLLAMA_HOST=http://ollama:11434 \
    PYTHONUNBUFFERED=1 \
    UVICORN_WORKERS=1

# Expose port (docs only)
EXPOSE 8000

# Start the API (adjust module path if your app is at api/app.py)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
