#!/usr/bin/env python3
"""
Download DMHC financial statement PDFs for major health plans.
Uses ScraperAPI with ultra_premium for Akamai-protected sites.
"""

import os
import re
import json
import time
import subprocess
from datetime import datetime

# Configuration
API_KEY = "***"
BASE_URL = "https://wpso.dmhc.ca.gov/fe/search/"
DOWNLOAD_DIR = "data/raw/financial_statements"

# Target health plans with their IDs from the dropdown
target_plans = {
    "Blue Cross of California": "933 0303",
    "Blue Shield of California Promise Health Plan": "933 0326",
    "Kaiser Foundation Health Plan, Inc.": "933 0055",
    "Health Net of California, Inc.": "933 0300",
    "Aetna Health of California Inc.": "933 0176",
    "Blue Cross of California Partnership Plan, Inc.": "933 0415",
    "Health Net Community Solutions, Inc.": "933 0426",
    "Aetna Better Health of California Inc.": "933 0521",
}

# Statement types we want
statement_types = {
    "1": "Annual DMHC Financial Reporting Form",
    "6": "Annual Independent Auditor's Report"
}

def curl_request(target_url, output_file=None, method='GET', data=None):
    """Make request via ScraperAPI using curl"""
    if output_file:
        output_arg = f"-o {output_file}"
    else:
        output_arg = ""
    
    if method == 'POST' and data:
        # Build POST data string
        post_str = "&".join([f"{k}={v}" for k, v in data.items()])
        post_arg = f"-X POST -d '{post_str}'"
    else:
        post_arg = ""
    
    cmd = f'curl -sL "http://api.scraperapi.com?api_key=***&url={target_url}&ultra_premium=true" {post_arg} {output_arg}'
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"    Curl error: {result.stderr[:200]}")
            return None
        return result.stdout if not output_file else True
    except Exception as e:
        print(f"    Request error: {e}")
        return None

def extract_form_fields(html):
    """Extract ASP.NET form fields"""
    fields = {}
    
    patterns = {
        '__VIEWSTATE': r'id="__VIEWSTATE" value="([^"]*)"',
        '__EVENTVALIDATION': r'id="__EVENTVALIDATION" value="([^"]*)"',
        '__VIEWSTATEGENERATOR': r'id="__VIEWSTATEGENERATOR" value="([^"]*)"',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, html)
        fields[key] = match.group(1) if match else ''
    
    if not fields.get('__VIEWSTATEGENERATOR'):
        fields['__VIEWSTATEGENERATOR'] = 'C2EE9ABB'
    
    return fields

def search_documents(plan_id, statement_type):
    """Search for documents"""
    # Get initial page
    html = curl_request(BASE_URL)
    if not html:
        return None
    
    # Extract form fields
    fields = extract_form_fields(html)
    
    if not fields['__VIEWSTATE']:
        print("    ✗ Could not extract VIEWSTATE")
        return None
    
    # Build POST data - need to URL encode the values
    from urllib.parse import quote_plus
    post_data = {
        '__VIEWSTATE': quote_plus(fields['__VIEWSTATE']),
        '__VIEWSTATEGENERATOR': fields['__VIEWSTATEGENERATOR'],
        '__EVENTVALIDATION': quote_plus(fields['__EVENTVALIDATION']) if fields['__EVENTVALIDATION'] else '',
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$ctl00$MainContent$MainContent$ddlHPType': '0',
        'ctl00$ctl00$MainContent$MainContent$ddlHP': quote_plus(plan_id),
        'ctl00$ctl00$MainContent$MainContent$ddlStatementType': statement_type,
        'ctl00$ctl00$MainContent$MainContent$btnSearch': 'Search'
    }
    
    # Submit search
    return curl_request(BASE_URL, method='POST', data=post_data)

def extract_pdf_links(html):
    """Extract PDF links from search results"""
    links = []
    
    # Find all PDF links
    pattern = r'href="(/fe/document/[^"]+\.pdf)"[^>]*>([^<]*)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    for path, text in matches:
        pdf_url = f"https://wpso.dmhc.ca.gov{path}"
        filename = path.split('/')[-1]
        links.append({
            'url': pdf_url,
            'filename': filename,
            'text': text.strip()
        })
    
    return links

