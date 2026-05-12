#!/usr/bin/env python3
"""
Flight Email Filter - Demo Mode
Shows what emails would be filtered without actually connecting
"""

import re

# Patterns for emails to AUTO-ARCHIVE (unhelpful)
AUTO_ARCHIVE_PATTERNS = [
    r'flight status changed from pending to scheduled',
    r'flight status: scheduled\s*$',
    r'booking confirmed.*flight.*scheduled',
    r'reservation confirmed.*flight',
]

# Patterns for emails to KEEP (important)
IMPORTANT_PATTERNS = [
    r'delayed',
    r'cancelled',
    r'cancellation',
    r'gate change',
    r'departure time change',
    r'arrival time change',
    r'flight time change',
    r'schedule change',
    r'flight change',
    r'diverted',
]

def should_archive(subject):
    """Check if email should be auto-archived"""
    text = subject.lower()
    
    # Check if it matches important patterns first
    for pattern in IMPORTANT_PATTERNS:
        if re.search(pattern, text):
            return False  # Keep important emails
    
    # Check if it matches auto-archive patterns
    for pattern in AUTO_ARCHIVE_PATTERNS:
        if re.search(pattern, text):
            return True  # Archive unhelpful emails
    
    return False  # Default: keep email

# Test examples
test_subjects = [
    "Flight Status changed from pending to scheduled - DL1234",
    "Flight Status changed from scheduled to delayed - DL1234",
    "Your flight DL1234 has been cancelled",
    "Gate change for flight DL1234",
    "Booking confirmed - Flight scheduled",
    "Flight Status: Scheduled",
    "Your flight has been delayed 30 minutes",
]

print("Flight Email Filter - Test Results:")
print("=" * 60)
for subject in test_subjects:
    action = "ARCHIVE" if should_archive(subject) else "KEEP"
    print(f"[{action:8}] {subject}")
