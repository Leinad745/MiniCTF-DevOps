# Build

FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim

LABEL org.opencontainers.image.title='mini-ctf' \
      org.opencontainers.image.description="Mini CTF educativo" \
      org.opencontainers.image.version="1.0.0"

# Sin buffer, ni bytecode y a la ruta de la bd sqlite
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    CTF_DB_PATH=/app/data/ctf.db

RUN mkdir -p /app/data && useradd -m -u 1000 appuser && chown -R appuser:appuser /app 

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

COPY --chown=appuser:appuser app/ ./app/

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

