#!/usr/bin/env python3
"""
Export Google Doc to Substack-ready Markdown
"""

import sys
import re
sys.path.insert(0, '/home/ubuntu/.openclaw/workspace/scripts')
from gdocs_editor import export_as_text

def convert_to_substack_markdown(doc_id, title, subtitle=""):
    """Convert Google Doc content to Substack Markdown"""
    
    text = export_as_text(doc_id)
    if not text:
        print("Error: Could not export document")
        return None
    
    # Substack uses simple formatting
    # We'll convert our content to Substack-friendly Markdown
    
    output = []
    
    # Title
    output.append(f"# {title}")
    output.append("")
    
    if subtitle:
        output.append(f"*{subtitle}*")
        output.append("")
    
    # Process content
    lines = text.split('\n')
    in_code_block = False
    
    for line in lines:
        # Skip the title line (already added)
        if line.strip() == title:
            continue
        if line.strip() == subtitle:
            continue
            
        # Handle code blocks
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            output.append(line)
            continue
        
        if in_code_block:
            output.append(line)
            continue
        
        # Handle headings
        if line.strip().startswith('# '):
            # H1 -> H2 (since title is H1)
            output.append(f"## {line.strip()[2:]}")
        elif line.strip().startswith('## '):
            # H2 -> H3
            output.append(f"### {line.strip()[3:]}")
        elif line.strip().startswith('### '):
            # H3 -> H4
            output.append(f"#### {line.strip()[4:]}")
        # Handle bold/italic
        elif line.strip().startswith('**') and line.strip().endswith('**'):
            # Bold heading style
            output.append(f"**{line.strip()[2:-2]}**")
        # Handle tables (convert to simple list)
        elif '|' in line and '---' not in line:
            cells = [c.strip() for c in line.split('|') if c.strip()]
            if len(cells) >= 2:
                output.append(f"- **{cells[0]}**: {cells[1]}")
        else:
            output.append(line)
    
    return '\n'.join(output)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--doc-id', required=True)
    parser.add_argument('--title', required=True)
    parser.add_argument('--subtitle', default="")
    parser.add_argument('--output', '-o', help='Output file')
    
    args = parser.parse_args()
    
    markdown = convert_to_substack_markdown(args.doc_id, args.title, args.subtitle)
    
    if markdown:
        if args.output:
            with open(args.output, 'w') as f:
                f.write(markdown)
            print(f"Saved to: {args.output}")
        else:
            print(markdown)
    else:
        print("Error converting document")
