---
source_file: "api\routers\chat.py"
type: "rationale"
community: "Community 19"
location: "L99"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_19
---

# Send message and get JARVIS response

## Connections
- [[AuthUser]] - `uses` [INFERRED]
- [[ChatCreate]] - `uses` [INFERRED]
- [[ChatList]] - `uses` [INFERRED]
- [[ChatRepository]] - `uses` [INFERRED]
- [[ChatResponse]] - `uses` [INFERRED]
- [[ChatService]] - `uses` [INFERRED]
- [[InMemoryRateLimiter]] - `uses` [INFERRED]
- [[MessageCreate]] - `uses` [INFERRED]
- [[MessageList]] - `uses` [INFERRED]
- [[MessageResponse]] - `uses` [INFERRED]
- [[RedisRateLimiter]] - `uses` [INFERRED]
- [[SendMessageResponse]] - `uses` [INFERRED]
- [[StreamEvent]] - `uses` [INFERRED]
- [[send_message()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_19