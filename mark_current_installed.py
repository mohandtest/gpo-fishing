#!/usr/bin/env python3
"""
Quick script to mark the current latest commit as installed.
Run this to stop the updater from nagging about the current version.
"""

import sys
import os
sys.path.append('src')

from updater import UpdateManager

class MockApp:
    def __init__(self):
        self.main_loop_active = False

print("🔄 Marking current version as installed...")

app = MockApp()
updater = UpdateManager(app)

if updater.mark_current_as_installed():
    print("✅ Current version marked as installed! No more update prompts for this version.")
else:
    print("❌ Failed to mark current version as installed.")

input("Press Enter to exit...")