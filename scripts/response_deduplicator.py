#!/usr/bin/env python3
"""
Response deduplication helper
Prevents sending duplicate messages
"""

from datetime import datetime, timedelta

class ResponseDeduplicator:
    def __init__(self):
        self.last_response = None
        self.last_response_time = None
        
    def is_duplicate(self, response_text):
        """Check if this response is a duplicate of the last one"""
        if not response_text or not self.last_response:
            return False
            
        # Normalize for comparison
        normalized_current = response_text.strip()[:200]
        normalized_last = self.last_response.strip()[:200]
        
        # Check if same content
        if normalized_current == normalized_last:
            # Check if within 5 seconds (same message batch)
            if self.last_response_time:
                time_diff = (datetime.now() - self.last_response_time).total_seconds()
                if time_diff < 5:
                    return True
        
        return False
    
    def record_response(self, response_text):
        """Record this response for future duplicate checking"""
        self.last_response = response_text
        self.last_response_time = datetime.now()

# Global instance
deduplicator = ResponseDeduplicator()
