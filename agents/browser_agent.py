# ==========================================================
# JARVIS v9.0 - Browser Automation Agent
# Playwright-based browser control with computer vision
# Autonomous web navigation
# ==========================================================

import logging
from typing import Dict, Any, Optional, List
import asyncio
import base64
from datetime import datetime

logger = logging.getLogger(__name__)


class BrowserAgent:
    """
    Browser automation agent for JARVIS v9.0
    - Uses Playwright for browser control
    - Screenshot + DOM analysis
    - Click buttons, fill forms, scrape data
    - Fully autonomous web navigation
    """

    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.available = False

        self._init_playwright()

        logger.info("🌐 Browser Agent initialized")

    def _init_playwright(self):
        """Initialize Playwright"""
        try:
            from playwright.async_api import async_playwright

            self.playwright_module = async_playwright
            self.available = True
            logger.info("✅ Playwright available")

        except ImportError:
            logger.warning("⚠️ Playwright not installed. Run: pip install playwright && playwright install")
            self.available = False

    async def start(self, headless: bool = True):
        """Start browser"""
        if not self.available:
            raise RuntimeError("Playwright not available")

        self.playwright = await self.playwright_module().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()

        logger.info("🚀 Browser started")

    async def stop(self):
        """Stop browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("🛑 Browser stopped")

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL"""
        if not self.page:
            await self.start()

        logger.info(f"🔗 Navigating to: {url}")

        try:
            response = await self.page.goto(url, wait_until="networkidle")

            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "status": response.status
            }

        except Exception as e:
            logger.error(f"❌ Navigation failed: {e}")
            return {"success": False, "error": str(e)}

    async def screenshot(self, full_page: bool = False) -> str:
        """Take screenshot and return base64"""
        if not self.page:
            raise RuntimeError("Browser not started")

        screenshot_bytes = await self.page.screenshot(full_page=full_page)
        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()

        logger.info("📸 Screenshot captured")

        return screenshot_b64

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element"""
        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            await self.page.click(selector)
            logger.info(f"👆 Clicked: {selector}")

            return {"success": True, "selector": selector}

        except Exception as e:
            logger.error(f"❌ Click failed: {e}")
            return {"success": False, "error": str(e)}

    async def fill(self, selector: str, text: str) -> Dict[str, Any]:
        """Fill input field"""
        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            await self.page.fill(selector, text)
            logger.info(f"✍️ Filled: {selector}")

            return {"success": True, "selector": selector}

        except Exception as e:
            logger.error(f"❌ Fill failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of element"""
        if not self.page:
            raise RuntimeError("Browser not started")

        try:
            text = await self.page.text_content(selector)
            return text

        except Exception as e:
            logger.error(f"❌ Get text failed: {e}")
            return None

    async def scrape(self, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Scrape multiple elements"""
        if not self.page:
            raise RuntimeError("Browser not started")

        results = {}

        for key, selector in selectors.items():
            try:
                text = await self.page.text_content(selector)
                results[key] = text
            except Exception as e:
                logger.warning(f"⚠️ Could not scrape {key}: {e}")
                results[key] = None

        logger.info(f"📊 Scraped {len(results)} elements")

        return results

    async def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute browser automation task

        Args:
            task: Task description (e.g., "Go to google.com and search for JARVIS")
            context: Additional context

        Returns:
            Task result
        """
        logger.info(f"🤖 Executing browser task: {task[:50]}...")

        # Parse task (simple implementation)
        task_lower = task.lower()

        try:
            if "go to" in task_lower or "navigate" in task_lower:
                # Extract URL
                words = task.split()
                url = next((w for w in words if "http" in w or ".com" in w), None)
                if url:
                    result = await self.navigate(url)
                    return result

            elif "click" in task_lower:
                # Extract selector (simplified)
                # In production, use LLM to extract selector
                selector = context.get("selector") if context else None
                if selector:
                    result = await self.click(selector)
                    return result

            elif "fill" in task_lower or "type" in task_lower:
                # Extract selector and text
                selector = context.get("selector") if context else None
                text = context.get("text") if context else None
                if selector and text:
                    result = await self.fill(selector, text)
                    return result

            elif "screenshot" in task_lower:
                screenshot = await self.screenshot()
                return {"success": True, "screenshot": screenshot}

            elif "scrape" in task_lower:
                selectors = context.get("selectors", {}) if context else {}
                data = await self.scrape(selectors)
                return {"success": True, "data": data}

            return {"success": False, "error": "Could not parse task"}

        except Exception as e:
            logger.error(f"❌ Task execution failed: {e}")
            return {"success": False, "error": str(e)}

    async def autonomous_navigate(self, goal: str, max_steps: int = 10) -> Dict[str, Any]:
        """
        Autonomous navigation to achieve goal
        Uses vision + LLM to decide actions

        Args:
            goal: Navigation goal (e.g., "Find JARVIS documentation")
            max_steps: Maximum navigation steps

        Returns:
            Navigation result
        """
        logger.info(f"🎯 Autonomous navigation: {goal}")

        steps = []

        for step in range(max_steps):
            # Take screenshot
            screenshot = await self.screenshot()

            # Get page state
            url = self.page.url
            title = await self.page.title()

            # TODO: Use vision LLM to analyze screenshot and decide next action
            # For now, just record state

            steps.append({
                "step": step,
                "url": url,
                "title": title,
                "timestamp": datetime.now().isoformat()
            })

            # Check if goal achieved (simplified)
            if goal.lower() in title.lower():
                logger.info(f"✅ Goal achieved in {step + 1} steps")
                return {
                    "success": True,
                    "steps": steps,
                    "final_url": url
                }

            # TODO: Decide next action based on vision analysis

        logger.warning(f"⚠️ Goal not achieved in {max_steps} steps")
        return {
            "success": False,
            "steps": steps,
            "error": "Max steps reached"
        }


# Test
if __name__ == "__main__":
    async def test_browser():
        agent = BrowserAgent()

        if not agent.available:
            print("❌ Playwright not available")
            return

        try:
            # Start browser
            await agent.start(headless=False)

            # Navigate
            result = await agent.navigate("https://www.google.com")
            print(f"\n✅ Navigation: {result}")

            # Take screenshot
            screenshot = await agent.screenshot()
            print(f"\n📸 Screenshot captured: {len(screenshot)} bytes")

            # Wait a bit
            await asyncio.sleep(2)

        finally:
            # Stop browser
            await agent.stop()

    asyncio.run(test_browser())
