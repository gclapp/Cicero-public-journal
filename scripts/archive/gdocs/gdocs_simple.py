#!/usr/bin/env python3
"""
Google Docs Creator - Uses service account or existing gog auth
Creates new docs and appends content
"""

import os
import sys
import json
import pickle
from pathlib import Path

# Use the gdocs token we just created
def get_gdocs_token():
    """Get Google Docs authentication token"""
    token_path = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
    
    if token_path.exists():
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
            return creds
    return None


def create_doc_with_requests(title, content=None):
    """Create a Google Doc using raw API requests with existing auth"""
    import requests
    
    creds = get_gdocs_token()
    if not creds:
        print("Error: No valid credentials found")
        print("Please run: python3 scripts/gdocs_auth_setup.py")
        sys.exit(1)
    
    # Refresh if needed
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }
    
    # Create document
    create_url = 'https://docs.googleapis.com/v1/documents'
    create_body = {'title': title}
    
    resp = requests.post(create_url, headers=headers, json=create_body)
    if resp.status_code != 200:
        print(f"Error creating doc: {resp.text}")
        sys.exit(1)
    
    doc = resp.json()
    doc_id = doc['documentId']
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    print(f"Created: {title}")
    print(f"URL: {doc_url}")
    
    # Add content if provided
    if content:
        update_url = f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate'
        update_body = {
            'requests': [{
                'insertText': {
                    'location': {'index': 1},
                    'text': content
                }
            }]
        }
        resp = requests.post(update_url, headers=headers, json=update_body)
        if resp.status_code == 200:
            print("Content added successfully")
        else:
            print(f"Warning: Could not add content: {resp.text}")
    
    return doc_id, doc_url


def append_to_doc(doc_id, text):
    """Append text to end of existing doc"""
    import requests
    
    creds = get_gdocs_token()
    if not creds:
        print("Error: No valid credentials found")
        sys.exit(1)
    
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
    
    headers = {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }
    
    # Get current document to find end index
    get_url = f'https://docs.googleapis.com/v1/documents/{doc_id}'
    resp = requests.get(get_url, headers=headers)
    
    if resp.status_code != 200:
        print(f"Error getting doc: {resp.text}")
        sys.exit(1)
    
    doc = resp.json()
    content = doc.get('body', {}).get('content', [])
    end_index = content[-1].get('endIndex', 1) - 1 if content else 1
    
    # Append text
    update_url = f'https://docs.googleapis.com/v1/documents/{doc_id}:batchUpdate'
    update_body = {
        'requests': [{
            'insertText': {
                'location': {'index': end_index},
                'text': text
            }
        }]
    }
    
    resp = requests.post(update_url, headers=headers, json=update_body)
    if resp.status_code == 200:
        print(f"Appended text at position {end_index}")
    else:
        print(f"Error: {resp.text}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Simple Google Docs Editor')
    parser.add_argument('action', choices=['create', 'append'])
    parser.add_argument('--title', help='Document title (for create)')
    parser.add_argument('--doc-id', help='Document ID (for append)')
    parser.add_argument('--text', '-t', required=True, help='Text content')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        if not args.title:
            print("Error: --title required")
            sys.exit(1)
        doc_id, url = create_doc_with_requests(args.title, args.text)
        print(f"\nDoc ID: {doc_id}")
        
    elif args.action == 'append':
        if not args.doc_id:
            print("Error: --doc-id required")
            sys.exit(1)
        append_to_doc(args.doc_id, args.text)


if __name__ == '__main__':
    main()
