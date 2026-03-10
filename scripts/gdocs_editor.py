#!/usr/bin/env python3
"""
Google Docs Editor - Full-featured with formatting, positioning, and suggestions
"""

import os
import sys
import pickle
import json
import re
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import requests

TOKEN_PATH = Path.home() / '.openclaw' / 'credentials' / 'gdocs-token.pickle'
DOCS_API = 'https://docs.googleapis.com/v1/documents'


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
        # Save refreshed token
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)
    
    return creds


def get_headers():
    """Get auth headers for API calls"""
    creds = get_credentials()
    return {
        'Authorization': f'Bearer {creds.token}',
        'Content-Type': 'application/json'
    }


def get_document(doc_id):
    """Get full document structure"""
    headers = get_headers()
    resp = requests.get(f'{DOCS_API}/{doc_id}', headers=headers)
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return None
    return resp.json()


def get_end_index(doc_id):
    """Get the end index of document content"""
    doc = get_document(doc_id)
    if not doc:
        return 1
    content = doc.get('body', {}).get('content', [])
    if content:
        return content[-1].get('endIndex', 1) - 1
    return 1


def find_text_position(doc_id, search_text):
    """Find the position of text in document"""
    doc = get_document(doc_id)
    if not doc:
        return None
    
    full_text = ""
    for element in doc.get('body', {}).get('content', []):
        if 'paragraph' in element:
            for elem in element['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    full_text += elem['textRun'].get('content', '')
    
    pos = full_text.find(search_text)
    if pos == -1:
        return None
    return pos + 1  # Google Docs uses 1-based indexing


def create_document(title, content=None, suggestions=False):
    """Create a new Google Doc"""
    headers = get_headers()
    
    # Create blank document
    resp = requests.post(DOCS_API, headers=headers, json={'title': title})
    if resp.status_code != 200:
        print(f"Error creating doc: {resp.text}")
        return None, None
    
    doc = resp.json()
    doc_id = doc['documentId']
    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    
    print(f"Created: {title}")
    print(f"URL: {doc_url}")
    
    # Add content if provided
    if content:
        insert_text(doc_id, content, index=1, suggestions=suggestions)
    
    return doc_id, doc_url


def insert_text(doc_id, text, index=None, bold=False, italic=False, 
                heading=None, font_size=None, suggestions=False):
    """Insert text with optional formatting at specific position"""
    headers = get_headers()
    
    if index is None:
        index = get_end_index(doc_id)
    
    requests_list = [{
        'insertText': {
            'location': {'index': index},
            'text': text
        }
    }]
    
    # Apply formatting
    end_index = index + len(text)
    text_style = {}
    fields = []
    
    if bold:
        text_style['bold'] = True
        fields.append('bold')
    if italic:
        text_style['italic'] = True
        fields.append('italic')
    if font_size:
        text_style['fontSize'] = {'magnitude': font_size, 'unit': 'PT'}
        fields.append('fontSize')
    
    if text_style:
        requests_list.append({
            'updateTextStyle': {
                'range': {'startIndex': index, 'endIndex': end_index},
                'textStyle': text_style,
                'fields': ','.join(fields)
            }
        })
    
    # Apply heading style
    if heading:
        requests_list.append({
            'updateParagraphStyle': {
                'range': {'startIndex': index, 'endIndex': end_index},
                'paragraphStyle': {'namedStyleType': heading},
                'fields': 'namedStyleType'
            }
        })
    
    body = {'requests': requests_list}
    if suggestions:
        body['writeControl'] = {'targetRevisionId': 'suggestions'}
    
    resp = requests.post(f'{DOCS_API}/{doc_id}:batchUpdate', 
                        headers=headers, json=body)
    
    if resp.status_code == 200:
        print(f"Inserted text at position {index}")
        return True
    else:
        print(f"Error: {resp.text}")
        return False


def replace_text(doc_id, old_text, new_text, suggestions=False):
    """Replace all occurrences of text"""
    headers = get_headers()
    
    requests_list = [{
        'replaceAllText': {
            'containsText': {'text': old_text, 'matchCase': True},
            'replaceText': new_text
        }
    }]
    
    body = {'requests': requests_list}
    if suggestions:
        body['writeControl'] = {'targetRevisionId': 'suggestions'}
    
    resp = requests.post(f'{DOCS_API}/{doc_id}:batchUpdate',
                        headers=headers, json=body)
    
    if resp.status_code == 200:
        result = resp.json()
        matches = result.get('replies', [{}])[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
        print(f"Replaced '{old_text}' with '{new_text}' ({matches} occurrences)")
        return True
    else:
        print(f"Error: {resp.text}")
        return False


def delete_text(doc_id, start_index, end_index, suggestions=False):
    """Delete text at specific range"""
    headers = get_headers()
    
    requests_list = [{
        'deleteContentRange': {
            'range': {'startIndex': start_index, 'endIndex': end_index}
        }
    }]
    
    body = {'requests': requests_list}
    if suggestions:
        body['writeControl'] = {'targetRevisionId': 'suggestions'}
    
    resp = requests.post(f'{DOCS_API}/{doc_id}:batchUpdate',
                        headers=headers, json=body)
    
    if resp.status_code == 200:
        print(f"Deleted text from {start_index} to {end_index}")
        return True
    else:
        print(f"Error: {resp.text}")
        return False


def export_as_text(doc_id):
    """Export document as plain text"""
    doc = get_document(doc_id)
    if not doc:
        return None
    
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


def get_suggestions(doc_id):
    """Get pending suggestions (requires Drive API)"""
    headers = get_headers()
    
    # Get document with suggestions
    resp = requests.get(f'{DOCS_API}/{doc_id}?suggestionsViewMode=SUGGESTIONS_INLINE',
                       headers=headers)
    
    if resp.status_code != 200:
        print(f"Error: {resp.text}")
        return None
    
    doc = resp.json()
    
    # Extract suggestions
    suggestions = []
    for content in doc.get('body', {}).get('content', []):
        if 'paragraph' in content:
            for elem in content['paragraph'].get('elements', []):
                if 'textRun' in elem:
                    text_run = elem['textRun']
                    if 'suggestedInsertionIds' in text_run:
                        suggestions.append({
                            'type': 'insertion',
                            'text': text_run.get('content', ''),
                            'ids': text_run['suggestedInsertionIds']
                        })
                    if 'suggestedDeletionIds' in text_run:
                        suggestions.append({
                            'type': 'deletion',
                            'text': text_run.get('content', ''),
                            'ids': text_run['suggestedDeletionIds']
                        })
    
    return suggestions


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Google Docs Editor')
    subparsers = parser.add_subparsers(dest='action', help='Action to perform')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create new document')
    create_parser.add_argument('--title', required=True, help='Document title')
    create_parser.add_argument('--text', '-t', help='Initial content')
    create_parser.add_argument('--suggestions', action='store_true', 
                               help='Insert as suggestions')
    
    # Insert command
    insert_parser = subparsers.add_parser('insert', help='Insert text')
    insert_parser.add_argument('--doc-id', required=True, help='Document ID')
    insert_parser.add_argument('--text', '-t', required=True, help='Text to insert')
    insert_parser.add_argument('--index', type=int, help='Position (default: end)')
    insert_parser.add_argument('--after', help='Insert after this text')
    insert_parser.add_argument('--bold', action='store_true', help='Bold text')
    insert_parser.add_argument('--italic', action='store_true', help='Italic text')
    insert_parser.add_argument('--heading', choices=['HEADING_1', 'HEADING_2', 'HEADING_3'],
                               help='Heading style')
    insert_parser.add_argument('--font-size', type=int, help='Font size in points')
    insert_parser.add_argument('--suggestions', action='store_true',
                               help='Insert as suggestion')
    
    # Replace command
    replace_parser = subparsers.add_parser('replace', help='Replace text')
    replace_parser.add_argument('--doc-id', required=True, help='Document ID')
    replace_parser.add_argument('--old', required=True, help='Text to find')
    replace_parser.add_argument('--new', required=True, help='Replacement text')
    replace_parser.add_argument('--suggestions', action='store_true',
                               help='Replace as suggestion')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete text range')
    delete_parser.add_argument('--doc-id', required=True, help='Document ID')
    delete_parser.add_argument('--start', type=int, required=True, help='Start index')
    delete_parser.add_argument('--end', type=int, required=True, help='End index')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export as text')
    export_parser.add_argument('--doc-id', required=True, help='Document ID')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get document JSON')
    get_parser.add_argument('--doc-id', required=True, help='Document ID')
    
    # Suggestions command
    sugg_parser = subparsers.add_parser('suggestions', help='View pending suggestions')
    sugg_parser.add_argument('--doc-id', required=True, help='Document ID')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        doc_id, url = create_document(args.title, args.text, args.suggestions)
        if doc_id:
            print(f"Doc ID: {doc_id}")
    
    elif args.action == 'insert':
        index = args.index
        if args.after and not index:
            index = find_text_position(args.doc_id, args.after)
            if index:
                index += len(args.after)
            else:
                print(f"Text '{args.after}' not found, appending to end")
                index = None
        
        insert_text(args.doc_id, args.text, index, args.bold, args.italic,
                   args.heading, args.font_size, args.suggestions)
    
    elif args.action == 'replace':
        replace_text(args.doc_id, args.old, args.new, args.suggestions)
    
    elif args.action == 'delete':
        delete_text(args.doc_id, args.start, args.end)
    
    elif args.action == 'export':
        text = export_as_text(args.doc_id)
        if text:
            print(text)
    
    elif args.action == 'get':
        doc = get_document(args.doc_id)
        if doc:
            print(json.dumps(doc, indent=2))
    
    elif args.action == 'suggestions':
        suggs = get_suggestions(args.doc_id)
        if suggs:
            print(f"Found {len(suggs)} suggestions:")
            for s in suggs:
                print(f"  [{s['type']}] {repr(s['text'][:50])}")
        else:
            print("No pending suggestions")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
