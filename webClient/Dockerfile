# Multi-stage build for webClient (unified API + Frontend)

# Stage 1: Build React frontend
FROM node:20-bookworm-slim@sha256:1e85773c98c31d4fe5b545e4cb17379e617b348832fb3738b22a08f68dec30f3 AS frontend-builder

WORKDIR /app/webClient/frontend

COPY webClient/frontend/package*.json webClient/frontend/.npmrc ./

# npm_token secret used for GitHub Packages auth (@penguintechinc scope)
RUN --mount=type=secret,id=npm_token \
    NPM_TOKEN=$(cat /run/secrets/npm_token) npm ci

COPY webClient/frontend/ ./
RUN npm run build

# Stage 2: Build Python API with embedded frontend
FROM python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && groupadd -g 1000 waddleperf \
    && useradd -m -u 1000 -g waddleperf waddleperf \
    && rm -rf /var/lib/apt/lists/*

COPY webClient/api/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY webClient/api/ ./
COPY --from=frontend-builder /app/webClient/frontend/dist ./static/

RUN chown -R waddleperf:waddleperf /app
USER waddleperf

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

ENV PORT=5000 \
    WORKERS=4 \
    WORKER_CLASS=eventlet \
    TIMEOUT=120 \
    LOG_LEVEL=info

CMD gunicorn --bind 0.0.0.0:${PORT} --workers ${WORKERS} --worker-class ${WORKER_CLASS} --timeout ${TIMEOUT} --log-level ${LOG_LEVEL} "app:app"
