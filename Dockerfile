FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi pydantic httpx opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp uvicorn
COPY . .
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live')"
CMD ["uvicorn","service:app","--host","0.0.0.0","--port","8000"]