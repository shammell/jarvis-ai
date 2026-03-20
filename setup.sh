#!/bin/bash
# ==========================================================
# JARVIS v9.0 ULTRA - Quick Start Script
# ==========================================================

echo "=================================="
echo "JARVIS v9.0 ULTRA - Quick Start"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python
echo -e "\n${YELLOW}Checking Python...${NC}"
if command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo -e "${RED}✗ Python not found. Please install Python 3.10+${NC}"
    exit 1
fi

# Check Node.js
echo -e "\n${YELLOW}Checking Node.js...${NC}"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION found${NC}"
else
    echo -e "${RED}✗ Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs state memory_storage models/lora_adapters
echo -e "${GREEN}✓ Directories created${NC}"

# Check .env file
echo -e "\n${YELLOW}Checking environment configuration...${NC}"
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠ .env file not found. Creating from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠ Please edit .env and add your GROQ_API_KEY${NC}"
    echo -e "${YELLOW}⚠ Get your key from: https://console.groq.com/keys${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Install Python dependencies
echo -e "\n${YELLOW}Installing Python dependencies...${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate venv
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Install Node.js dependencies
echo -e "\n${YELLOW}Installing Node.js dependencies...${NC}"
npm install > /dev/null 2>&1
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Generate gRPC code
echo -e "\n${YELLOW}Generating gRPC code...${NC}"
python -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ gRPC code generated${NC}"
else
    echo -e "${YELLOW}⚠ gRPC code generation skipped (grpcio-tools may not be installed)${NC}"
fi

# Summary
echo -e "\n=================================="
echo -e "${GREEN}✓ JARVIS v9.0 ULTRA Setup Complete!${NC}"
echo -e "==================================\n"

echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Edit .env file with your API keys"
echo -e "2. Start services:"
echo -e "   ${GREEN}Terminal 1:${NC} python grpc/python_server.py"
echo -e "   ${GREEN}Terminal 2:${NC} npm run start:bridge"
echo -e "   ${GREEN}Terminal 3:${NC} python main.py"
echo -e "\n3. Test the system:"
echo -e "   ${GREEN}curl http://localhost:8000/health${NC}"
echo -e "\n4. View documentation:"
echo -e "   ${GREEN}cat README.md${NC}"
echo -e "\n${YELLOW}For detailed setup, see README.md${NC}\n"
