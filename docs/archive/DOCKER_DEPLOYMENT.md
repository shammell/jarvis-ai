# JARVIS v9.0 ULTRA - Docker Deployment Guide

## Mert Desktop Par Deploy Karne Ke Liye

### Prerequisites
- Docker Desktop installed on Mert's computer
- Git (optional, for cloning)

### Step 1: Project Transfer
```bash
# Option 1: Copy entire jarvis_project folder to Mert's desktop
# Option 2: Use Git to clone/push

# Copy to Mert's desktop
scp -r jarvis_project/ mert@desktop:/path/to/destination/
```

### Step 2: Environment Setup
```bash
cd jarvis_project

# Copy environment template
cp .env.example .env

# Edit .env file and add your API keys
nano .env  # or use any text editor
```

### Step 3: Build and Run
```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### Step 4: Verify Deployment
```bash
# Check logs
docker-compose logs -f jarvis

# Test API
curl http://localhost:8000/health

# Test WhatsApp Bridge
curl http://localhost:3002/api/whatsapp/status
```

### Services Running
- **JARVIS Main API**: http://localhost:8000
- **WhatsApp Bridge**: http://localhost:3002
- **gRPC Service**: localhost:50051
- **Redis**: localhost:6379

### Management Commands
```bash
# Stop services
docker-compose stop

# Start services
docker-compose start

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v
```

### Urdu/Hindi Instructions

**Mert ke desktop par deploy karne ke liye:**

1. **Docker Desktop install karo** (agar nahi hai)

2. **JARVIS folder copy karo** Mert ke computer par

3. **Environment file setup karo:**
   ```bash
   cd jarvis_project
   cp .env.example .env
   # .env file mein apni API keys dalo
   ```

4. **Docker start karo:**
   ```bash
   docker-compose up -d
   ```

5. **Check karo:**
   - Browser mein jao: http://localhost:8000/docs
   - WhatsApp: http://localhost:3002

**Bas! JARVIS ab Mert ke desktop par chal raha hai!**

### Troubleshooting

**Port already in use:**
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

**Container not starting:**
```bash
# Check logs
docker-compose logs jarvis

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

**API key missing:**
```bash
# Edit .env file
nano .env
# Add: GROQ_API_KEY=your_key_here
docker-compose restart
```

### Remote Access Setup

**Agar aap apne laptop se Mert ke desktop ko access karna chahte ho:**

1. **Mert ke desktop par:**
   ```bash
   # Find IP address
   ipconfig  # Windows
   ifconfig  # Linux/Mac
   ```

2. **Apne laptop se:**
   ```bash
   # Access JARVIS
   curl http://mert-desktop-ip:8000/health
   
   # Browser mein
   http://mert-desktop-ip:8000/docs
   ```

### System Requirements
- RAM: 4GB minimum, 8GB recommended
- Storage: 10GB free space
- CPU: 2 cores minimum, 4 cores recommended
- Network: Internet connection for API calls

### Backup
```bash
# Backup data
docker-compose exec jarvis tar -czf /app/backup.tar.gz /app/data /app/state

# Copy backup
docker cp jarvis-v9-ultra:/app/backup.tar.gz ./backup.tar.gz
```

### Updates
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

## Support
- Check logs: `docker-compose logs -f`
- Restart: `docker-compose restart`
- Full reset: `docker-compose down -v && docker-compose up -d`
