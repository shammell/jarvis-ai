# JARVIS Web App - Testing Guide

## Quick Test Checklist

### 1. Backend API Tests

#### Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status":"healthy","version":"9.0.0","timestamp":"..."}`

#### Legacy API (should still work)
```bash
curl -X POST http://localhost:8000/api/message \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello JARVIS"}'
```

#### Chat API (requires auth token)
```bash
# Get your JWT token from browser localStorage after login
TOKEN="your_jwt_token_here"

# Create chat
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test Chat"}'

# List chats
curl http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer $TOKEN"

# Send message (replace CHAT_ID)
curl -X POST http://localhost:8000/api/v1/chats/CHAT_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello JARVIS"}'
```

### 2. Frontend Tests

#### Manual Testing Flow
1. **Sign Up**
   - Go to http://localhost:3000
   - Click "Sign Up"
   - Enter email and password (min 6 chars)
   - Should redirect to chat page

2. **Sign In**
   - Go to http://localhost:3000/login
   - Enter credentials
   - Should redirect to chat page

3. **Create Chat**
   - Click "New Chat" button
   - Should create empty chat thread

4. **Send Message**
   - Type message in composer
   - Press Enter or click Send
   - Should see user message appear
   - Should see JARVIS response appear

5. **Switch Chats**
   - Click different chat in sidebar
   - Should load that chat's messages

6. **Sign Out**
   - Click "Sign Out" button
   - Should redirect to login page

### 3. Database Tests

#### Check Tables Exist
```sql
-- Run in Supabase SQL Editor
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';
```
Expected: profiles, chats, messages, chat_runs

#### Check RLS Policies
```sql
SELECT tablename, policyname
FROM pg_policies
WHERE schemaname = 'public';
```
Expected: Multiple policies for each table

#### Test Data Isolation
1. Create two user accounts
2. Send messages in User A
3. Sign in as User B
4. Verify User B cannot see User A's chats

### 4. Security Tests

#### JWT Verification
```bash
# Try without token (should fail)
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}'
```
Expected: 401 Unauthorized

#### Invalid Token
```bash
# Try with invalid token (should fail)
curl -X POST http://localhost:8000/api/v1/chats \
  -H "Authorization: Bearer invalid_token" \
  -H "Content-Type: application/json" \
  -d '{"title":"Test"}'
```
Expected: 401 Unauthorized

#### Cross-User Access
```bash
# Try to access another user's chat (should fail)
curl http://localhost:8000/api/v1/chats/OTHER_USER_CHAT_ID/messages \
  -H "Authorization: Bearer $TOKEN"
```
Expected: 404 Not Found or empty messages

### 5. Performance Tests

#### Response Time
```bash
# Measure API response time
time curl -X POST http://localhost:8000/api/v1/chats/CHAT_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Quick test"}'
```
Expected: < 2 seconds for simple queries

#### Concurrent Requests
```bash
# Send 10 concurrent requests
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/chats/CHAT_ID/messages \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content":"Test '$i'"}' &
done
wait
```

### 6. Integration Tests

#### Full User Flow
```python
# test_integration.py
import requests
import time

BASE_URL = "http://localhost:8000"
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_anon_key"

def test_full_flow():
    # 1. Sign up
    email = f"test_{int(time.time())}@example.com"
    password = "test123456"

    auth_response = requests.post(
        f"{SUPABASE_URL}/auth/v1/signup",
        json={"email": email, "password": password},
        headers={"apikey": SUPABASE_KEY}
    )
    assert auth_response.status_code == 200
    token = auth_response.json()["access_token"]

    # 2. Create chat
    chat_response = requests.post(
        f"{BASE_URL}/api/v1/chats",
        json={"title": "Test Chat"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert chat_response.status_code == 201
    chat_id = chat_response.json()["id"]

    # 3. Send message
    message_response = requests.post(
        f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
        json={"content": "Hello JARVIS"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert message_response.status_code == 200
    assert "user_message" in message_response.json()
    assert "assistant_message" in message_response.json()

    # 4. Get messages
    messages_response = requests.get(
        f"{BASE_URL}/api/v1/chats/{chat_id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert messages_response.status_code == 200
    assert len(messages_response.json()["messages"]) == 2

    print("✅ All tests passed!")

if __name__ == "__main__":
    test_full_flow()
```

