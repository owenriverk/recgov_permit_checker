FROM python:3.11-slim

WORKDIR /app

COPY . .


RUN pip install --no-cache-dir fastapi uvicorn pandas requests python-dotenv sqlalchemy

# This will be overridden by docker-compose for each service
EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]