def download_pdf(pdf_url, output_path):
    """Download PDF via ScraperAPI using curl"""
    result = curl_request(pdf_url, output_file=output_path)
    if result and os.path.exists(output_path):
        size = os.path.getsize(output_path)
        # Check if it's actually a PDF
        with open(output_path, 'rb') as f:
            header = f.read(10)
            if header.startswith(b'%PDF'):
                return size
            elif b'<html' in header.lower():
                # It's HTML, not a PDF
                os.remove(output_path)
                return None
            else:
                return size
    return None

def main():
    print("=" * 70)
    print("DMHC Financial Statement PDF Downloader")
    print("=" * 70)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    all_downloads = []
    download_count = 0
    
    for plan_name, plan_id in target_plans.items():
        print(f"\n{'='*70}")
        print(f"Health Plan: {plan_name}")
        print(f"{'='*70}")
        
        for stmt_code, stmt_name in statement_types.items():
            print(f"\n  Document Type: {stmt_name}")
            print(f"  Searching...")
            
            result_html = search_documents(plan_id, stmt_code)
            if not result_html:
                print(f"    ✗ Search failed")
                continue
            
            # Save debug HTML
            debug_path = f"/tmp/dmhc_debug_{plan_id.replace(' ', '_')}_{stmt_code}.html"
            with open(debug_path, 'w') as f:
                f.write(result_html[:100000])
            
            # Extract PDF links
            pdf_links = extract_pdf_links(result_html)
            print(f"    Found {len(pdf_links)} PDF(s)")
            
            if not pdf_links:
                # Try alternative extraction
                alt_links = re.findall(r'href="(/fe/document/[^"]+\.pdf)"', result_html, re.IGNORECASE)
                print(f"    Alternative: {len(alt_links)} link(s)")
                for link in alt_links[:5]:
                    pdf_url = f"https://wpso.dmhc.ca.gov{link}"
                    pdf_links.append({
                        'url': pdf_url,
                        'filename': link.split('/')[-1],
                        'text': 'Unknown'
                    })
            
            # Download PDFs (limit to 3 per search)
            for pdf in pdf_links[:3]:
                safe_plan = re.sub(r'[^\w\s-]', '', plan_name).strip().replace(' ', '_')[:30]
                safe_type = re.sub(r'[^\w\s-]', '', stmt_name).strip().replace(' ', '_')[:30]
                output_name = f"{safe_plan}_{safe_type}_{pdf['filename']}"
                output_path = os.path.join(DOWNLOAD_DIR, output_name)
                
                if os.path.exists(output_path):
                    print(f"    ✓ Exists: {output_name}")
                    continue
                
                print(f"    Downloading: {pdf['filename']}")
                size = download_pdf(pdf['url'], output_path)
                
                if size:
                    print(f"      ✓ Saved ({size:,} bytes)")
                    all_downloads.append({
                        'plan': plan_name,
                        'type': stmt_name,
                        'filename': output_name,
                        'url': pdf['url'],
                        'size': size,
                        'downloaded_at': datetime.now().isoformat()
                    })
                    download_count += 1
                    
                    if download_count % 5 == 0:
                        print(f"\n{'='*70}")
                        print(f"PROGRESS REPORT: {download_count} downloads completed")
                        print(f"{'='*70}")
                else:
                    print(f"      ✗ Failed")
                
                time.sleep(1)
        
        time.sleep(2)
    
    # Save manifest
    manifest = {
        'downloaded_at': datetime.now().isoformat(),
        'total_downloads': len(all_downloads),
        'files': all_downloads
    }
    
    manifest_path = os.path.join(DOWNLOAD_DIR, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"DOWNLOAD COMPLETE")
    print(f"Total PDFs: {len(all_downloads)}")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*70}")
    
    return all_downloads

if __name__ == "__main__":
    main()
