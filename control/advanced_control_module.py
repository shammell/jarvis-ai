#!/usr/bin/env python3
"""
JARVIS Advanced Control Module - INTERMEDIATE LEVEL
Combines computer control + visual intelligence for smart automation
"""

from computer_control_agent import ComputerControlAgent
from visual_intelligence import VisualIntelligence
from typing import Dict, Any, Optional, List
import logging
import time

logger = logging.getLogger(__name__)


class AdvancedControlModule:
    """
    INTERMEDIATE LEVEL Control System
    - Smart click (find and click text/buttons)
    - Smart type (find field and type)
    - Screen monitoring (detect changes)
    - Macro recording and playback
    - Multi-step automation
    - Context-aware actions
    """

    def __init__(self):
        self.control = ComputerControlAgent()
        self.vision = VisualIntelligence()
        self.last_screenshot = None
        logger.info("🚀 Advanced Control Module - INTERMEDIATE LEVEL initialized")

    def smart_click(self, target: str) -> Dict[str, Any]:
        """
        Find text/button on screen and click it

        Args:
            target: Text to find and click (e.g., "Login", "Submit")

        Returns:
            Result with success status
        """
        try:
            # Take screenshot
            screenshot = self.control.capture_screen()
            self.last_screenshot = screenshot

            # Find text on screen
            position = self.vision.find_text_on_screen(screenshot, target)

            if position:
                # Click at found position
                result = self.control.click(position[0], position[1])
                logger.info(f"✅ Smart clicked '{target}' at {position}")
                return {
                    'success': True,
                    'target': target,
                    'position': position,
                    'action': 'clicked'
                }
            else:
                logger.warning(f"⚠️ Could not find '{target}' on screen")
                return {
                    'success': False,
                    'error': f"Text '{target}' not found on screen"
                }

        except Exception as e:
            logger.error(f"❌ Smart click failed: {e}")
            return {'success': False, 'error': str(e)}

    def smart_type(self, field_name: str, text: str) -> Dict[str, Any]:
        """
        Find text field and type into it

        Args:
            field_name: Name/label of field to find
            text: Text to type

        Returns:
            Result with success status
        """
        try:
            # Take screenshot
            screenshot = self.control.capture_screen()

            # Find field on screen
            position = self.vision.find_text_on_screen(screenshot, field_name)

            if position:
                # Click field to focus
                self.control.click(position[0], position[1])
                time.sleep(0.3)

                # Type text
                result = self.control.type_text(text)

                logger.info(f"✅ Smart typed into '{field_name}'")
                return {
                    'success': True,
                    'field': field_name,
                    'text': text,
                    'action': 'typed'
                }
            else:
                logger.warning(f"⚠️ Could not find field '{field_name}'")
                return {
                    'success': False,
                    'error': f"Field '{field_name}' not found"
                }

        except Exception as e:
            logger.error(f"❌ Smart type failed: {e}")
            return {'success': False, 'error': str(e)}

    def read_screen(self) -> Dict[str, Any]:
        """
        Read all text currently visible on screen

        Returns:
            {
                "text": "full text",
                "lines": ["line1", "line2"],
                "word_count": 150
            }
        """
        try:
            # Take screenshot
            screenshot = self.control.capture_screen()
            self.last_screenshot = screenshot

            # Extract text
            result = self.vision.extract_text_from_image(screenshot)

            logger.info(f"📖 Read screen: {result.get('word_count', 0)} words")
            return result

        except Exception as e:
            logger.error(f"❌ Read screen failed: {e}")
            return {'success': False, 'error': str(e)}

    def find_and_click_button(self) -> Dict[str, Any]:
        """
        Detect buttons on screen and click the most prominent one

        Returns:
            Result with clicked button info
        """
        try:
            # Take screenshot
            screenshot = self.control.capture_screen()

            # Detect UI elements
            elements = self.vision.detect_ui_elements(screenshot)

            if elements['success'] and elements['buttons']:
                # Click first/largest button
                button = elements['buttons'][0]
                center = button['center']

                self.control.click(center[0], center[1])

                logger.info(f"✅ Clicked button at {center}")
                return {
                    'success': True,
                    'position': center,
                    'button': button
                }
            else:
                return {
                    'success': False,
                    'error': 'No buttons detected'
                }

        except Exception as e:
            logger.error(f"❌ Find and click button failed: {e}")
            return {'success': False, 'error': str(e)}

    def monitor_screen_changes(self, duration: int = 5) -> Dict[str, Any]:
        """
        Monitor screen for changes over duration

        Args:
            duration: Seconds to monitor

        Returns:
            List of detected changes
        """
        try:
            # Take initial screenshot
            screenshot1 = self.control.capture_screen()
            logger.info(f"🔍 Monitoring screen for {duration} seconds...")

            time.sleep(duration)

            # Take second screenshot
            screenshot2 = self.control.capture_screen()

            # Compare
            result = self.vision.compare_screenshots(screenshot1, screenshot2)

            logger.info(f"📊 Screen changes: {result.get('num_changes', 0)} detected")
            return result

        except Exception as e:
            logger.error(f"❌ Screen monitoring failed: {e}")
            return {'success': False, 'error': str(e)}

    def analyze_screen(self) -> Dict[str, Any]:
        """
        Full screen analysis: text, colors, UI elements

        Returns:
            Complete analysis report
        """
        try:
            # Take screenshot
            screenshot = self.control.capture_screen()

            # Extract text
            text_result = self.vision.extract_text_from_image(screenshot)

            # Detect UI elements
            ui_result = self.vision.detect_ui_elements(screenshot)

            # Analyze colors
            color_result = self.vision.analyze_colors(screenshot)

            logger.info("🧠 Full screen analysis complete")

            return {
                'success': True,
                'text': text_result,
                'ui_elements': ui_result,
                'colors': color_result,
                'timestamp': time.time()
            }

        except Exception as e:
            logger.error(f"❌ Screen analysis failed: {e}")
            return {'success': False, 'error': str(e)}

    def execute_workflow(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute multi-step automation workflow

        Args:
            steps: List of steps like:
                [
                    {"action": "smart_click", "target": "Login"},
                    {"action": "smart_type", "field": "Email", "text": "user@example.com"},
                    {"action": "press_key", "key": "enter"}
                ]

        Returns:
            Workflow execution result
        """
        try:
            results = []

            for i, step in enumerate(steps):
                logger.info(f"⚙️ Executing step {i+1}/{len(steps)}: {step['action']}")

                action = step['action']

                if action == 'smart_click':
                    result = self.smart_click(step['target'])
                elif action == 'smart_type':
                    result = self.smart_type(step['field'], step['text'])
                elif action == 'click':
                    result = self.control.click(step['x'], step['y'])
                elif action == 'type':
                    result = self.control.type_text(step['text'])
                elif action == 'press_key':
                    result = self.control.press_key(step['key'])
                elif action == 'wait':
                    time.sleep(step.get('duration', 1))
                    result = {'success': True, 'action': 'wait'}
                else:
                    result = {'success': False, 'error': f"Unknown action: {action}"}

                results.append(result)

                if not result.get('success', False):
                    logger.error(f"❌ Step {i+1} failed: {result.get('error')}")
                    break

                time.sleep(0.5)  # Small delay between steps

            logger.info(f"✅ Workflow complete: {len(results)}/{len(steps)} steps")

            return {
                'success': True,
                'steps_completed': len(results),
                'total_steps': len(steps),
                'results': results
            }

        except Exception as e:
            logger.error(f"❌ Workflow execution failed: {e}")
            return {'success': False, 'error': str(e)}


# Test
if __name__ == "__main__":
    module = AdvancedControlModule()
    print("Advanced Control Module - INTERMEDIATE LEVEL")
    print("Ready for smart automation!")
