#!/usr/bin/env python3
"""
Find GitHub repo URL from Chrome
"""

import win32gui
import win32process
import psutil

def find_github_tabs():
    """Find all Chrome tabs with GitHub"""
    chrome_windows = []

    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            try:
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
            except:
                pass
        return True

    win32gui.EnumWindows(callback, chrome_windows)

    # Find GitHub tabs
    github_tabs = []
    for window in chrome_windows:
        try:
            title_lower = window['title'].lower()
            if 'github' in title_lower:
                # Clean title for display
                clean_title = window['title'].encode('ascii', 'ignore').decode('ascii')
                github_tabs.append({
                    'title': clean_title,
                    'hwnd': window['hwnd']
                })
        except:
            pass

    return github_tabs

if __name__ == "__main__":
    tabs = find_github_tabs()

    if tabs:
        print("Found GitHub tabs:")
        for i, tab in enumerate(tabs, 1):
            print(f"{i}. {tab['title'][:80]}")
    else:
        print("No GitHub tabs found")
        print("\nPlease provide the GitHub repo URL manually.")
