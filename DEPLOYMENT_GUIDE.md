# JARVIS v9.0 Deployment Guide

**Version:** 9.0.0  
**Date:** 2026-04-20  
**Status:** Production-Ready

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/[username]/jarvis-v9.git
cd jarvis-v9
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
npm install  # For WhatsApp bridge
```

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Run System
```bash
python main.py
```

---

## Environment Variables

Create `.env` file:

```bash
# Required
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=your_jwt_secret_here
ADMIN_PASSWORD=your_admin_password_here

# Optional
OPENAI_API_KEY=your_openai_api_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info
MAX_CONCURRENT_REQUESTS=100
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3
AUTONOMOUS_MODE=false
```

---

## Architecture Overview

```
JARVIS v9.0 Architecture
├── Entry Point (main.py - 102 lines)
├── Core Orchestrator (core/orchestrator.py - 261 lines)
├── API Layer (core/api/routes.py - 171 lines)
├── Performance Layer
│   ├── Lazy Loader (core/lazy_loader.py)
│   └── Multi-Tier Cache (core/cache.py)
├── Reliability Layer
│   ├── Circuit Breaker (core/circuit_breaker.py)
│   └── Retry Logic (core/retry.py)
├── Observability Layer
│   ├── Structured Logging (core/structured_logging.py)
│   └── Metrics (core/metrics.py)
└── Configuration (core/config.py)
```

---

## Deployment Options

### Option 1: Local Development
```bash
python main.py
```
Access: http://localhost:8000

### Option 2: Docker Container
```bash
docker build -t jarvis-v9 .
docker run -p 8000:8000 --env-file .env jarvis-v9
```

### Option 3: Docker Compose
```bash
docker-compose up -d
```

### Option 4: Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Option 5: Cloud Platforms

**AWS:**
```bash
# Elastic Beanstalk
eb init -p python-3.11 jarvis-v9
eb create jarvis-v9-prod
eb deploy
```

**Google Cloud:**
```bash
gcloud app deploy
```

**Azure:**
```bash
az webapp up --name jarvis-v9 --runtime "PYTHON:3.11"
```

---

## Performance Tuning

### Redis Configuration
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

### Gunicorn (Production)
```bash
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120 \
  --keep-alive 5
```

### Nginx Reverse Proxy
```nginx
upstream jarvis {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name jarvis.example.com;

    location / {
        proxy_pass http://jarvis;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Monitoring

### Health Check
```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "9.0.0",
  "uptime_seconds": 3600,
  "total_requests": 1234,
  "cache_hit_rate": 0.87
}
```

### Metrics Endpoint
```bash
curl http://localhost:8000/metrics
```

### Prometheus Integration
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'jarvis'
    static_configs:
      - targets: ['localhost:8000']
```

### Grafana Dashboard
Import dashboard from `monitoring/grafana-dashboard.json`

---

## Scaling

### Horizontal Scaling
```bash
# Run multiple instances behind load balancer
python main.py --port 8001 &
python main.py --port 8002 &
python main.py --port 8003 &
```

### Load Balancer (HAProxy)
```
frontend jarvis_frontend
    bind *:80
    default_backend jarvis_backend

backend jarvis_backend
    balance roundrobin
    server jarvis1 127.0.0.1:8001 check
    server jarvis2 127.0.0.1:8002 check
    server jarvis3 127.0.0.1:8003 check
```

---

## Security

### JWT Configuration
```python
# Rotate JWT secret regularly
JWT_SECRET=<generate-with-openssl-rand-hex-32>
JWT_ALGORITHM=HS256
JWT_ACCESS_EXPIRATION=1800  # 30 minutes
```

### HTTPS Setup
```bash
# Let's Encrypt
certbot --nginx -d jarvis.example.com
```

### Rate Limiting
```python
# Already configured in core/api/routes.py
# Default: 100 requests per minute per IP
```

---

## Backup & Recovery

### Database Backup
```bash
# Redis backup
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/redis-$(date +%Y%m%d).rdb
```

### State Backup
```bash
# Backup persistent state
tar -czf jarvis-state-$(date +%Y%m%d).tar.gz data/ logs/
```

### Disaster Recovery
```bash
# Restore from backup
tar -xzf jarvis-state-20260420.tar.gz
redis-cli FLUSHALL
redis-cli --pipe < backup/redis-20260420.rdb
python main.py
```

---

## Troubleshooting

### Issue: Startup Fails
```bash
# Check logs
tail -f logs/jarvis.log

# Verify environment
python -c "from core.config import settings; print(settings)"

# Test Redis connection
redis-cli ping
```

### Issue: High Memory Usage
```bash
# Check cache size
redis-cli INFO memory

# Clear cache
redis-cli FLUSHDB

# Restart with lower cache limit
export MAX_CACHE_SIZE=500
python main.py
```

### Issue: Slow Response Times
```bash
# Enable debug logging
export LOG_LEVEL=debug
python main.py

# Check circuit breaker status
curl http://localhost:8000/api/system/status

# Monitor metrics
curl http://localhost:8000/metrics
```

---

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suite
```bash
pytest tests/test_phd_modules.py -v
```

### Coverage Report
```bash
pytest --cov=core --cov-report=html
open htmlcov/index.html
```

### Load Testing
```bash
# Using Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Using wrk
wrk -t4 -c100 -d30s http://localhost:8000/api/message
```

---

## Maintenance

### Update Dependencies
```bash
pip install --upgrade -r requirements.txt
npm update
```

### Rotate Secrets
```bash
# Generate new JWT secret
openssl rand -hex 32

# Update .env
# Restart service
```

### Clean Logs
```bash
# Rotate logs (automatic with logrotate)
find logs/ -name "*.log" -mtime +30 -delete
```

---

## Support

**Documentation:** https://jarvis-v9.readthedocs.io  
**Issues:** https://github.com/[username]/jarvis-v9/issues  
**Email:** support@jarvis-v9.com

---

**Last Updated:** 2026-04-20  
**Maintainer:** JARVIS Development Team
