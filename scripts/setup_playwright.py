#!/usr/bin/env python3
"""
Chrono24 Image Download - Attempt 1: Playwright with FlareSolverr
"""

import subprocess
import os

# Install playwright
subprocess.run(["pip3", "install", "playwright", "--break-system-packages"], check=True)

# Install browser
subprocess.run(["playwright", "install", "chromium"], check=True)

print("Playwright installed")
