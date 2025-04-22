FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir fastapi uvicorn pandas requests python-dotenv sqlalchemy psycopg2-binary

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]

# Install supervisor
RUN apt-get update && apt-get install -y supervisor

# Copy the config
COPY supervisord.conf /etc/supervisord.conf

# Final command
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