### 7. Error Handling Tests

#### Invalid Input
```bash
# Empty message
curl -X POST http://localhost:8000/api/v1/chats/CHAT_ID/messages \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":""}'
```
Expected: 422 Validation Error

#### Non-existent Chat
```bash
# Invalid chat ID
curl http://localhost:8000/api/v1/chats/00000000-0000-0000-0000-000000000000/messages \
  -H "Authorization: Bearer $TOKEN"
```
Expected: 404 Not Found

### 8. Browser Console Tests

Open browser console (F12) and run:

```javascript
// Check Supabase connection
console.log('Supabase URL:', process.env.NEXT_PUBLIC_SUPABASE_URL)

// Check API URL
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL)

// Check auth state
const { data: { session } } = await supabase.auth.getSession()
console.log('Session:', session)

// Test API call
const response = await fetch('http://localhost:8000/api/v1/chats', {
  headers: {
    'Authorization': `Bearer ${session.access_token}`
  }
})
console.log('Chats:', await response.json())
```

## Common Issues & Solutions

### Issue: "JWT secret not configured"
**Solution**: Add `SUPABASE_JWT_SECRET` to `.env`

### Issue: "Invalid token"
**Solution**:
1. Check JWT secret matches Supabase project
2. Token might be expired, sign in again
3. Verify token format: `Bearer <token>`

### Issue: "Chat not found"
**Solution**:
1. Verify chat belongs to authenticated user
2. Check chat_id is correct UUID
3. Ensure RLS policies are enabled

### Issue: Frontend can't connect to backend
**Solution**:
1. Verify backend is running on port 8000
2. Check CORS_ORIGINS includes frontend URL
3. Check NEXT_PUBLIC_API_URL in .env.local

### Issue: Messages not appearing
**Solution**:
1. Check browser console for errors
2. Verify JWT token is valid
3. Check backend logs for errors
4. Ensure orchestrator is initialized

### Issue: "Supabase client error"
**Solution**:
1. Verify SUPABASE_URL and keys are correct
2. Check Supabase project is active
3. Verify RLS policies are enabled
4. Check database migrations ran successfully

## Performance Benchmarks

Expected performance metrics:

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Sign In | < 500ms | < 1s |
| Create Chat | < 200ms | < 500ms |
| Send Message | < 2s | < 5s |
| Load Messages | < 300ms | < 1s |
| List Chats | < 200ms | < 500ms |

## Load Testing

Use Apache Bench for load testing:

```bash
# Install ab (Apache Bench)
# Windows: Download from Apache website
# Linux: sudo apt-get install apache2-utils
# Mac: brew install ab

# Test chat creation (100 requests, 10 concurrent)
ab -n 100 -c 10 -H "Authorization: Bearer $TOKEN" \
  -p chat.json -T application/json \
  http://localhost:8000/api/v1/chats
```

## Automated Testing

Create `test_webapp.sh`:

```bash
#!/bin/bash

echo "Running JARVIS Web App Tests..."

# 1. Check backend is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo "❌ Backend not running"
    exit 1
fi
echo "✅ Backend is running"

# 2. Check frontend is running
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "❌ Frontend not running"
    exit 1
fi
echo "✅ Frontend is running"

# 3. Check database connection
# (Add Supabase health check)

echo ""
echo "✅ All basic checks passed!"
echo "Run manual tests for full verification"
```

## Test Coverage Goals

- ✅ Authentication flow
- ✅ Chat CRUD operations
- ✅ Message send/receive
- ✅ User data isolation
- ✅ Error handling
- ✅ JWT verification
- ✅ RLS policies
- ✅ API backward compatibility
- ✅ Frontend routing
- ✅ UI responsiveness

## Next Steps

After basic tests pass:
1. Add rate limiting tests
2. Add streaming tests
3. Add file upload tests (when implemented)
4. Add mobile responsiveness tests
5. Add accessibility tests
6. Add SEO tests
7. Add performance monitoring
