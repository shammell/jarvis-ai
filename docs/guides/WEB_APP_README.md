# JARVIS Web App - Setup Guide

## Overview
Production-ready ChatGPT/Claude-like web application for JARVIS with Supabase authentication and multi-user chat support.

## Architecture
- **Frontend**: Next.js 14 (TypeScript) with Tailwind CSS
- **Backend**: FastAPI with existing JARVIS orchestrator
- **Database**: Supabase (PostgreSQL)
- **Auth**: Supabase Auth (JWT)

## Prerequisites
- Python 3.9+
- Node.js 18+
- Supabase account
- Existing JARVIS dependencies

## Setup Instructions

### 1. Backend Setup

#### Install Python dependencies
```bash
cd C:\Users\AK\jarvis_project
pip install supabase pyjwt
```

#### Configure environment variables
Add to `.env`:
```env
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
SUPABASE_JWT_SECRET=your_jwt_secret

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

#### Run database migrations
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run the migration file: `supabase/migrations/20260309_create_chat_tables.sql`

### 2. Frontend Setup

#### Install dependencies
```bash
cd web
npm install
```

#### Configure environment variables
Create `web/.env.local`:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_project_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Running the Application

#### Start backend (Terminal 1)
```bash
cd C:\Users\AK\jarvis_project
python main.py
```
Backend runs on: http://localhost:8000

#### Start frontend (Terminal 2)
```bash
cd web
npm run dev
```
Frontend runs on: http://localhost:3000

### 4. First Time Usage

1. Open http://localhost:3000
2. Click "Sign Up" to create an account
3. Sign in with your credentials
4. Start chatting with JARVIS!

## API Endpoints

### New Chat API (v1)
- `POST /api/v1/chats` - Create new chat
- `GET /api/v1/chats` - List user chats
- `GET /api/v1/chats/{chat_id}/messages` - Get messages
- `POST /api/v1/chats/{chat_id}/messages` - Send message
- `POST /api/v1/chats/{chat_id}/stream` - Stream response (SSE)
- `DELETE /api/v1/chats/{chat_id}` - Archive chat

### Legacy API (backward compatible)
- `POST /api/message` - Process message (existing)
- `POST /api/agent-team` - Agent team execution (existing)
- `GET /api/stats` - System stats (existing)

## Database Schema

### Tables
- `profiles` - User profiles
- `chats` - Chat threads
- `messages` - Chat messages
- `chat_runs` - Observability data

### Security
- Row Level Security (RLS) enabled on all tables
- JWT verification on all API requests
- User data isolation enforced at DB level

## Features

### Frontend
- ✅ Supabase authentication (email/password)
- ✅ Multi-chat thread management
- ✅ Real-time message streaming
- ✅ Responsive UI (mobile-friendly)
- ✅ Message history with pagination
- ✅ Auto-save chat titles
- ✅ Metadata display (latency, source)

### Backend
- ✅ JWT authentication middleware
- ✅ Conversation-aware API
- ✅ Reuses existing JARVIS intelligence
- ✅ Message persistence
- ✅ User data isolation
- ✅ CORS configuration
- ✅ Backward compatibility

## Development

### Frontend development
```bash
cd web
npm run dev     # Development server
npm run build   # Production build
npm run start   # Production server
npm run lint    # Lint code
```

### Backend testing
```bash
# Test chat API
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}'
```

## Production Deployment

### Frontend (Vercel)
1. Push code to GitHub
2. Import project in Vercel
3. Set environment variables
4. Deploy

### Backend (Docker/Cloud)
1. Use existing Docker setup
2. Add Supabase env vars
3. Deploy to cloud provider

## Security Checklist

- ✅ JWT verification on all protected routes
- ✅ Row Level Security (RLS) policies
- ✅ User data isolation
- ✅ Input validation (Pydantic)
- ✅ CORS restrictions
- ✅ Rate limiting (recommended: add middleware)
- ✅ Secrets in environment variables only

## Troubleshooting

### Backend issues
- Check `.env` has all Supabase credentials
- Verify JWT secret matches Supabase project
- Check logs in `logs/jarvis_v9.log`

### Frontend issues
- Verify `.env.local` has correct values
- Check browser console for errors
- Ensure backend is running on port 8000

### Database issues
- Run migrations in Supabase SQL Editor
- Check RLS policies are enabled
- Verify service role key has admin access

## File Structure

```
jarvis_project/
├── api/                          # New chat API
│   ├── routers/
│   │   └── chat.py              # Chat endpoints
│   ├── services/
│   │   └── chat_service.py      # Business logic
│   ├── repositories/
│   │   └── chat_repository.py   # Data access
│   ├── schemas/
│   │   └── chat.py              # Pydantic models
│   ├── db/
│   │   └── supabase_client.py   # DB client
│   └── auth.py                  # JWT verification
├── supabase/
│   └── migrations/
│       └── 20260309_create_chat_tables.sql
├── web/                         # Next.js frontend
│   ├── app/
│   │   ├── chat/
│   │   │   └── page.tsx        # Chat UI
│   │   ├── login/
│   │   │   └── page.tsx        # Auth UI
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   └── chat/
│   │       ├── ChatSidebar.tsx
│   │       ├── ChatTimeline.tsx
│   │       └── ChatComposer.tsx
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── supabase/
│   │       └── client.ts       # Supabase client
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.js
└── main.py                      # Updated with chat router

```

## Next Steps

1. **Add rate limiting** - Protect against abuse
2. **Add streaming UI** - Real-time token streaming
3. **Add file uploads** - Image/document support
4. **Add chat search** - Search across conversations
5. **Add export** - Download chat history
6. **Add themes** - Dark/light mode
7. **Add OAuth** - Google/GitHub sign-in

## Support

For issues or questions:
- Check logs: `logs/jarvis_v9.log`
- Review Supabase dashboard
- Check browser console
- Verify all environment variables

## License

Part of JARVIS v9.0+ project
