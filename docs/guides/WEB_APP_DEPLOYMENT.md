# JARVIS Web App - Production Deployment Checklist

## Pre-Deployment Checklist

### 1. Environment Configuration ✓

#### Backend
- [ ] All environment variables set in production
- [ ] `SUPABASE_URL` configured
- [ ] `SUPABASE_SERVICE_KEY` configured (service role key, not anon key)
- [ ] `SUPABASE_JWT_SECRET` matches Supabase project
- [ ] `CORS_ORIGINS` includes production frontend URL
- [ ] `GROQ_API_KEY` and other JARVIS keys configured
- [ ] Database connection tested

#### Frontend
- [ ] `NEXT_PUBLIC_SUPABASE_URL` configured
- [ ] `NEXT_PUBLIC_SUPABASE_ANON_KEY` configured (anon key, not service key)
- [ ] `NEXT_PUBLIC_API_URL` points to production backend
- [ ] Build succeeds locally (`npm run build`)
- [ ] No hardcoded localhost URLs

### 2. Database Setup ✓

- [ ] Supabase project created
- [ ] Database migrations executed
- [ ] Tables created: profiles, chats, messages, chat_runs
- [ ] Indexes created
- [ ] RLS policies enabled on all tables
- [ ] RLS policies tested with multiple users
- [ ] Backup strategy configured

### 3. Security Audit ✓

- [ ] JWT secret is strong and unique
- [ ] Service keys never exposed to frontend
- [ ] CORS properly restricted
- [ ] RLS policies prevent cross-user access
- [ ] Input validation on all endpoints
- [ ] Rate limiting configured (recommended)
- [ ] HTTPS enforced in production
- [ ] Secrets not committed to git

### 4. Testing ✓

- [ ] All API endpoints tested
- [ ] Authentication flow tested
- [ ] Chat creation/deletion tested
- [ ] Message send/receive tested
- [ ] User isolation verified
- [ ] Error handling tested
- [ ] Performance benchmarks met
- [ ] Mobile responsiveness tested
- [ ] Cross-browser testing done

### 5. Performance Optimization ✓

- [ ] Frontend build optimized
- [ ] Images optimized (if any)
- [ ] API response times acceptable
- [ ] Database queries optimized
- [ ] Caching strategy implemented
- [ ] CDN configured for static assets

### 6. Monitoring & Logging ✓

- [ ] Backend logging configured
- [ ] Error tracking setup (Sentry, etc.)
- [ ] Performance monitoring setup
- [ ] Database monitoring enabled
- [ ] Uptime monitoring configured
- [ ] Alert thresholds set

---

## Deployment Steps

### Option 1: Vercel (Frontend) + Railway (Backend)

#### Deploy Backend to Railway

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Create New Project**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli

   # Login
   railway login

   # Initialize project
   cd C:\Users\AK\jarvis_project
   railway init
   ```

3. **Configure Environment Variables**
   - Go to Railway dashboard
   - Add all environment variables from `.env`
   - Ensure `CORS_ORIGINS` includes Vercel URL

4. **Deploy**
   ```bash
   railway up
   ```

5. **Get Backend URL**
   - Copy the Railway deployment URL
   - Example: `https://jarvis-backend.railway.app`

#### Deploy Frontend to Vercel

1. **Push to GitHub**
   ```bash
   cd C:\Users\AK\jarvis_project
   git add .
   git commit -m "Add JARVIS web app"
   git push origin main
   ```

2. **Import to Vercel**
   - Go to https://vercel.com
   - Click "Import Project"
   - Select your GitHub repository
   - Set root directory to `web`

3. **Configure Environment Variables**
   - Add `NEXT_PUBLIC_SUPABASE_URL`
   - Add `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - Add `NEXT_PUBLIC_API_URL` (Railway backend URL)

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete

5. **Update CORS**
   - Copy Vercel deployment URL
   - Update `CORS_ORIGINS` in Railway backend
   - Redeploy backend

### Option 2: Docker Deployment

#### Build Docker Images

1. **Backend Dockerfile** (already exists)
   ```dockerfile
   # Already in project root
   # Verify it includes new dependencies
   ```

2. **Frontend Dockerfile**
   ```dockerfile
   # Create web/Dockerfile
   FROM node:18-alpine

   WORKDIR /app

   COPY package*.json ./
   RUN npm ci

   COPY . .
   RUN npm run build

   EXPOSE 3000

   CMD ["npm", "start"]
   ```

3. **Docker Compose**
   ```yaml
   # docker-compose.prod.yml
   version: '3.8'

   services:
     backend:
       build: .
       ports:
         - "8000:8000"
       env_file:
         - .env
       restart: always

     frontend:
       build: ./web
       ports:
         - "3000:3000"
       environment:
         - NEXT_PUBLIC_SUPABASE_URL=${SUPABASE_URL}
         - NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
         - NEXT_PUBLIC_API_URL=http://backend:8000
       depends_on:
         - backend
       restart: always
   ```

4. **Deploy**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Option 3: VPS Deployment (DigitalOcean, AWS, etc.)

1. **Setup Server**
   ```bash
   # SSH into server
   ssh user@your-server-ip

   # Install dependencies
   sudo apt update
   sudo apt install python3 python3-pip nodejs npm nginx
   ```

2. **Clone Repository**
   ```bash
   git clone https://github.com/yourusername/jarvis.git
   cd jarvis
   ```

3. **Setup Backend**
   ```bash
   pip3 install -r requirements.txt

   # Create systemd service
   sudo nano /etc/systemd/system/jarvis-backend.service
   ```

   ```ini
   [Unit]
   Description=JARVIS Backend
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/jarvis
   Environment="PATH=/usr/bin"
   ExecStart=/usr/bin/python3 main.py
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

   ```bash
   sudo systemctl enable jarvis-backend
   sudo systemctl start jarvis-backend
   ```

