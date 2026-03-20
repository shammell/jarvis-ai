# ==========================================================
# JARVIS v9.0 - Autonomous Startup System
# Runs automatically when JARVIS starts
# No user prompting needed
# ==========================================================

import logging
import asyncio
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class AutonomousStartup:
    """
    Autonomous startup system that runs automatically
    - Loads previous session state
    - Resumes active goals
    - Starts proactive monitoring
    - Executes without user prompting
    """

    def __init__(self, autonomy_system):
        self.autonomy_system = autonomy_system
        self.auto_mode = True  # Always run autonomously

        logger.info("🚀 Autonomous Startup System initialized")

    async def startup(self):
        """
        Run autonomous startup sequence
        This runs automatically when JARVIS starts
        """
        logger.info("="*60)
        logger.info("AUTONOMOUS STARTUP SEQUENCE")
        logger.info("="*60)

        # 1. Resume previous session
        await self._resume_previous_session()

        # 2. Check for pending work
        await self._check_pending_work()

        # 3. Start proactive monitoring
        await self._start_proactive_monitoring()

        # 4. Execute autonomous tasks
        await self._execute_autonomous_tasks()

        logger.info("✅ Autonomous startup complete")

    async def _resume_previous_session(self):
        """Resume from previous session automatically"""
        logger.info("\n📂 Resuming previous session...")

        resume_result = await self.autonomy_system.resume_session()

        if resume_result['resumed']:
            logger.info(f"✅ Resumed: {resume_result['message']}")
            logger.info(f"   Active goals: {resume_result['active_goals_count']}")

            # Automatically continue next goal
            next_goal = resume_result.get('next_goal')
            if next_goal:
                logger.info(f"   Next: {next_goal['description']}")
                logger.info(f"   Progress: {next_goal['progress']:.1%}")
        else:
            logger.info("ℹ️  No previous session to resume")

    async def _check_pending_work(self):
        """Check for pending work and execute automatically"""
        logger.info("\n🔍 Checking for pending work...")

        # Get active goals
        active_goals = self.autonomy_system.goal_manager.get_active_goals()

        if active_goals:
            logger.info(f"✅ Found {len(active_goals)} active goals")

            # Auto-execute high priority goals
            for goal in active_goals:
                if goal['priority'] >= 3:  # HIGH or CRITICAL
                    logger.info(f"🚀 Auto-executing: {goal['description']}")

                    try:
                        result = await self.autonomy_system.execute_goal(
                            goal['description'],
                            context=goal['context']
                        )

                        if result['success']:
                            logger.info(f"✅ Completed: {goal['description']}")
                        else:
                            logger.warning(f"⚠️  Failed: {goal['description']}")

                    except Exception as e:
                        logger.error(f"❌ Error executing goal: {e}")
        else:
            logger.info("ℹ️  No pending work found")

    async def _start_proactive_monitoring(self):
        """Start proactive monitoring and suggestions"""
        logger.info("\n🔮 Starting proactive monitoring...")

        suggestions = await self.autonomy_system.get_proactive_suggestions()

        if suggestions['suggestion_count'] > 0:
            logger.info(f"💡 Generated {suggestions['suggestion_count']} suggestions")

            # Auto-execute low-risk suggestions
            for i, suggestion in enumerate(suggestions['suggestions']):
                if suggestion['priority'] == 'low':
                    logger.info(f"🚀 Auto-executing suggestion: {suggestion['title']}")

                    try:
                        result = await self.autonomy_system.execute_suggestion(i)
                        if result.get('success'):
                            logger.info(f"✅ Suggestion executed successfully")
                    except Exception as e:
                        logger.error(f"❌ Error executing suggestion: {e}")
        else:
            logger.info("ℹ️  No suggestions at this time")

    async def _execute_autonomous_tasks(self):
        """Execute autonomous maintenance tasks"""
        logger.info("\n🔧 Running autonomous maintenance...")

        # Take performance snapshot
        self.autonomy_system.self_monitor.take_snapshot()
        logger.info("✅ Performance snapshot taken")

        # Check system health
        status = self.autonomy_system.get_system_status()
        health = status['performance']['health_score']
        autonomy = status['autonomy']['level']

        logger.info(f"📊 System Health: {health:.1f}/100")
        logger.info(f"🤖 Autonomy Level: {autonomy:.1%}")

        # Auto-optimize if health is low
        if health < 80:
            logger.warning(f"⚠️  Low health detected: {health:.1f}/100")
            logger.info("🚀 Auto-starting optimization...")

            try:
                result = await self.autonomy_system.execute_goal(
                    "Optimize system performance",
                    priority=4,  # CRITICAL
                    context={"auto_triggered": True, "health_score": health}
                )

                if result['success']:
                    logger.info("✅ Auto-optimization complete")
            except Exception as e:
                logger.error(f"❌ Auto-optimization failed: {e}")

    async def background_loop(self):
        """
        Background loop that runs continuously
        Monitors and executes tasks autonomously
        """
        logger.info("🔄 Starting autonomous background loop...")

        while True:
            try:
                # Check every 5 minutes
                await asyncio.sleep(300)

                logger.info("\n🔄 Autonomous check cycle...")

                # Check for new work
                await self._check_pending_work()

                # Generate proactive suggestions
                await self._start_proactive_monitoring()

                # Take snapshot
                self.autonomy_system.self_monitor.take_snapshot()

            except Exception as e:
                logger.error(f"❌ Background loop error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error


# Integration function for JARVIS main.py
async def autonomous_startup_sequence(autonomy_system):
    """
    Call this from JARVIS main.py startup
    Runs autonomous startup without user prompting
    """
    startup = AutonomousStartup(autonomy_system)
    await startup.startup()

    # Start background loop (non-blocking)
    asyncio.create_task(startup.background_loop())


# Standalone test
if __name__ == "__main__":
    from enhanced_autonomy import EnhancedAutonomySystem

    async def test():
        system = EnhancedAutonomySystem()
        startup = AutonomousStartup(system)

        # Run startup sequence
        await startup.startup()

        # Run background loop for 1 minute (test)
        logger.info("\n🔄 Running background loop for 1 minute (test)...")
        try:
            await asyncio.wait_for(startup.background_loop(), timeout=60)
        except asyncio.TimeoutError:
            logger.info("✅ Background loop test complete")

    asyncio.run(test())
