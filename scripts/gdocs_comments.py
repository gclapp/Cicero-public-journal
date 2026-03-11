#!/usr/bin/env python3
"""
Google Docs Comment System - Add comments for review workflow
"""

import os
import sys
import pickle
from pathlib import Path
import requests

TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
DOCS_API = 'https://docs.googleapis.com/v1/documents'
DRIVE_API = 'https://www.googleapis.com/drive/v3'


def get_credentials():
    """Get valid credentials"""
    if not TOKEN_PATH.exists():
        print("Error: Not authenticated.")
        sys.exit(1)
    
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    
    if creds.expired and creds.refresh_token:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
    
    return creds


def get_headers():
    """Get auth headers"""
    creds = get_credentials()
    return {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }


def add_comment(doc_id, text, anchor_text=None, start_index=None, end_index=None):
    """Add a comment to the document"""
    headers = get_headers()
    
    # Build comment anchor
    if anchor_text:
        # Find the text in document
        doc_url = f'{DOCS_API}/{doc_id}'
        doc_resp = requests.get(doc_url, headers=headers)
        
        if doc_resp.status_code != 200:
            print(f"Error getting document: {doc_resp.text}")
            return False
        
        doc = doc_resp.json()
        full_text = ""
        text_positions = []
        
        # Build full text and track positions
        for element in doc.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for elem in element['paragraph'].get('elements', []):
                    if 'textRun' in elem:
                        content = elem['textRun'].get('content', '')
                        start = len(full_text) + 1  # 1-based indexing
                        full_text += content
                        end = len(full_text)
                        text_positions.append((start, end, content))
        
        # Find anchor text
        pos = full_text.find(anchor_text)
        if pos == -1:
            print(f"Anchor text '{anchor_text}' not found")
            return False
        
        start_index = pos + 1  # Convert to 1-based
        end_index = pos + len(anchor_text)
    
    # Create comment
    comment_url = f'{DRIVE_API}/files/{doc_id}/comments'
    
    comment_body = {
        'content': text,
        'anchor': {
            'r': {
                'd': {
                    'id': doc_id,
                    'startIndex': start_index,
                    'endIndex': end_index
                }
            }
        }
    }
    
    resp = requests.post(comment_url, headers=headers, json=comment_body, params={'fields': 'id,content,author,resolved'})
    
    if resp.status_code == 200:
        print(f"✅ Comment added: {text[:50]}...")
        return True
    else:
        print(f"Error adding comment: {resp.text}")
        return False


def list_comments(doc_id):
    """List all comments on a document"""
    headers = get_headers()
    
    url = f'{DRIVE_API}/files/{doc_id}/comments'
    resp = requests.get(url, headers=headers, params={'fields': 'comments(id,content,author,resolved)'})
    
    if resp.status_code == 200:
        comments = resp.json().get('comments', [])
        print(f"\nFound {len(comments)} comment(s):\n")
        for i, comment in enumerate(comments, 1):
            author = comment.get('author', {}).get('displayName', 'Unknown')
            content = comment.get('content', '')
            resolved = comment.get('resolved', False)
            status = "✅ Resolved" if resolved else "⏳ Open"
            print(f"{i}. [{status}] {author}: {content[:100]}...")
        return comments
    else:
        print(f"Error listing comments: {resp.text}")
        return []


def resolve_comment(doc_id, comment_id):
    """Mark a comment as resolved"""
    headers = get_headers()
    
    url = f'{DRIVE_API}/files/{doc_id}/comments/{comment_id}'
    body = {'resolved': True}
    
    resp = requests.patch(url, headers=headers, json=body)
    
    if resp.status_code == 200:
        print(f"✅ Comment resolved")
        return True
    else:
        print(f"Error resolving comment: {resp.text}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Docs Comments')
    parser.add_argument('action', choices=['add', 'list', 'resolve'])
    parser.add_argument('--doc-id', required=True, help='Document ID')
    parser.add_argument('--text', '-t', help='Comment text')
    parser.add_argument('--anchor', '-a', help='Text to anchor comment to')
    parser.add_argument('--comment-id', help='Comment ID to resolve')
    
    args = parser.parse_args()
    
    if args.action == 'add':
        if not args.text:
            print("Error: --text required")
            sys.exit(1)
        add_comment(args.doc_id, args.text, args.anchor)
    
    elif args.action == 'list':
        list_comments(args.doc_id)
    
    elif args.action == 'resolve':
        if not args.comment_id:
            print("Error: --comment-id required")
            sys.exit(1)
        resolve_comment(args.doc_id, args.comment_id)


if __name__ == '__main__':
    main()
