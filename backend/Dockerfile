FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y make git curl

COPY app ./app
COPY seeds ./seeds
COPY Makefile pyproject.toml poetry.lock ./
RUN make .venv/bin/activate

EXPOSE 8000
CMD ["make", "api"]
