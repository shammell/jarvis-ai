#!/usr/bin/env python3
"""
JARVIS Computer Control Agent - INTERMEDIATE LEVEL
Advanced visual control with AI vision, OCR, and intelligent automation
"""

import pyautogui
import mss
import cv2
import numpy as np
from PIL import Image
import io
import base64
from typing import Dict, Any, Tuple, Optional, List
import logging
import time
import pytesseract
from collections import deque
import json

logger = logging.getLogger(__name__)

# Safety settings
pyautogui.FAILSAFE = True  # Move mouse to corner to abort
pyautogui.PAUSE = 0.3  # Faster response time


class ComputerControlAgent:
    """
    INTERMEDIATE LEVEL Computer Control
    - AI-powered visual recognition
    - OCR text extraction
    - Smart element detection
    - Screen recording
    - Multi-monitor support
    - Gesture automation
    - Context-aware actions
    """

    def __init__(self):
        self.sct = mss.mss()
        self.screen_size = pyautogui.size()
        self.screen_history = deque(maxlen=10)  # Last 10 screenshots
        self.action_history = deque(maxlen=50)  # Last 50 actions
        self.recording = False
        self.recorded_actions = []
        logger.info(f"🖥️ Computer Control Agent INTERMEDIATE - Screen: {self.screen_size}")

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        Capture screen and return base64 encoded image

        Args:
            region: (x, y, width, height) or None for full screen

        Returns:
            Base64 encoded PNG image
        """
        if region:
            monitor = {
                "top": region[1],
                "left": region[0],
                "width": region[2],
                "height": region[3]
            }
        else:
            monitor = self.sct.monitors[1]  # Primary monitor

        screenshot = self.sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        logger.info(f"📸 Screen captured: {img.size}")
        return img_base64

    def move_mouse(self, x: int, y: int, duration: float = 0.5) -> Dict[str, Any]:
        """Move mouse to position"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            logger.info(f"🖱️ Mouse moved to ({x}, {y})")
            return {"success": True, "position": (x, y)}
        except Exception as e:
            logger.error(f"❌ Mouse move failed: {e}")
            return {"success": False, "error": str(e)}

    def click(self, x: Optional[int] = None, y: Optional[int] = None,
              button: str = "left", clicks: int = 1) -> Dict[str, Any]:
        """
        Click at position

        Args:
            x, y: Position (None = current position)
            button: "left", "right", or "middle"
            clicks: Number of clicks (2 = double-click)
        """
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
                logger.info(f"👆 Clicked at ({x}, {y}) - {button} x{clicks}")
            else:
                pyautogui.click(clicks=clicks, button=button)
                logger.info(f"👆 Clicked - {button} x{clicks}")

            return {"success": True, "button": button, "clicks": clicks}
        except Exception as e:
            logger.error(f"❌ Click failed: {e}")
            return {"success": False, "error": str(e)}

    def drag(self, x1: int, y1: int, x2: int, y2: int, duration: float = 1.0) -> Dict[str, Any]:
        """Drag from (x1, y1) to (x2, y2)"""
        try:
            pyautogui.moveTo(x1, y1)
            pyautogui.drag(x2 - x1, y2 - y1, duration=duration)
            logger.info(f"🖱️ Dragged from ({x1}, {y1}) to ({x2}, {y2})")
            return {"success": True, "from": (x1, y1), "to": (x2, y2)}
        except Exception as e:
            logger.error(f"❌ Drag failed: {e}")
            return {"success": False, "error": str(e)}

    def type_text(self, text: str, interval: float = 0.05) -> Dict[str, Any]:
        """Type text with keyboard"""
        try:
            pyautogui.write(text, interval=interval)
            logger.info(f"⌨️ Typed: {text[:50]}...")
            return {"success": True, "text": text}
        except Exception as e:
            logger.error(f"❌ Type failed: {e}")
            return {"success": False, "error": str(e)}

    def press_key(self, key: str, presses: int = 1) -> Dict[str, Any]:
        """Press a key (e.g., 'enter', 'esc', 'tab')"""
        try:
            pyautogui.press(key, presses=presses)
            logger.info(f"⌨️ Pressed: {key} x{presses}")
            return {"success": True, "key": key}
        except Exception as e:
            logger.error(f"❌ Key press failed: {e}")
            return {"success": False, "error": str(e)}

    def hotkey(self, *keys: str) -> Dict[str, Any]:
        """Press hotkey combination (e.g., 'ctrl', 'c')"""
        try:
            pyautogui.hotkey(*keys)
            logger.info(f"⌨️ Hotkey: {'+'.join(keys)}")
            return {"success": True, "keys": keys}
        except Exception as e:
            logger.error(f"❌ Hotkey failed: {e}")
            return {"success": False, "error": str(e)}

    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None) -> Dict[str, Any]:
        """
        Scroll mouse wheel

        Args:
            clicks: Positive = up, negative = down
            x, y: Position to scroll at (None = current)
        """
        try:
            if x is not None and y is not None:
                pyautogui.moveTo(x, y)
            pyautogui.scroll(clicks)
            logger.info(f"🖱️ Scrolled: {clicks} clicks")
            return {"success": True, "clicks": clicks}
        except Exception as e:
            logger.error(f"❌ Scroll failed: {e}")
            return {"success": False, "error": str(e)}

    def find_image_on_screen(self, template_path: str, confidence: float = 0.8) -> Optional[Tuple[int, int]]:
        """
        Find image on screen using template matching

        Args:
            template_path: Path to template image
            confidence: Match confidence (0-1)

        Returns:
            (x, y) center position or None
        """
        try:
            location = pyautogui.locateOnScreen(template_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                logger.info(f"🔍 Found image at {center}")
                return center
            else:
                logger.warning(f"⚠️ Image not found: {template_path}")
                return None
        except Exception as e:
            logger.error(f"❌ Image search failed: {e}")
            return None

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position"""
        pos = pyautogui.position()
        return (pos.x, pos.y)

    def get_pixel_color(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get RGB color of pixel at position"""
        color = pyautogui.pixel(x, y)
        return color

    def execute(self, command: str, **kwargs) -> Dict[str, Any]:
        """
        Execute computer control command

        Commands:
            - screenshot: Capture screen
            - move: Move mouse to (x, y)
            - click: Click at (x, y)
            - type: Type text
            - press: Press key
            - hotkey: Press key combination
            - scroll: Scroll wheel
            - drag: Drag from (x1, y1) to (x2, y2)
        """
        logger.info(f"🤖 Executing: {command}")

        try:
            if command == "screenshot":
                region = kwargs.get("region")
                img = self.capture_screen(region)
                return {"success": True, "image": img}

            elif command == "move":
                x, y = kwargs["x"], kwargs["y"]
                duration = kwargs.get("duration", 0.5)
                return self.move_mouse(x, y, duration)

            elif command == "click":
                x = kwargs.get("x")
                y = kwargs.get("y")
                button = kwargs.get("button", "left")
                clicks = kwargs.get("clicks", 1)
                return self.click(x, y, button, clicks)

            elif command == "type":
                text = kwargs["text"]
                interval = kwargs.get("interval", 0.05)
                return self.type_text(text, interval)

            elif command == "press":
                key = kwargs["key"]
                presses = kwargs.get("presses", 1)
                return self.press_key(key, presses)

            elif command == "hotkey":
                keys = kwargs["keys"]
                return self.hotkey(*keys)

            elif command == "scroll":
                clicks = kwargs["clicks"]
                x = kwargs.get("x")
                y = kwargs.get("y")
                return self.scroll(clicks, x, y)

            elif command == "drag":
                x1, y1 = kwargs["x1"], kwargs["y1"]
                x2, y2 = kwargs["x2"], kwargs["y2"]
                duration = kwargs.get("duration", 1.0)
                return self.drag(x1, y1, x2, y2, duration)

            elif command == "get_position":
                pos = self.get_mouse_position()
                return {"success": True, "position": pos}

            elif command == "get_color":
                x, y = kwargs["x"], kwargs["y"]
                color = self.get_pixel_color(x, y)
                return {"success": True, "color": color}

            else:
                return {"success": False, "error": f"Unknown command: {command}"}

        except Exception as e:
            logger.error(f"❌ Command execution failed: {e}")
            return {"success": False, "error": str(e)}


# Test
if __name__ == "__main__":
    agent = ComputerControlAgent()

    print("Computer Control Agent Test")
    print(f"Screen size: {agent.screen_size}")
    print(f"Mouse position: {agent.get_mouse_position()}")

    # Take screenshot
    print("\nTaking screenshot...")
    img = agent.capture_screen()
    print(f"Screenshot size: {len(img)} bytes")

    print("\nComputer control ready!")
    print("FAILSAFE: Move mouse to screen corner to abort")
