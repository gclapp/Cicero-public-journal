#!/usr/bin/env python3
"""
DMHC Delegation Search - Status Checker
Reports current project status without requiring Telegram bot token
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_DIR = Path("/home/ubuntu/.openclaw/workspace/projects/dmhc-delegation-search")
DB_PATH = PROJECT_DIR / "data/processed/dmhc_search.db"
STATE_FILE = Path("/home/ubuntu/.openclaw/workspace/.dmhc_monitor_state.json")

def check_database():
    """Check database statistics."""
    if not DB_PATH.exists():
        return {"error": "Database not found"}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        stats = {}
        
        # Documents
        cursor = conn.execute("SELECT COUNT(*) FROM source_documents")
        stats['documents'] = cursor.fetchone()[0]
        
        # Chunks
        cursor = conn.execute("SELECT COUNT(*) FROM text_chunks")
        stats['chunks'] = cursor.fetchone()[0]
        
        # Candidates by status
        cursor = conn.execute("SELECT status, COUNT(*) FROM candidate_chunks GROUP BY status")
        stats['candidates'] = dict(cursor.fetchall())
        
        # Leads
        cursor = conn.execute("SELECT COUNT(*) FROM delegation_leads")
        stats['total_leads'] = cursor.fetchone()[0]
        
        # Leads by confidence
        cursor = conn.execute(
            "SELECT confidence_score, COUNT(*) FROM delegation_leads GROUP BY confidence_score"
        )
        stats['leads_by_confidence'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
    except Exception as e:
        return {"error": str(e)}

def check_source_connectors():
    """Check if source connector files exist."""
    sources_dir = PROJECT_DIR / "app/sources"
    connectors = {
        "medical_surveys": (sources_dir / "medical_surveys.py").exists(),
        "enforcement_actions": (sources_dir / "enforcement_actions.py").exists(),
        "financial_exams": (sources_dir / "financial_exams.py").exists()
    }
    return connectors

def check_llm_config():
    """Check if LLM is configured for real extraction."""
    llm_file = PROJECT_DIR / "app/extraction/llm_extract.py"
    if not llm_file.exists():
        return {"configured": False, "error": "LLM extractor not found"}
    
    try:
        content = llm_file.read_text()
        # Check if it uses real LLM vs mock
        uses_real = "gpt-4o-mini" in content or "GPT-4o-mini" in content
        uses_mock = "mock" in content.lower() and "def extract" in content
        
        return {
            "configured": uses_real,
            "uses_real_model": uses_real,
            "has_mock_fallback": uses_mock
        }
    except Exception as e:
        return {"configured": False, "error": str(e)}

def format_status_report():
    """Format a comprehensive status report."""
    now = datetime.now(timezone.utc)
    pt_time = now - timedelta(hours=8)
    
    db_stats = check_database()
    connectors = check_source_connectors()
    llm_config = check_llm_config()
    
    report = f"""📊 *DMHC Delegation Search - Status Report*

⏰ {pt_time.strftime('%I:%M %p PT')} | {now.strftime('%H:%M UTC')}

*Source Connectors:*
"""
    
    for name, exists in connectors.items():
        emoji = "✅" if exists else "❌"
        report += f"{emoji} {name.replace('_', ' ').title()}\n"
    
    report += f"""
*Database Statistics:*
"""
    
    if "error" in db_stats:
        report += f"❌ Error: {db_stats['error']}\n"
    else:
        report += f"📄 Documents: {db_stats.get('documents', 0)}\n"
        report += f"📝 Text chunks: {db_stats.get('chunks', 0)}\n"
        report += f"🎯 Total leads: {db_stats.get('total_leads', 0)}\n"
        
        candidates = db_stats.get('candidates', {})
        if candidates:
            report += f"\n*Candidates:*\n"
            for status, count in candidates.items():
                report += f"  • {status}: {count}\n"
        
        leads_by_conf = db_stats.get('leads_by_confidence', {})
        if leads_by_conf:
            report += f"\n*Leads by confidence:*\n"
            for conf, count in leads_by_conf.items():
                report += f"  • {conf}: {count}\n"
    
    report += f"""
*LLM Configuration:*
"""
    if llm_config.get("configured"):
        report += "✅ Using real GPT-4o-mini model\n"
    else:
        report += "⚠️ Mock mode or not configured\n"
    
    if llm_config.get("has_mock_fallback"):
        report += "ℹ️ Mock fallback available\n"
    
    # Determine overall progress
    steps_complete = sum(1 for v in connectors.values() if v)
    has_leads = db_stats.get('total_leads', 0) > 0 if 'total_leads' in db_stats else False
    llm_ready = llm_config.get("configured", False)
    
    report += f"""
*Overall Progress:*
"""
    if steps_complete >= 2:
        report += "✅ Step 1/4: Source connectors created\n"
    else:
        report += "🟡 Step 1/4: Source connectors (partial)\n"
    
    if has_leads:
        report += "✅ Step 2/4: Extraction run (has leads)\n"
    else:
        report += "⏳ Step 2/4: Extraction run (pending)\n"
    
    if llm_ready:
        report += "✅ Step 3/4: LLM configured for real mode\n"
    else:
        report += "⏳ Step 3/4: LLM configuration (pending)\n"
    
    report += "⏳ Step 4/4: Final validation (pending)\n"
    
    return report

def main():
    """Main entry point."""
    report = format_status_report()
    print(report)
    
    # Also save to state file for monitor to pick up
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            state['last_check'] = datetime.now(timezone.utc).isoformat()
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"\n[Warning] Could not update state file: {e}")

if __name__ == "__main__":
    main()
