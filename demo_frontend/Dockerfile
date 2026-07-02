FROM python:3.14-slim

WORKDIR /app

# Create a non-root user first
RUN useradd -u 1000 -m appuser

# Install deps before copying code (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY main.py .

# Drop to non-root
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]