# ── Stage 1: Build frontend ───────────────────────────────────────────────────
FROM node:20-alpine AS frontend
WORKDIR /build
COPY dashboard/package.json dashboard/package-lock.json* ./
RUN npm install
COPY dashboard/ .
RUN npm run build

# ── Stage 2: Python runtime ───────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App source
COPY . .

# Built frontend
COPY --from=frontend /build/dist ./dashboard/dist

# Workspace volume mount point
RUN mkdir -p /app/workspace

EXPOSE 8000

CMD ["python", "main.py", "--web", "--host", "0.0.0.0", "--port", "8000"]
