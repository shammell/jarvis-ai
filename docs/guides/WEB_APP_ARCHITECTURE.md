# JARVIS Web App - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         JARVIS Web App                              │
│                    (ChatGPT/Claude-like Interface)                  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                  │
│                      Next.js 14 + TypeScript                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Login UI   │  │   Chat UI    │  │  Components  │            │
│  │              │  │              │  │              │            │
│  │ • Sign Up    │  │ • Sidebar    │  │ • Timeline   │            │
│  │ • Sign In    │  │ • Messages   │  │ • Composer   │            │
│  │ • Auth Flow  │  │ • Composer   │  │ • Sidebar    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│         │                  │                  │                    │
│         └──────────────────┴──────────────────┘                    │
│                            │                                        │
│                  ┌─────────▼─────────┐                            │
│                  │   API Client      │                            │
│                  │   (axios + SSE)   │                            │
│                  └─────────┬─────────┘                            │
│                            │                                        │
│                  ┌─────────▼─────────┐                            │
│                  │ Supabase Client   │                            │
│                  │  (Auth + JWT)     │                            │
│                  └───────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             │ HTTPS + JWT Bearer Token
                             │
┌─────────────────────────────▼───────────────────────────────────────┐
│                           BACKEND                                   │
│                      FastAPI + Python                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    API Layer                                  │ │
│  │                                                               │ │
│  │  ┌────────────────┐         ┌────────────────┐              │ │
│  │  │  Chat Router   │         │  Auth Middleware│              │ │
│  │  │  /api/v1/chats │◄────────┤  JWT Verify    │              │ │
│  │  └────────┬───────┘         └────────────────┘              │ │
│  │           │                                                   │ │
│  │  ┌────────▼───────┐                                          │ │
│  │  │  Chat Service  │                                          │ │
│  │  │  • send_message│                                          │ │
│  │  │  • create_chat │                                          │ │
│  │  │  • get_messages│                                          │ │
│  │  └────────┬───────┘                                          │ │
│  │           │                                                   │ │
│  │  ┌────────▼───────────┐                                      │ │
│  │  │  Chat Repository   │                                      │ │
│  │  │  • DB operations   │                                      │ │
│  │  │  • User isolation  │                                      │ │
│  │  └────────────────────┘                                      │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐ │
│  │              JARVIS v9.0 Orchestrator                        │ │
│  │                                                               │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │ │
│  │  │ Speculative    │  │  System2       │  │  Memory       │ │ │
│  │  │ Decoder        │  │  Thinking      │  │  Controller   │ │ │
│  │  └────────────────┘  └────────────────┘  └───────────────┘ │ │
│  │                                                               │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │ │
│  │  │ First          │  │  Hyper         │  │  Skill        │ │ │
│  │  │ Principles     │  │  Automation    │  │  Loader       │ │ │
│  │  └────────────────┘  └────────────────┘  └───────────────┘ │ │
│  │                                                               │ │
│  │  ┌────────────────────────────────────────────────────────┐ │ │
│  │  │         Enhanced Autonomy System                       │ │ │
│  │  │  • Autonomous Executor  • Goal Manager                │ │ │
│  │  │  • Self Monitor         • Proactive Agent             │ │ │
│  │  └────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                             │                                       │
│  ┌──────────────────────────▼───────────────────────────────────┐ │
│  │                  Legacy API (Backward Compatible)            │ │
│  │  • POST /api/message                                         │ │
│  │  • POST /api/agent-team                                      │ │
│  │  • GET  /api/stats                                           │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             │ SQL + RLS
                             │
┌─────────────────────────────▼───────────────────────────────────────┐
│                      DATABASE LAYER                                 │
│                   Supabase (PostgreSQL)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   profiles   │  │    chats     │  │   messages   │            │
│  │              │  │              │  │              │            │
│  │ • id         │  │ • id         │  │ • id         │            │
│  │ • name       │  │ • user_id    │  │ • chat_id    │            │
│  │ • created_at │  │ • title      │  │ • user_id    │            │
│  │              │  │ • created_at │  │ • role       │            │
│  │              │  │ • updated_at │  │ • content    │            │
│  │              │  │ • archived   │  │ • metadata   │            │
│  │              │  │              │  │ • created_at │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │              Row Level Security (RLS)                        │ │
│  │  • Users can only access their own data                     │ │
│  │  • Enforced at database level                               │ │
│  │  • JWT-based authentication                                 │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Supabase Auth                             │ │
│  │  • Email/Password authentication                            │ │
│  │  • JWT token generation                                     │ │
│  │  • Session management                                       │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘


DATA FLOW - Sending a Message
═══════════════════════════════

1. User types message in ChatComposer
2. Frontend calls sendMessage(chatId, content)
3. API client adds JWT Bearer token to request
4. Backend receives POST /api/v1/chats/{id}/messages
5. Auth middleware verifies JWT token
6. Chat service validates chat ownership
7. User message persisted to database
8. JARVIS orchestrator.process_message() called
9. JARVIS generates response using all v9.0 systems
10. Assistant message persisted to database
11. Response returned to frontend
12. UI updates with both messages


SECURITY LAYERS
═══════════════

┌─────────────────────────────────────┐
│  1. Frontend: Supabase Auth         │
│     • JWT token in localStorage     │
│     • Auto-refresh on expiry        │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  2. API: JWT Verification           │
│     • Validate signature            │
│     • Check expiration              │
│     • Extract user_id               │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  3. Service: Ownership Check        │
│     • Verify chat belongs to user   │
│     • Validate permissions          │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  4. Database: RLS Policies          │
│     • Row-level isolation           │
│     • User_id filtering             │
│     • Automatic enforcement         │
└─────────────────────────────────────┘


DEPLOYMENT ARCHITECTURE
═══════════════════════

Production Setup:

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│   Vercel     │      │   Railway    │      │   Supabase   │
│  (Frontend)  │─────▶│  (Backend)   │─────▶│  (Database)  │
│              │      │              │      │              │
│ • Next.js    │      │ • FastAPI    │      │ • PostgreSQL │
│ • Static     │      │ • Docker     │      │ • Auth       │
│ • CDN        │      │ • Auto-scale │      │ • Storage    │
└──────────────┘      └──────────────┘      └──────────────┘
```
