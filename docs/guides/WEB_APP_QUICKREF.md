# JARVIS Web App - Quick Reference

## 🚀 Quick Start

```bash
# Setup (first time only)
./setup_webapp.sh          # Linux/Mac
.\setup_webapp.ps1         # Windows

# Start both services
./start_webapp.sh          # Linux/Mac
.\start_webapp.ps1         # Windows

# Or start manually:
python main.py             # Terminal 1 (Backend)
cd web && npm run dev      # Terminal 2 (Frontend)
```

## 🌐 URLs

- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📁 Project Structure

```
jarvis_project/
├── api/                    # New chat API
│   ├── routers/chat.py    # Endpoints
│   ├── services/          # Business logic
│   ├── repositories/      # Data access
│   ├── schemas/           # Pydantic models
│   └── auth.py            # JWT verification
├── web/                   # Next.js frontend
│   ├── app/               # Pages
│   ├── components/        # React components
│   └── lib/               # API client
├── supabase/migrations/   # Database schema
└── main.py                # FastAPI app
```

## 🔑 Environment Variables

### Backend (.env)
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJxxx...
SUPABASE_JWT_SECRET=your-jwt-secret
CORS_ORIGINS=http://localhost:3000
```

### Frontend (web/.env.local)
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🔌 API Endpoints

### Chat API (v1) - Requires Auth
```
POST   /api/v1/chats                    Create chat
GET    /api/v1/chats                    List chats
GET    /api/v1/chats/{id}/messages      Get messages
POST   /api/v1/chats/{id}/messages      Send message
POST   /api/v1/chats/{id}/stream        Stream response
DELETE /api/v1/chats/{id}               Archive chat
```

### Legacy API - Backward Compatible
```
POST   /api/message                     Process message
POST   /api/agent-team                  Agent team execution
GET    /api/stats                       System stats
GET    /health                          Health check
```

## 🧪 Quick Tests

```bash
# Health check
curl http://localhost:8000/health

# Create chat (with auth)
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Chat"}'

# Legacy API (no auth)
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello JARVIS"}'
```

## 🗄️ Database Schema

```sql
profiles (id, display_name, created_at)
chats (id, user_id, title, created_at, updated_at, archived)
messages (id, chat_id, user_id, role, content, metadata, created_at)
chat_runs (id, chat_id, message_id, model_source, latency_ms, success)
```

## 🔒 Security Features

- ✅ JWT authentication on all chat endpoints
- ✅ Row Level Security (RLS) in database
- ✅ User data isolation
- ✅ CORS restrictions
- ✅ Input validation
- ✅ Secure password hashing (Supabase)

## 🛠️ Common Commands

```bash
# Backend
pip install -r requirements.txt    # Install deps
python main.py                     # Start server
python -m pytest                   # Run tests

# Frontend
cd web
npm install                        # Install deps
npm run dev                        # Development
npm run build                      # Production build
npm run start                      # Production server
npm run lint                       # Lint code

# Database
# Run migrations in Supabase SQL Editor:
# supabase/migrations/20260309_create_chat_tables.sql
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend won't start | Check .env has all Supabase credentials |
| Frontend can't connect | Verify NEXT_PUBLIC_API_URL is correct |
| Auth fails | Check JWT secret matches Supabase |
| No messages appear | Check browser console, verify token |
| Database error | Run migrations, check RLS policies |

## 📊 Performance Targets

| Operation | Target |
|-----------|--------|
| Sign In | < 500ms |
| Create Chat | < 200ms |
| Send Message | < 2s |
| Load Messages | < 300ms |

## 🎯 Key Features

### Frontend
- Multi-user authentication
- Chat thread management
- Real-time messaging
- Message history
- Responsive UI
- Metadata display

### Backend
- JWT authentication
- Conversation persistence
- JARVIS intelligence integration
- User data isolation
- Backward compatibility
- SSE streaming

## 📝 User Flow

1. **Sign Up** → Create account with email/password
2. **Sign In** → Authenticate and get JWT token
3. **Create Chat** → Start new conversation thread
4. **Send Message** → Type and send to JARVIS
5. **Get Response** → JARVIS processes and responds
6. **Switch Chats** → Navigate between conversations
7. **Sign Out** → End session

## 🔗 Important Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app with chat router |
| `api/routers/chat.py` | Chat API endpoints |
| `api/services/chat_service.py` | Business logic |
| `api/auth.py` | JWT verification |
| `web/app/chat/page.tsx` | Main chat UI |
| `web/lib/api.ts` | API client |
| `supabase/migrations/*.sql` | Database schema |

## 📚 Documentation

- `WEB_APP_README.md` - Complete setup guide
- `WEB_APP_IMPLEMENTATION.md` - Implementation details
- `WEB_APP_ARCHITECTURE.md` - System architecture
- `WEB_APP_TESTING.md` - Testing guide

## 🚢 Deployment

### Frontend (Vercel)
1. Push to GitHub
2. Import in Vercel
3. Set env vars
4. Deploy

### Backend (Railway/Render)
1. Use Docker or direct deploy
2. Set env vars
3. Deploy

### Database (Supabase)
- Already hosted
- Run migrations
- Configure RLS

## 💡 Tips

- Use browser DevTools to inspect JWT tokens
- Check `logs/jarvis_v9.log` for backend errors
- Use Supabase dashboard to view database
- Test with curl before frontend testing
- Keep JWT secret secure and never commit it

## 🎨 UI Components

```
ChatPage
├── ChatSidebar
│   ├── New Chat Button
│   ├── Chat List
│   └── Sign Out Button
├── ChatTimeline
│   └── Message Bubbles
└── ChatComposer
    ├── Textarea Input
    └── Send Button
```

## 🔄 Data Flow

```
User Input → Frontend → API Client → Backend API
→ Auth Middleware → Chat Service → JARVIS Orchestrator
→ Response → Database → Frontend → UI Update
```

## ⚡ Quick Fixes

```bash
# Reset frontend
cd web && rm -rf .next node_modules && npm install

# Reset backend
pip install --force-reinstall -r requirements.txt

# Check logs
tail -f logs/jarvis_v9.log

# Restart services
pkill -f "python main.py"
pkill -f "next dev"
```

## 📞 Support

- Check logs: `logs/jarvis_v9.log`
- Browser console: F12
- Supabase dashboard: Check auth/database
- API docs: http://localhost:8000/docs

---

**Version**: 1.0.0
**Last Updated**: 2026-03-09
**Status**: Production Ready ✅
