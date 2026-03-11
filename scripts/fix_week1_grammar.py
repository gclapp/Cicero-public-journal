#!/usr/bin/env python3
"""Fix grammar and formatting issues in the Week 1 blog post"""

import sys
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from gdocs_editor import get_credentials
import requests

DOC_ID = "1YrQldCbF0_QhNw3Y1PLfSIJMySmk-trGxQJZV-HIajg"

def get_headers():
    creds = get_credentials()
    return {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }

def find_and_replace(doc_id, old_text, new_text):
    """Find and replace text in document"""
    headers = get_headers()
    
    requests_list = [{
        'replaceAllText': {
            'containsText': {
                'text': old_text,
                'matchCase': True
            },
            'replaceText': new_text
        }
    }]
    
    body = {'requests': requests_list}
    
    resp = requests.post(
        f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate',
        headers=headers,
        json=body
    )
    
    if resp.status_code == 200:
        result = resp.json()
        replies = result.get('replies', [])
        if replies:
            occurrences = replies[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
            print(f"✅ Replaced '{old_text}' with '{new_text}' ({occurrences} occurrence(s))")
            return True
        else:
            print(f"⚠️ No occurrences of '{old_text}' found")
            return False
    else:
        print(f"❌ Error: {resp.text}")
        return False

# Fix 1: Familiarr -> Familiar
find_and_replace(DOC_ID, "Familiarr", "Familiar")

# Fix 2: Add line break between sections
find_and_replace(DOC_ID, "The Mirror of Setup: Who Are You, Really?The Personal", "The Mirror of Setup: Who Are You, Really?\n\nThe Personal")

print("\n✅ Grammar fixes applied!")
