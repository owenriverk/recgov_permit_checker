FROM python:3.11-slim

WORKDIR /app

COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pandas requests python-dotenv sqlalchemy psycopg2-binary

# Install supervisor
RUN apt-get update && apt-get install -y supervisor

# Copy supervisor config
COPY supervisord.conf /etc/supervisord.conf

# Expose FastAPI port
EXPOSE 8000

# Start both the API and scanner
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
