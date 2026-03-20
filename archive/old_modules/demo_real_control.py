#!/usr/bin/env python3
"""
REAL DEMONSTRATION - Shameel's Chrome Control
Actually detect and control the existing Chrome instance
"""

import win32gui
import win32process
import psutil
import time
import pyautogui

def find_shameel_chrome():
    """Find Shameel's Chrome window"""
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
                except:
                    pass
        return True

    win32gui.EnumWindows(callback, chrome_windows)

    # Find Shameel's profile
    for window in chrome_windows:
        title = window['title'].lower()
        if 'shameel' in title or 'google chrome' in title:
            return window

    # Return first Chrome window if Shameel not found
    return chrome_windows[0] if chrome_windows else None

def get_chrome_tabs_info(chrome_window):
    """Get info about Chrome tabs"""
    print(f"\n=== Chrome Window Detected ===")
    print(f"Title: {chrome_window['title']}")
    print(f"PID: {chrome_window['pid']}")
    print(f"HWND: {chrome_window['hwnd']}")

    # Get process info
    try:
        process = psutil.Process(chrome_window['pid'])
        print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"CPU: {process.cpu_percent(interval=0.1)}%")
    except:
        pass

def switch_and_control(chrome_window):
    """Switch to Chrome and perform action"""
    print(f"\n=== Switching to Chrome ===")

    # Bring window to front
    win32gui.SetForegroundWindow(chrome_window['hwnd'])
    time.sleep(0.5)

    print("Chrome window is now active")
    print("\nDemonstrating control:")
    print("1. Opening new tab...")

    # Open new tab
    pyautogui.hotkey('ctrl', 't')
    time.sleep(0.5)

    print("2. Navigating to example.com...")
    pyautogui.write('example.com', interval=0.02)
    time.sleep(0.3)
    pyautogui.press('enter')

    print("\n=== Control Demonstrated ===")
    print("[OK] Found your Chrome")
    print("[OK] Switched to it")
    print("[OK] Opened new tab")
    print("[OK] Navigated to example.com")

if __name__ == "__main__":
    print("REAL CHROME CONTROL DEMO")
    print("=" * 50)

    # Find Shameel's Chrome
    chrome = find_shameel_chrome()

    if not chrome:
        print("ERROR: No Chrome windows found!")
        exit(1)

    # Show info
    get_chrome_tabs_info(chrome)

    # Demonstrate control automatically
    print("\n" + "=" * 50)
    print("Demonstrating control in 2 seconds...")
    time.sleep(2)

    switch_and_control(chrome)

    print("\n" + "=" * 50)
    print("Demo complete!")
