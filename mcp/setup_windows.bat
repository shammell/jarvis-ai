@echo off
echo ============================================
echo  JARVIS Terminal MCP - Windows Setup
echo ============================================
echo.

REM Step 1: Check Node.js
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Node.js nahi mila! Install karo: https://nodejs.org
    pause
    exit /b 1
)
echo [OK] Node.js mila

REM Step 2: Set folder path
SET MCP_DIR=%USERPROFILE%\jarvis-terminal-mcp
echo [INFO] MCP folder: %MCP_DIR%

REM Step 3: Copy files
IF NOT EXIST "%MCP_DIR%" mkdir "%MCP_DIR%"
copy "server.js" "%MCP_DIR%\server.js"
copy "package.json" "%MCP_DIR%\package.json"

REM Step 4: Install dependencies
echo.
echo [INFO] Dependencies install ho rahi hain...
cd /d "%MCP_DIR%"
npm install

IF ERRORLEVEL 1 (
    echo [ERROR] npm install fail ho gaya!
    pause
    exit /b 1
)

echo.
echo [OK] Dependencies install ho gayi!
echo.
echo ============================================
echo  Ab Claude Code mein yeh command run karo:
echo ============================================
echo.
echo claude mcp add jarvis-terminal --scope user -- node "%MCP_DIR%\server.js"
echo.
echo ============================================
echo  Ya seedha claude mein jaake type karo:
echo ============================================
echo.
echo /mcp
echo.
pause
