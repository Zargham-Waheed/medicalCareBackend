FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# system deps for psycopg/Postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential libpq-dev curl && \
  rm -rf /var/lib/apt/lists/*

# install python deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy source
COPY ./app /app/app

# Cloud Run listens on $PORT
ENV PORT=8080

# start FastAPI with uvicorn
# IMPORTANT: app.main:app must match the FastAPI instance in app/main.py
CMD exec uvicorn app.main:app --host 0.0.0.0 --port $PORT

