# JARVIS v9.0 ULTRA - Docker Configuration
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for WhatsApp integration
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
COPY package.json .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node dependencies
RUN npm install

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs data state whatsapp_session

# Expose ports
EXPOSE 8000 3002 50051

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=info

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["python", "main.py"]