4. **Setup Frontend**
   ```bash
   cd web
   npm install
   npm run build

   # Use PM2 for process management
   npm install -g pm2
   pm2 start npm --name "jarvis-frontend" -- start
   pm2 save
   pm2 startup
   ```

5. **Configure Nginx**
   ```nginx
   # /etc/nginx/sites-available/jarvis
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }

       location /api {
           proxy_pass http://localhost:8000;
           proxy_http_version 1.1;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

   ```bash
   sudo ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx
   ```

6. **Setup SSL with Let's Encrypt**
   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

## Post-Deployment Checklist

### 1. Verification ✓

- [ ] Frontend loads at production URL
- [ ] Backend health check responds
- [ ] Sign up flow works
- [ ] Sign in flow works
- [ ] Chat creation works
- [ ] Message sending works
- [ ] User isolation verified
- [ ] HTTPS working
- [ ] No console errors

### 2. Performance ✓

- [ ] Page load time < 3s
- [ ] API response time < 2s
- [ ] No memory leaks
- [ ] Database queries optimized
- [ ] CDN serving static assets

### 3. Monitoring ✓

- [ ] Error tracking active
- [ ] Performance monitoring active
- [ ] Uptime monitoring active
- [ ] Logs accessible
- [ ] Alerts configured

### 4. Documentation ✓

- [ ] Production URLs documented
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Team access configured
- [ ] Support contacts listed

---

## Rollback Procedure

### Vercel (Frontend)
1. Go to Vercel dashboard
2. Select deployment
3. Click "Rollback to this deployment"

### Railway (Backend)
1. Go to Railway dashboard
2. Select previous deployment
3. Click "Redeploy"

### Docker
```bash
# Stop current containers
docker-compose down

# Checkout previous version
git checkout <previous-commit>

# Rebuild and restart
docker-compose up -d --build
```

### VPS
```bash
# Stop services
sudo systemctl stop jarvis-backend
pm2 stop jarvis-frontend

# Checkout previous version
git checkout <previous-commit>

# Restart services
sudo systemctl start jarvis-backend
pm2 restart jarvis-frontend
```

---

## Maintenance Tasks

### Daily
- [ ] Check error logs
- [ ] Monitor uptime
- [ ] Review performance metrics

### Weekly
- [ ] Database backup verification
- [ ] Security updates
- [ ] Performance optimization review

### Monthly
- [ ] Dependency updates
- [ ] Security audit
- [ ] Cost optimization review
- [ ] User feedback review

---

## Scaling Considerations

### When to Scale

- Response time > 3s consistently
- CPU usage > 80% sustained
- Memory usage > 80% sustained
- Database connections maxed out
- User complaints about performance

### Scaling Options

1. **Vertical Scaling**
   - Upgrade server resources
   - Increase database tier

2. **Horizontal Scaling**
   - Add more backend instances
   - Load balancer configuration
   - Database read replicas

3. **Caching**
   - Redis for session storage
   - CDN for static assets
   - API response caching

4. **Database Optimization**
   - Add indexes
   - Query optimization
   - Connection pooling
   - Read replicas

---

## Cost Estimates

### Vercel + Railway + Supabase

| Service | Tier | Cost/Month |
|---------|------|------------|
| Vercel | Hobby | $0 |
| Railway | Starter | $5 |
| Supabase | Free | $0 |
| **Total** | | **$5/month** |

### Production Scale

| Service | Tier | Cost/Month |
|---------|------|------------|
| Vercel | Pro | $20 |
| Railway | Pro | $20 |
| Supabase | Pro | $25 |
| **Total** | | **$65/month** |

---

## Support & Troubleshooting

### Common Production Issues

1. **502 Bad Gateway**
   - Backend not running
   - Check Railway/server logs
   - Verify environment variables

2. **CORS Errors**
   - Update CORS_ORIGINS
   - Redeploy backend
   - Clear browser cache

3. **Auth Failures**
   - Check JWT secret
   - Verify Supabase configuration
   - Check token expiration

4. **Slow Performance**
   - Check database queries
   - Review API response times
   - Check server resources

### Getting Help

- Check logs first
- Review documentation
- Search GitHub issues
- Contact support

---

## Success Criteria

- [ ] ✅ Application accessible at production URL
- [ ] ✅ All features working as expected
- [ ] ✅ Performance targets met
- [ ] ✅ Security audit passed
- [ ] ✅ Monitoring active
- [ ] ✅ Team trained on deployment
- [ ] ✅ Documentation complete
- [ ] ✅ Backup strategy in place

---

**Deployment Date**: _____________
**Deployed By**: _____________
**Production URL**: _____________
**Status**: ⬜ Ready | ⬜ In Progress | ⬜ Complete
