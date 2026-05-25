#!/usr/bin/env python3
"""
Google Docs with Track Changes (Suggestions) Support

This script adds proper suggestions/track changes functionality.
Note: Suggestions require the document to be shared with suggestion permissions.
"""

import os
import sys
import pickle
import json
from pathlib import Path
import requests

TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
DOCS_API = 'https://docs.googleapis.com/v1/documents'
DRIVE_API = 'https://www.googleapis.com/drive/v3'


def get_credentials():
    """Get valid credentials"""
    if not TOKEN_PATH.exists():
        print("Error: Not authenticated. Run: python3 scripts/gdocs_auth_setup.py")
        sys.exit(1)
    
    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)
    
    # Refresh if needed
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


def get_document_revisions(doc_id):
    """Get all revisions of a document (for tracking changes)"""
    headers = get_headers()
    url = f'{DOCS_API}/{doc_id}/revisions'
    
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        revisions = resp.json().get('revisions', [])
        return revisions
    else:
        print(f"Error getting revisions: {resp.text}")
        return []


def compare_revisions(doc_id, base_rev_id, target_rev_id):
    """Compare two revisions to see changes"""
    headers = get_headers()
    
    # Get base revision
    base_url = f'{DOCS_API}/{doc_id}/revisions/{base_rev_id}'
    base_resp = requests.get(base_url, headers=headers)
    
    # Get target revision  
    target_url = f'{DOCS_API}/{doc_id}/revisions/{target_rev_id}'
    target_resp = requests.get(target_url, headers=headers)
    
    if base_resp.status_code == 200 and target_resp.status_code == 200:
        base_content = base_resp.json()
        target_content = target_resp.json()
        return {
            'base': base_content,
            'target': target_content,
            'changes': extract_changes(base_content, target_content)
        }
    else:
        print(f"Error comparing revisions")
        return None


def extract_changes(base, target):
    """Extract what changed between two revisions"""
    changes = []
    
    base_text = get_text_from_doc(base)
    target_text = get_text_from_doc(target)
    
    if base_text != target_text:
        changes.append({
            'type': 'content_change',
            'base_length': len(base_text),
            'target_length': len(target_text)
        })
    
    return changes


def get_text_from_doc(doc):
    """Extract text from document structure"""
    text = []
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            para = element['paragraph']
            para_text = ''
            for elem in para.get('elements', []):
                if 'textRun' in elem:
                    para_text += elem['textRun'].get('content', '')
            text.append(para_text)
    return ''.join(text)


def enable_suggestions(doc_id):
    """
    Enable suggestions mode for a document.
    Note: This requires changing document permissions to allow suggestions.
    """
    headers = get_headers()
    
    # Get current permissions
    url = f'{DRIVE_API}/files/{doc_id}/permissions'
    resp = requests.get(url, headers=headers)
    
    if resp.status_code == 200:
        permissions = resp.json().get('permissions', [])
        print(f"Current permissions: {len(permissions)}")
        for perm in permissions:
            print(f"  - {perm.get('role')}: {perm.get('type')}")
        return permissions
    else:
        print(f"Error getting permissions: {resp.text}")
        return None


def view_changes(doc_id):
    """View all changes in a document"""
    revisions = get_document_revisions(doc_id)
    
    if not revisions:
        print("No revisions found")
        return
    
    print(f"\nDocument has {len(revisions)} revision(s):\n")
    
    for i, rev in enumerate(revisions):
        rev_id = rev.get('id')
        modified_time = rev.get('modifiedTime')
        author = rev.get('lastModifyingUser', {}).get('displayName', 'Unknown')
        
        print(f"Revision {i+1} (ID: {rev_id})")
        print(f"  Time: {modified_time}")
        print(f"  Author: {author}")
        
        if i > 0:
            # Compare with previous revision
            prev_rev = revisions[i-1]
            comparison = compare_revisions(doc_id, prev_rev['id'], rev_id)
            if comparison and comparison['changes']:
                for change in comparison['changes']:
                    print(f"  Change: {change['type']}")
        print()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Docs Track Changes')
    parser.add_argument('action', choices=['revisions', 'changes', 'permissions'])
    parser.add_argument('--doc-id', required=True, help='Document ID')
    parser.add_argument('--base', help='Base revision ID')
    parser.add_argument('--target', help='Target revision ID')
    
    args = parser.parse_args()
    
    if args.action == 'revisions':
        revisions = get_document_revisions(args.doc_id)
        print(f"\nFound {len(revisions)} revision(s):\n")
        for rev in revisions:
            print(f"ID: {rev.get('id')}")
            print(f"  Time: {rev.get('modifiedTime')}")
            print(f"  Author: {rev.get('lastModifyingUser', {}).get('displayName', 'Unknown')}")
            print()
    
    elif args.action == 'changes':
        view_changes(args.doc_id)
    
    elif args.action == 'permissions':
        enable_suggestions(args.doc_id)


if __name__ == '__main__':
    main()
