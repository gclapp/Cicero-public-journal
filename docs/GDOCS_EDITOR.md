# Google Docs Editor - Usage Guide

## Setup (One-time)
```bash
python3 scripts/gdocs_auth_setup.py
```

## Commands

### Create Document
```bash
python3 scripts/gdocs_editor.py create --title "My Document" --text "Initial content"
```

### Insert Text
```bash
# At end (default)
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "New content"

# At specific position
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "New content" --index 100

# After specific text
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "New content" --after "existing text"

# With formatting
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "Bold heading" --bold --heading HEADING_1
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "Italic note" --italic
python3 scripts/gdocs_editor.py insert --doc-id DOC_ID --text "Big text" --font-size 24
```

### Replace Text
```bash
python3 scripts/gdocs_editor.py replace --doc-id DOC_ID --old "old text" --new "new text"
```

### Delete Text
```bash
python3 scripts/gdocs_editor.py delete --doc-id DOC_ID --start 10 --end 50
```

### Export Document
```bash
python3 scripts/gdocs_editor.py export --doc-id DOC_ID
```

### View Document Structure
```bash
python3 scripts/gdocs_editor.py get --doc-id DOC_ID
```

## Features

| Feature | Status |
|---------|--------|
| Create documents | ✅ Working |
| Insert at end | ✅ Working |
| Insert at position | ✅ Working |
| Insert after text | ✅ Working |
| Bold formatting | ✅ Working |
| Italic formatting | ✅ Working |
| Headings (H1, H2, H3) | ✅ Working |
| Font size | ✅ Working |
| Replace text | ✅ Working |
| Delete range | ✅ Working |
| Export to text | ✅ Working |
| Suggestions mode | ⚠️ Requires more setup |

## Document ID

The Document ID is in the Google Docs URL:
```
https://docs.google.com/document/d/DOCUMENT_ID/edit
```

## Example Workflow

```bash
# Create blog post
doc_id=$(python3 scripts/gdocs_editor.py create --title "My Blog Post" --text "Draft content" | grep "Doc ID:" | cut -d' ' -f3)

# Add heading
python3 scripts/gdocs_editor.py insert --doc-id $doc_id --text "Introduction" --heading HEADING_1 --bold

# Add content
python3 scripts/gdocs_editor.py insert --doc-id $doc_id --text "This is my blog post content."

# Export for review
python3 scripts/gdocs_editor.py export --doc-id $doc_id
```
