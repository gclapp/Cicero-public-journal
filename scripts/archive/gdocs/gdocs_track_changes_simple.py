#!/usr/bin/env python3
"""
Track changes between document versions
Compare current document to last saved version
"""

import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from gdocs_editor import get_document, export_as_text

SNAPSHOT_DIR = Path('/home/ubuntu/.openclaw/workspace/docs/snapshots')

def save_snapshot(doc_id, name=""):
    """Save current document state"""
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    
    text = export_as_text(doc_id)
    if not text:
        print("Error: Could not export document")
        return False
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{doc_id}_{timestamp}.txt"
    if name:
        filename = f"{doc_id}_{name}_{timestamp}.txt"
    
    filepath = SNAPSHOT_DIR / filename
    filepath.write_text(text)
    print(f"Snapshot saved: {filepath}")
    return str(filepath)


def get_latest_snapshot(doc_id):
    """Get most recent snapshot for document"""
    snapshots = list(SNAPSHOT_DIR.glob(f"{doc_id}_*.txt"))
    if not snapshots:
        return None
    return max(snapshots, key=lambda p: p.stat().st_mtime)


def compare_to_snapshot(doc_id):
    """Compare current doc to last snapshot"""
    current = export_as_text(doc_id)
    if not current:
        print("Error: Could not export current document")
        return
    
    snapshot_file = get_latest_snapshot(doc_id)
    if not snapshot_file:
        print("No previous snapshot found. Creating one now...")
        save_snapshot(doc_id, "baseline")
        return
    
    previous = snapshot_file.read_text()
    
    if current == previous:
        print("✅ No changes detected since last snapshot")
        return
    
    print("📝 CHANGES DETECTED since last snapshot:\n")
    print(f"Previous: {snapshot_file.name}")
    print(f"Current:  {len(current)} chars")
    print(f"Previous: {len(previous)} chars")
    print(f"Diff:     {len(current) - len(previous):+d} chars\n")
    
    # Simple diff - show first difference
    lines_current = current.split('\n')
    lines_previous = previous.split('\n')
    
    print("--- Changed Lines ---")
    for i, (cur, prev) in enumerate(zip(lines_current, lines_previous)):
        if cur != prev:
            print(f"\nLine {i+1}:")
            print(f"  BEFORE: {prev[:100]}")
            print(f"  AFTER:  {cur[:100]}")
    
    # Save new snapshot
    print("\n💾 Saving new snapshot...")
    save_snapshot(doc_id)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Track document changes')
    parser.add_argument('action', choices=['save', 'compare', 'list'])
    parser.add_argument('--doc-id', required=True, help='Document ID')
    parser.add_argument('--name', help='Snapshot name')
    
    args = parser.parse_args()
    
    if args.action == 'save':
        save_snapshot(args.doc_id, args.name or "")
    elif args.action == 'compare':
        compare_to_snapshot(args.doc_id)
    elif args.action == 'list':
        snapshots = list(SNAPSHOT_DIR.glob(f"{args.doc_id}_*.txt"))
        print(f"\nSnapshots for {args.doc_id}:")
        for snap in sorted(snapshots):
            size = snap.stat().st_size
            mtime = datetime.fromtimestamp(snap.stat().st_mtime)
            print(f"  {snap.name} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})")


if __name__ == '__main__':
    main()
