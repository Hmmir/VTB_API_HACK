FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    sqlalchemy==2.0.23 \
    psycopg2-binary==2.9.9 \
    pydantic==2.5.0 \
    python-multipart==0.0.6 \
    PyJWT==2.8.0

# Copy application
COPY main.py .

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

