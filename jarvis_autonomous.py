#!/usr/bin/env python3
# ==========================================================
# JARVIS v9.0 - Auto-Start Script
# Runs JARVIS with autonomous startup
# No user interaction needed
# ==========================================================

import asyncio
import logging
from enhanced_autonomy import EnhancedAutonomySystem
from core.autonomous_startup import AutonomousStartup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jarvis_autonomous.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """
    Auto-start JARVIS with full autonomy
    Runs without user prompting
    """
    logger.info("="*60)
    logger.info("JARVIS v9.0 - AUTONOMOUS MODE")
    logger.info("="*60)

    # Initialize Enhanced Autonomy System
    system = EnhancedAutonomySystem()

    # Initialize Autonomous Startup
    startup = AutonomousStartup(system)

    # Run startup sequence (auto-resumes, auto-executes)
    await startup.startup()

    # Start background loop (runs forever)
    logger.info("\n🔄 Entering autonomous mode...")
    logger.info("System will now run autonomously")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*60)

    try:
        await startup.background_loop()
    except KeyboardInterrupt:
        logger.info("\n\n⏹️  Autonomous mode stopped by user")

        # Save state before exit
        system.autonomous_decision.save('data/autonomous_decision_state.json')
        logger.info("💾 State saved")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 JARVIS autonomous mode terminated")
