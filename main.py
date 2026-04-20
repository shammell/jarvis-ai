# ==========================================================
# JARVIS v9.0 - Main Entry Point (Refactored)
# PhD-Level Architecture - Modular Design
# ==========================================================

import os
import sys
import logging
from contextlib import asynccontextmanager

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import modular components
from core.orchestrator import JarvisV9Orchestrator
from core.api.routes import setup_routes

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jarvis_v9.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global orchestrator

    logger.info("="*60)
    logger.info("JARVIS v9.0 ULTRA - Starting")
    logger.info("="*60)

    # Initialize orchestrator
    orchestrator = JarvisV9Orchestrator()

    # Setup API routes
    setup_routes(app, orchestrator)

    logger.info("✅ JARVIS v9.0 ULTRA ready")

    yield

    # Cleanup on shutdown
    logger.info("🛑 JARVIS v9.0 ULTRA shutting down...")

    # Save state if needed
    if hasattr(orchestrator, 'autonomous'):
        orchestrator.autonomous.save('data/autonomous_decision_state.json')

    logger.info("👋 JARVIS v9.0 ULTRA stopped")


# Create FastAPI app
app = FastAPI(
    title="JARVIS v9.0 ULTRA",
    description="PhD-Level AI Assistant with Elon Musk Features",
    version="9.0.0",
    lifespan=lifespan
)


# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Create required directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state", exist_ok=True)
    os.makedirs("data", exist_ok=True)

    logger.info("="*60)
    logger.info("JARVIS v9.0 ULTRA")
    logger.info("PhD-Level AI Assistant with Elon Musk Features")
    logger.info("="*60)

    # Run server
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        log_level="info"
    )
