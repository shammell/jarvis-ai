#!/bin/bash
# JARVIS Cleanup Script - PhD Level
# Removes build artifacts, caches, and redundant dependencies

set -e

echo "🧹 JARVIS Cleanup - PhD Level"
echo "=============================="

# Backup first
BACKUP_DIR="archive/pre_cleanup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 1. Remove Python cache
echo "1. Removing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
echo "   ✓ Python cache removed"

# 2. Remove pytest cache
echo "2. Removing pytest cache..."
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
rm -f .coverage 2>/dev/null || true
echo "   ✓ Pytest cache removed"

# 3. Deduplicate node_modules (keep only root)
echo "3. Deduplicating node_modules..."
# Keep root node_modules, remove duplicates
if [ -d "whatsapp/node_modules" ]; then
    echo "   Moving whatsapp/node_modules to backup..."
    mv whatsapp/node_modules "$BACKUP_DIR/whatsapp_node_modules"
    echo "   ✓ whatsapp/node_modules removed (72MB saved)"
fi

if [ -d "mcp/node_modules" ]; then
    echo "   Moving mcp/node_modules to backup..."
    mv mcp/node_modules "$BACKUP_DIR/mcp_node_modules"
    echo "   ✓ mcp/node_modules removed (85MB saved)"
fi

# 4. Remove build artifacts
echo "4. Removing build artifacts..."
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ Build artifacts removed"

# 5. Remove log files (keep directory)
echo "5. Cleaning log files..."
find logs/ -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
echo "   ✓ Old logs removed"

# 6. Remove graphify cache
echo "6. Cleaning graphify cache..."
rm -rf graphify-out/cache/* 2>/dev/null || true
echo "   ✓ Graphify cache cleared"

# 7. Size report
echo ""
echo "📊 Cleanup Summary"
echo "=================="
du -sh . 2>/dev/null || true
echo ""
echo "Backup location: $BACKUP_DIR"
echo "✅ Cleanup complete"
