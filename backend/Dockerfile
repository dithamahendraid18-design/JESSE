FROM python:3.11-slim

WORKDIR /app

# Install backend package
COPY backend/ /app/backend
COPY clients/ /app/clients
COPY .env.example /app/.env.example

RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir -e /app/backend

ENV PORT=5000
ENV CLIENTS_DIR=/app/clients

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "jesse.app:create_app()"]