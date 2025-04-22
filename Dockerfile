FROM python:3.11-slim

WORKDIR /app

COPY . .

# Install dependencies
RUN pip install --no-cache-dir fastapi uvicorn pandas requests python-dotenv

# This will be overridden by docker-compose for each service
CMD ["python", "Main.py"]
