# Pension Case System - single image serving the API and the web interface.
#
#   docker build -t pension-case .
#   docker run -d -p 80:8000 -v pension-data:/data --name pension pension-case
#
# LibreOffice makes the PDFs in place of Word, so the image carries it along with
# Liberation Serif (metric-compatible with Times New Roman) and a Devanagari face.

# ---------------------------------------------------------------- web build
FROM node:20-slim AS web
WORKDIR /build/frontend
COPY frontend/package*.json ./
RUN npm ci --silent
COPY frontend/ ./
RUN npm run build

# ---------------------------------------------------------------- runtime
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PENSION_DB=/data/pension.db \
    PENSION_STORAGE=/data/storage \
    PENSION_SECRET=/data/.secret \
    PENSION_FRONTEND=/app/frontend/dist \
    PENSION_FONT_LATIN="Liberation Serif" \
    PENSION_FONT_DEVANAGARI="Noto Sans Devanagari" \
    HOME=/data

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
        libreoffice-writer \
        fonts-liberation fonts-noto-core fonts-noto-devanagari fonts-lohit-deva \
        fontconfig \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/backend/
COPY --from=web /build/frontend/dist /app/frontend/dist

# Build the .docx templates with the fonts installed above.
RUN python build_templates.py

RUN useradd --system --create-home pension && mkdir -p /data && chown -R pension /data /app
USER pension
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
