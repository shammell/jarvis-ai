#!/bin/bash
# JARVIS Web App - Quick Verification Script

echo "=========================================="
echo "JARVIS Web App - File Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check backend files
echo "Checking Backend Files..."
files=(
    "api/__init__.py"
    "api/auth.py"
    "api/routers/__init__.py"
    "api/routers/chat.py"
    "api/services/__init__.py"
    "api/services/chat_service.py"
    "api/repositories/__init__.py"
    "api/repositories/chat_repository.py"
    "api/schemas/__init__.py"
    "api/schemas/chat.py"
    "api/db/__init__.py"
    "api/db/supabase_client.py"
    "supabase/migrations/20260309_create_chat_tables.sql"
)

backend_count=0
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        ((backend_count++))
    else
        echo -e "${RED}✗${NC} $file"
    fi
done

echo ""
echo "Checking Frontend Files..."
frontend_files=(
    "web/package.json"
    "web/tsconfig.json"
    "web/next.config.js"
    "web/tailwind.config.js"
    "web/postcss.config.js"
    "web/.env.local.example"
    "web/.gitignore"
    "web/app/layout.tsx"
    "web/app/page.tsx"
    "web/app/globals.css"
    "web/app/login/page.tsx"
    "web/app/chat/page.tsx"
    "web/components/chat/ChatSidebar.tsx"
    "web/components/chat/ChatTimeline.tsx"
    "web/components/chat/ChatComposer.tsx"
    "web/lib/api.ts"
    "web/lib/supabase/client.ts"
)

frontend_count=0
for file in "${frontend_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        ((frontend_count++))
    else
        echo -e "${RED}✗${NC} $file"
    fi
done

echo ""
echo "Checking Documentation..."
doc_files=(
    "WEB_APP_README.md"
    "WEB_APP_QUICKREF.md"
    "WEB_APP_IMPLEMENTATION.md"
    "WEB_APP_ARCHITECTURE.md"
    "WEB_APP_TESTING.md"
    "WEB_APP_DEPLOYMENT.md"
    "WEB_APP_SUMMARY.md"
    "WEB_APP_BEFORE_AFTER.md"
    "WEB_APP_CHECKLIST.md"
)

doc_count=0
for file in "${doc_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        ((doc_count++))
    else
        echo -e "${RED}✗${NC} $file"
    fi
done

echo ""
echo "Checking Scripts..."
script_files=(
    "setup_webapp.sh"
    "setup_webapp.ps1"
    "start_webapp.sh"
    "start_webapp.ps1"
)

script_count=0
for file in "${script_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
        ((script_count++))
    else
        echo -e "${RED}✗${NC} $file"
    fi
done

echo ""
echo "=========================================="
echo "Summary"
echo "=========================================="
echo "Backend Files: $backend_count/${#files[@]}"
echo "Frontend Files: $frontend_count/${#frontend_files[@]}"
echo "Documentation: $doc_count/${#doc_files[@]}"
echo "Scripts: $script_count/${#script_files[@]}"
echo ""

total=$((backend_count + frontend_count + doc_count + script_count))
expected=$((${#files[@]} + ${#frontend_files[@]} + ${#doc_files[@]} + ${#script_files[@]}))

if [ $total -eq $expected ]; then
    echo -e "${GREEN}✅ All files present! ($total/$expected)${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Run ./setup_webapp.sh"
    echo "2. Configure .env and web/.env.local"
    echo "3. Run database migration in Supabase"
    echo "4. Run ./start_webapp.sh"
    echo "5. Open http://localhost:3000"
else
    echo -e "${RED}⚠️  Some files missing ($total/$expected)${NC}"
fi

echo ""
