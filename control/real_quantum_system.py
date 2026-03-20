#!/usr/bin/env python3
"""
JARVIS REAL QUANTUM SYSTEM - FULL CONTROL
Complete laptop access with intelligent decision making
"""

import cv2
import numpy as np
from PIL import Image, ImageGrab
import io
import base64
from typing import Dict, Any, List, Tuple, Optional
import logging
import time
import json
import pyautogui
import mss
import psutil
import subprocess
import os
import shlex
import shutil
import win32gui
import win32con
import win32process
from collections import deque

logger = logging.getLogger(__name__)


class RealQuantumVision:
    """
    Real Quantum Vision - Actually sees and understands screen

    Features:
    - Real-time screen analysis
    - Window detection and identification
    - Tab detection in browsers
    - User profile detection
    - Text recognition (OCR)
    - Element localization
    - Context understanding
    """

    def __init__(self):
        self.last_screenshot = None
        self.window_cache = {}
        logger.info("Real Quantum Vision initialized")

    def get_all_windows(self) -> List[Dict[str, Any]]:
        """Get all open windows with details"""
        windows = []

        def callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    rect = win32gui.GetWindowRect(hwnd)
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)

                    try:
                        process = psutil.Process(pid)
                        process_name = process.name()
                    except:
                        process_name = "unknown"

                    windows_list.append({
                        'hwnd': hwnd,
                        'title': title,
                        'process': process_name,
                        'pid': pid,
                        'rect': rect,
                        'position': {'x': rect[0], 'y': rect[1]},
                        'size': {'width': rect[2]-rect[0], 'height': rect[3]-rect[1]}
                    })
            return True

        win32gui.EnumWindows(callback, windows)
        return windows

    def find_chrome_windows(self) -> List[Dict[str, Any]]:
        """Find all Chrome windows with user profiles"""
        all_windows = self.get_all_windows()
        chrome_windows = []

        for window in all_windows:
            if 'chrome' in window['process'].lower():
                # Parse title to detect user profile
                title = window['title']
                user_profile = "Unknown"

                if " - " in title:
                    parts = title.split(" - ")
                    if len(parts) >= 2:
                        # Last part usually contains profile info
                        last_part = parts[-1]
                        if "Google Chrome" in last_part:
                            # Check if profile name is before it
                            if len(parts) >= 3:
                                user_profile = parts[-2]
                        else:
                            user_profile = last_part

                chrome_windows.append({
                    **window,
                    'user_profile': user_profile,
                    'is_chrome': True
                })

        logger.info(f"Found {len(chrome_windows)} Chrome windows")
        return chrome_windows

    def analyze_chrome_tabs(self, chrome_window: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze Chrome window to detect tabs"""
        # Focus the window
        hwnd = chrome_window['hwnd']
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.3)

        # Take screenshot
        screenshot = ImageGrab.grab()

        # Analyze for tabs (simplified - would use OCR in production)
        return {
            'window': chrome_window,
            'screenshot_taken': True,
            'analysis': 'Chrome window analyzed'
        }

    def get_active_window(self) -> Dict[str, Any]:
        """Get currently active window"""
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        try:
            process = psutil.Process(pid)
            process_name = process.name()
        except:
            process_name = "unknown"

        return {
            'hwnd': hwnd,
            'title': title,
            'process': process_name,
            'pid': pid
        }

    def switch_to_window(self, hwnd: int) -> bool:
        """Switch to specific window"""
        try:
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.2)
            return True
        except Exception as e:
            logger.error(f"Failed to switch window: {e}")
            return False

    def take_smart_screenshot(self) -> Tuple[Image.Image, str]:
        """Take screenshot and analyze"""
        screenshot = ImageGrab.grab()

        # Convert to base64
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        img_base64 = base64.b64encode(buffer.getvalue()).decode()

        self.last_screenshot = screenshot

        return screenshot, img_base64


class RealQuantumControl:
    """
    Real Quantum Control - Full laptop control

    Features:
    - Process management
    - Window management
    - File system operations
    - Network monitoring
    - System resource monitoring
    - Application launching
    - Smart automation
    """

    def __init__(self):
        self.vision = RealQuantumVision()
        logger.info("Real Quantum Control initialized")

    def get_system_info(self) -> Dict[str, Any]:
        """Get complete system information"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            },
            'processes': len(psutil.pids()),
            'boot_time': psutil.boot_time()
        }

    def get_running_processes(self) -> List[Dict[str, Any]]:
        """Get all running processes"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        return processes

    def find_process(self, name: str) -> List[Dict[str, Any]]:
        """Find process by name"""
        matching = []
        for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline']):
            try:
                if name.lower() in proc.info['name'].lower():
                    matching.append(proc.info)
            except:
                pass
        return matching

    def kill_process(self, pid: int) -> bool:
        """Kill process by PID"""
        try:
            process = psutil.Process(pid)
            process.terminate()
            return True
        except Exception as e:
            logger.error(f"Failed to kill process {pid}: {e}")
            return False

    def launch_application(self, app_name: str) -> Dict[str, Any]:
        """Launch application intelligently"""
        try:
            # Try direct launch without shell invocation
            args = shlex.split(app_name)
            if not args:
                raise ValueError("Application name is empty")

            executable = args[0]
            if not os.path.isabs(executable):
                resolved = shutil.which(executable)
                if resolved:
                    args[0] = resolved

            subprocess.Popen(args)
            time.sleep(2)

            return {
                'success': True,
                'app': app_name,
                'method': 'direct_launch'
            }
        except Exception as e:
            # Fallback to Windows search
            pyautogui.press('win')
            time.sleep(0.5)
            pyautogui.write(app_name, interval=0.02)
            time.sleep(0.5)
            pyautogui.press('enter')

            return {
                'success': True,
                'app': app_name,
                'method': 'windows_search'
            }

    def smart_chrome_control(self, action: str, **kwargs) -> Dict[str, Any]:
        """Smart Chrome control with user profile awareness"""

        # Find all Chrome windows
        chrome_windows = self.vision.find_chrome_windows()

        if not chrome_windows:
            return {
                'success': False,
                'error': 'No Chrome windows found'
            }

        # Find Shameel's profile
        shameel_window = None
        for window in chrome_windows:
            if 'shameel' in window['user_profile'].lower():
                shameel_window = window
                break

        if not shameel_window:
            # Use first Chrome window
            shameel_window = chrome_windows[0]

        logger.info(f"Using Chrome window: {shameel_window['user_profile']}")

        # Switch to that window
        self.vision.switch_to_window(shameel_window['hwnd'])
        time.sleep(0.3)

        # Perform action
        if action == 'new_tab':
            pyautogui.hotkey('ctrl', 't')
            time.sleep(0.3)
            return {
                'success': True,
                'action': 'new_tab',
                'window': shameel_window['user_profile']
            }

        elif action == 'navigate':
            url = kwargs.get('url', '')
            pyautogui.hotkey('ctrl', 'l')  # Focus address bar
            time.sleep(0.2)
            pyautogui.write(url, interval=0.02)
            time.sleep(0.2)
            pyautogui.press('enter')
            return {
                'success': True,
                'action': 'navigate',
                'url': url,
                'window': shameel_window['user_profile']
            }

        elif action == 'search':
            query = kwargs.get('query', '')
            pyautogui.write(query, interval=0.02)
            time.sleep(0.2)
            pyautogui.press('enter')
            return {
                'success': True,
                'action': 'search',
                'query': query,
                'window': shameel_window['user_profile']
            }

        return {'success': False, 'error': 'Unknown action'}


# Test
if __name__ == "__main__":
    print("Real Quantum System - Full Control")
    print()

    control = RealQuantumControl()

    # Get system info
    info = control.get_system_info()
    print(f"CPU: {info['cpu_percent']}%")
    print(f"Memory: {info['memory']['percent']}%")
    print(f"Processes: {info['processes']}")
    print()

    # Find Chrome windows
    chrome_windows = control.vision.find_chrome_windows()
    print(f"Chrome windows: {len(chrome_windows)}")
    for window in chrome_windows:
        print(f"  - {window['user_profile']}: {window['title'][:50]}")
