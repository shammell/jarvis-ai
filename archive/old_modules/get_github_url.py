#!/usr/bin/env python3
"""
Get GitHub URL from current Chrome tab
"""

import win32gui
import win32process
import psutil
import pyautogui
import time

def find_chrome():
    """Find Chrome window"""
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

    # Find GitHub tab
    for window in chrome_windows:
        if 'github' in window['title'].lower():
            return window

    return chrome_windows[0] if chrome_windows else None

def get_url_from_chrome(chrome_window):
    """Get URL from Chrome address bar"""
    # Switch to Chrome
    win32gui.SetForegroundWindow(chrome_window['hwnd'])
    time.sleep(0.3)

    # Focus address bar
    pyautogui.hotkey('ctrl', 'l')
    time.sleep(0.2)

    # Copy URL
    pyautogui.hotkey('ctrl', 'c')
    time.sleep(0.2)

    # Press Escape to unfocus
    pyautogui.press('escape')

    print(f"Chrome Title: {chrome_window['title']}")
    print("\nURL copied to clipboard!")
    print("Please paste the URL here.")

if __name__ == "__main__":
    chrome = find_chrome()
    if chrome:
        get_url_from_chrome(chrome)
    else:
        print("No Chrome found")
