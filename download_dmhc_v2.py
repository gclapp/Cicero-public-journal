#!/usr/bin/env python3
"""
Download DMHC financial statement PDFs for major health plans.
Uses ScraperAPI with ultra_premium for Akamai-protected sites.
Version 2: Better session handling
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlencode, urljoin
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

def get_scraperapi_url(target_url):
    """Build ScraperAPI URL with ultra_premium"""
    encoded_url = requests.utils.quote(target_url, safe='')
    return f"http://api.scraperapi.com?api_key={API_KEY}&url={encoded_url}&ultra_premium=true"

def fetch_via_scraperapi(target_url, method='GET', data=None):
    """Make request via ScraperAPI"""
    scraper_url = get_scraperapi_url(target_url)
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded' if data else None,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Origin': 'https://wpso.dmhc.ca.gov',
        'Referer': 'https://wpso.dmhc.ca.gov/fe/search/'
    }
    
    try:
        if method == 'POST' and data:
            response = requests.post(scraper_url, data=data, headers=headers, timeout=120)
        else:
            response = requests.get(scraper_url, headers=headers, timeout=120)
        
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error: {e}")
        return None

def extract_form_fields(html):
    """Extract all ASP.NET form fields"""
    fields = {}
    
    # ViewState
    match = re.search(r'id="__VIEWSTATE" value="([^"]*)"', html)
    fields['__VIEWSTATE'] = match.group(1) if match else ''
    
    # EventValidation
    match = re.search(r'id="__EVENTVALIDATION" value="([^"]*)"', html)
    fields['__EVENTVALIDATION'] = match.group(1) if match else ''
    
    # ViewStateGenerator
    match = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]*)"', html)
    fields['__VIEWSTATEGENERATOR'] = match.group(1) if match else 'C2EE9ABB'
    
    # EventTarget
    match = re.search(r'id="__EVENTTARGET" value="([^"]*)"', html)
    fields['__EVENTTARGET'] = match.group(1) if match else ''
    
    # EventArgument
    match = re.search(r'id="__EVENTARGUMENT" value="([^"]*)"', html)
    fields['__EVENTARGUMENT'] = match.group(1) if match else ''
    
    return fields

def search_documents(plan_id, statement_type):
    """Search for documents using the DMHC search form"""
    # Step 1: Get initial page
    print(f"    Fetching search page...")
    html = fetch_via_scraperapi(BASE_URL)
    if not html:
        return None
    
    # Step 2: Extract form fields
    form_fields = extract_form_fields(html)
    
    # Step 3: Build POST data for search
    post_data = {
        '__VIEWSTATE': form_fields['__VIEWSTATE'],
        '__VIEWSTATEGENERATOR': form_fields['__VIEWSTATEGENERATOR'],
        '__EVENTVALIDATION': form_fields['__EVENTVALIDATION'],
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$ctl00$MainContent$MainContent$ddlHPType': '0',
        'ctl00$ctl00$MainContent$MainContent$ddlHP': plan_id,
        'ctl00$ctl00$MainContent$MainContent$ddlStatementType': statement_type,
        'ctl00$ctl00$MainContent$MainContent$btnSearch': 'Search'
    }
    
    # Step 4: Submit search
    print(f"    Submitting search...")
    result_html = fetch_via_scraperapi(BASE_URL, method='POST', data=post_data)
    return result_html

def extract_results(html):
    """Extract document results from search results page"""
    results = []
    
    # Look for the results grid
    # Pattern for document rows
    doc_pattern = r'<tr[^>]*>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>(.*?)</td>.*?<td[^>]*>.*?href="(/fe/document/[^"]+\.pdf)".*?</tr>'
    
    matches = re.findall(doc_pattern, html, re.DOTALL | re.IGNORECASE)
    
    for match in matches:
        period_end = re.sub(r'<[^>]+>', '', match[0]).strip()
        received = re.sub(r'<[^>]+>', '', match[1]).strip()
        doc_type = re.sub(r'<[^>]+>', '', match[2]).strip()
        plan_name = re.sub(r'<[^>]+>', '', match[3]).strip()
        pdf_path = match[4]
        
        pdf_url = urljoin("https://wpso.dmhc.ca.gov", pdf_path)
        filename = pdf_path.split('/')[-1]
        
        results.append({
            'period_end': period_end,
            'received': received,
            'doc_type': doc_type,
            'plan_name': plan_name,
            'pdf_url': pdf_url,
            'filename': filename
        })
    
    return results

def download_pdf(pdf_url, output_path):
    """Download PDF via ScraperAPI"""
    scraper_url = get_scraperapi_url(pdf_url)
    
    try:
        response = requests.get(scraper_url, timeout=120, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        return os.path.getsize(output_path)
    except Exception as e:
        print(f"    Download error: {e}")
        return None

def main():
    print("=" * 70)
    print("DMHC Financial Statement PDF Downloader v2")
    print("=" * 70)
    
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    all_downloads = []
    download_count = 0
    
    for plan_name, plan_id in target_plans.items():
        print(f"\n{'='*70}")
        print(f"Health Plan: {plan_name}")
        print(f"{'='*70}")
        
        for stmt_code, stmt_name in statement_types.items():
            print(f"\n  Searching: {stmt_name}")
            
            # Search
            result_html = search_documents(plan_id, stmt_code)
            if not result_html:
                print(f"    ✗ Search failed")
                continue
            
            # Save debug HTML
            debug_file = f"/tmp/dmhc_{plan_id.replace(' ', '_')}_{stmt_code}.html"
            with open(debug_file, 'w') as f:
                f.write(result_html)
            
            # Extract results
            docs = extract_results(result_html)
            print(f"    Found {len(docs)} document(s)")
            
            if not docs:
                # Try alternative extraction
                pdf_links = re.findall(r'href="(/fe/document/[^"]+\.pdf)"', result_html)
                print(f"    Alternative search found {len(pdf_links)} PDF link(s)")
                for link in pdf_links[:5]:  # Limit to first 5
                    pdf_url = urljoin("https://wpso.dmhc.ca.gov", link)
                    filename = link.split('/')[-1]
                    docs.append({
                        'period_end': 'unknown',
                        'received': 'unknown',
                        'doc_type': stmt_name,
                        'plan_name': plan_name,
                        'pdf_url': pdf_url,
                        'filename': filename
                    })
            
            # Download PDFs
            for doc in docs[:3]:  # Limit to 3 most recent per type
                safe_plan = re.sub(r'[^\w\s-]', '', plan_name).strip().replace(' ', '_')
                safe_type = re.sub(r'[^\w\s-]', '', stmt_name).strip().replace(' ', '_')
                output_filename = f"{safe_plan}_{safe_type}_{doc['filename']}"
                output_path = os.path.join(DOWNLOAD_DIR, output_filename)
                
                # Skip if already exists
                if os.path.exists(output_path):
                    print(f"    ✓ Already exists: {output_filename}")
                    continue
                
                print(f"    Downloading: {doc['filename']}")
                size = download_pdf(doc['pdf_url'], output_path)
                
                if size:
                    print(f"      ✓ Saved ({size:,} bytes)")
                    all_downloads.append({
                        'plan': plan_name,
                        'type': stmt_name,
                        'filename': output_filename,
                        'url': doc['pdf_url'],
                        'size': size
                    })
                    download_count += 1
                    
                    if download_count % 5 == 0:
                        print(f"\n{'='*70}")
                        print(f"PROGRESS: {download_count} downloads completed")
                        print(f"{'='*70}")
                else:
                    print(f"      ✗ Failed")
                
                time.sleep(1)
        
        time.sleep(2)
    
    # Save manifest
    manifest = {
        'downloaded_at': datetime.now().isoformat(),
        'total': len(all_downloads),
        'files': all_downloads
    }
    
    manifest_path = os.path.join(DOWNLOAD_DIR, "manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {len(all_downloads)} PDFs downloaded")
    print(f"Manifest: {manifest_path}")
    print(f"{'='*70}")
    
    return all_downloads

if __name__ == "__main__":
    main()
