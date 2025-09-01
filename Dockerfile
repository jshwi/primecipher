FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y make git curl

COPY backend ./backend
COPY seeds ./seeds
COPY Makefile pyproject.toml poetry.lock ./
RUN git init --quiet
RUN make .venv/bin/activate

EXPOSE 8000
CMD ["make", "api"]

FROM node:20-alpine AS frontend

WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
ARG NEXT_PUBLIC_API_BASE
ARG NEXT_PUBLIC_REFRESH_TOKEN
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE
ENV NEXT_PUBLIC_REFRESH_TOKEN=$NEXT_PUBLIC_REFRESH_TOKEN
COPY package.json ./
RUN npm install --no-audit --no-fund
COPY . .
RUN npm run build
EXPOSE 3000
