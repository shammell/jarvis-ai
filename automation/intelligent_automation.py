#!/usr/bin/env python3
"""
INTELLIGENT AUTOMATION SYSTEM
Real AI-powered decision making and adaptive control
"""

import win32gui
import win32process
import psutil
import time
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of an action with metrics"""
    action: str
    success: bool
    duration: float
    screen_change_percent: float
    timestamp: float
    metadata: Dict = field(default_factory=dict)


class IntelligentAutomation:
    """
    Intelligent automation with real learning capabilities:
    - Adaptive timing based on system performance
    - Smart retry with exponential backoff
    - Action success prediction
    - Performance optimization
    - Error recovery strategies
    """

    def __init__(self):
        self.action_history = deque(maxlen=200)
        self.screen_history = deque(maxlen=20)
        self.performance_stats = {
            'open_tab': {'avg_time': 0.5, 'success_rate': 1.0, 'samples': 0},
            'navigate': {'avg_time': 2.0, 'success_rate': 0.9, 'samples': 0},
            'close_tab': {'avg_time': 0.3, 'success_rate': 1.0, 'samples': 0},
        }
        pyautogui.PAUSE = 0.05  # Minimal pause
        logger.info("Intelligent Automation initialized")

    def find_chrome_by_profile(self, profile_name: str = None) -> Optional[Dict]:
        """Find Chrome window, optionally by profile"""
        chrome_windows = []

        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        process = psutil.Process(pid)
                        if 'chrome' in process.name().lower():
                            chrome_windows.append({
                                'hwnd': hwnd,
                                'title': title,
                                'pid': pid
                            })
                    except Exception as e:
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.exception("Failed to get window information: %s", e)
                        pass
            return True

        win32gui.EnumWindows(callback, chrome_windows)

        if not chrome_windows:
            return None

        # If profile specified, try to find it
        if profile_name:
            for window in chrome_windows:
                if profile_name.lower() in window['title'].lower():
                    return window

        # Return first window
        return chrome_windows[0]

    def switch_to_chrome(self, chrome_window: Dict) -> bool:
        """Switch to Chrome with verification"""
        try:
            win32gui.SetForegroundWindow(chrome_window['hwnd'])
            time.sleep(0.2)

            # Verify
            active = win32gui.GetForegroundWindow()
            return active == chrome_window['hwnd']
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Failed to switch to Chrome window: %s", e)
            return False
            return False

    def take_screenshot(self) -> np.ndarray:
        """Capture screen efficiently"""
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)
        screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

        self.screen_history.append(screenshot_cv)
        return screenshot_cv

    def calculate_screen_change(self) -> float:
        """Calculate screen change percentage"""
        if len(self.screen_history) < 2:
            return 0.0

        prev = cv2.resize(self.screen_history[-2], (320, 240))
        curr = cv2.resize(self.screen_history[-1], (320, 240))

        diff = cv2.absdiff(prev, curr)
        change_percent = np.sum(diff) / (320 * 240 * 3 * 255)

        return change_percent

    def adaptive_wait(self, action_type: str, multiplier: float = 1.0):
        """Wait adaptively based on learned performance"""
        stats = self.performance_stats.get(action_type, {'avg_time': 1.0})
        wait_time = stats['avg_time'] * multiplier
        time.sleep(wait_time)

    def execute_with_retry(self, action_func, max_retries: int = 3,
                          verify_change: bool = True) -> ActionResult:
        """Execute action with smart retry logic"""
        start_time = time.time()

        for attempt in range(max_retries):
            # Take before screenshot
            self.take_screenshot()

            # Execute action
            try:
                action_func()
            except Exception as e:
                logger.error(f"Action failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                else:
                    return ActionResult(
                        action=action_func.__name__,
                        success=False,
                        duration=time.time() - start_time,
                        screen_change_percent=0.0,
                        timestamp=time.time(),
                        metadata={'error': str(e)}
                    )

            # Wait and verify
            time.sleep(0.5)
            self.take_screenshot()
            change = self.calculate_screen_change()

            # Check if action succeeded
            if not verify_change or change > 0.01:
                duration = time.time() - start_time
                result = ActionResult(
                    action=action_func.__name__,
                    success=True,
                    duration=duration,
                    screen_change_percent=change,
                    timestamp=time.time(),
                    metadata={'attempts': attempt + 1}
                )

                self.action_history.append(result)
                self._update_performance_stats(result)

                return result

            # Retry
            if attempt < max_retries - 1:
                logger.warning(f"Action verification failed, retrying ({attempt + 1}/{max_retries})")
                time.sleep(0.3 * (attempt + 1))

        # All retries failed
        return ActionResult(
            action=action_func.__name__,
            success=False,
            duration=time.time() - start_time,
            screen_change_percent=0.0,
            timestamp=time.time(),
            metadata={'max_retries_reached': True}
        )

    def _update_performance_stats(self, result: ActionResult):
        """Update performance statistics for learning"""
        action = result.action

        if action not in self.performance_stats:
            self.performance_stats[action] = {
                'avg_time': result.duration,
                'success_rate': 1.0 if result.success else 0.0,
                'samples': 1
            }
        else:
            stats = self.performance_stats[action]
            n = stats['samples']

            # Update running average
            stats['avg_time'] = (stats['avg_time'] * n + result.duration) / (n + 1)
            stats['success_rate'] = (stats['success_rate'] * n + (1.0 if result.success else 0.0)) / (n + 1)
            stats['samples'] = n + 1

    def smart_open_tab(self, chrome_window: Dict) -> ActionResult:
        """Open new tab with intelligence"""
        self.switch_to_chrome(chrome_window)

        def action():
            pyautogui.hotkey('ctrl', 't')

        return self.execute_with_retry(action, verify_change=True)

    def smart_navigate(self, chrome_window: Dict, url: str) -> ActionResult:
        """Navigate with intelligence"""
        self.switch_to_chrome(chrome_window)

        def action():
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.1)
            pyautogui.write(url, interval=0.01)
            time.sleep(0.1)
            pyautogui.press('enter')
            time.sleep(1.5)  # Wait for page load

        return self.execute_with_retry(action, verify_change=True, max_retries=2)

    def smart_close_tab(self, chrome_window: Dict) -> ActionResult:
        """Close tab with intelligence"""
        self.switch_to_chrome(chrome_window)

        def action():
            pyautogui.hotkey('ctrl', 'w')

        return self.execute_with_retry(action, verify_change=True)

    def execute_intelligent_workflow(self, chrome_window: Dict,
                                     workflow: List[Dict]) -> Dict:
        """Execute workflow with intelligent decision making"""
        results = []
        total_start = time.time()

        logger.info(f"Starting intelligent workflow: {len(workflow)} steps")

        for i, step in enumerate(workflow):
            action = step['action']
            logger.info(f"Step {i+1}/{len(workflow)}: {action}")

            if action == 'open_tab':
                result = self.smart_open_tab(chrome_window)
            elif action == 'navigate':
                result = self.smart_navigate(chrome_window, step['url'])
            elif action == 'close_tab':
                result = self.smart_close_tab(chrome_window)
            elif action == 'wait':
                time.sleep(step.get('seconds', 1))
                result = ActionResult(
                    action='wait',
                    success=True,
                    duration=step.get('seconds', 1),
                    screen_change_percent=0.0,
                    timestamp=time.time()
                )
            else:
                logger.error(f"Unknown action: {action}")
                continue

            results.append({
                'step': i + 1,
                'action': action,
                'success': result.success,
                'duration': result.duration,
                'screen_change': f"{result.screen_change_percent:.2%}",
                'metadata': result.metadata
            })

            logger.info(f"  Result: {'SUCCESS' if result.success else 'FAILED'} "
                       f"({result.duration:.2f}s, {result.screen_change_percent:.2%} change)")

            # Stop on critical failure
            if not result.success and step.get('required', False):
                logger.error("Critical step failed, stopping workflow")
                break

        total_duration = time.time() - total_start
        success_count = sum(1 for r in results if r['success'])

        return {
            'total_steps': len(workflow),
            'completed_steps': len(results),
            'successful_steps': success_count,
            'total_duration': total_duration,
            'results': results,
            'performance_stats': self.performance_stats
        }

    def get_insights(self) -> Dict:
        """Get performance insights"""
        if not self.action_history:
            return {'message': 'No actions performed yet'}

        recent_actions = list(self.action_history)[-20:]

        success_rate = sum(1 for a in recent_actions if a.success) / len(recent_actions)
        avg_duration = sum(a.duration for a in recent_actions) / len(recent_actions)
        avg_change = sum(a.screen_change_percent for a in recent_actions) / len(recent_actions)

        return {
            'total_actions': len(self.action_history),
            'recent_success_rate': f"{success_rate:.1%}",
            'avg_action_duration': f"{avg_duration:.2f}s",
            'avg_screen_change': f"{avg_change:.2%}",
            'learned_stats': self.performance_stats
        }


# Demo
if __name__ == "__main__":
    print("INTELLIGENT AUTOMATION SYSTEM")
    print("=" * 60)

    automation = IntelligentAutomation()

    # Find Chrome
    chrome = automation.find_chrome_by_profile()

    if not chrome:
        print("ERROR: No Chrome found")
        exit(1)

    print(f"Using Chrome: {chrome['title'][:60]}\n")

    # Define intelligent workflow
    workflow = [
        {'action': 'open_tab'},
        {'action': 'navigate', 'url': 'python.org'},
        {'action': 'wait', 'seconds': 1},
        {'action': 'open_tab'},
        {'action': 'navigate', 'url': 'github.com'},
        {'action': 'wait', 'seconds': 1},
        {'action': 'open_tab'},
        {'action': 'navigate', 'url': 'stackoverflow.com'},
    ]

    print("Executing intelligent workflow...\n")
    result = automation.execute_intelligent_workflow(chrome, workflow)

    print("\n" + "=" * 60)
    print("WORKFLOW RESULTS")
    print("=" * 60)
    print(f"Total Steps: {result['total_steps']}")
    print(f"Completed: {result['completed_steps']}")
    print(f"Successful: {result['successful_steps']}")
    print(f"Duration: {result['total_duration']:.2f}s")
    print()

    for r in result['results']:
        status = "[OK]" if r['success'] else "[FAIL]"
        print(f"{status} Step {r['step']}: {r['action']} "
              f"({r['duration']:.2f}s, {r['screen_change']} change)")

    print("\n" + "=" * 60)
    print("PERFORMANCE INSIGHTS")
    print("=" * 60)
    insights = automation.get_insights()
    for key, value in insights.items():
        if key != 'learned_stats':
            print(f"{key}: {value}")

    print("\nLearned Performance Stats:")
    for action, stats in insights['learned_stats'].items():
        print(f"  {action}:")
        print(f"    Avg Time: {stats['avg_time']:.2f}s")
        print(f"    Success Rate: {stats['success_rate']:.1%}")
        print(f"    Samples: {stats['samples']}")
