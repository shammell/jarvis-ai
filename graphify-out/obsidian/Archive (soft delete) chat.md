---
source_file: "api\routers\chat.py"
type: "rationale"
community: "Community 19"
location: "L172"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_19
---

# Archive (soft delete) chat

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
- [[delete_chat()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_19