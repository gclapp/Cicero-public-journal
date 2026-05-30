#!/usr/bin/env python3
"""
Download DMHC financial statement PDFs for major health plans.
Uses ScraperAPI with ultra_premium for Akamai-protected sites.
"""

import os
import re
import json
import time
import requests
from urllib.parse import urlencode, quote
from datetime import datetime

# Configuration
API_KEY = "[REDACTED_SCRAPER_API_KEY]"
BASE_URL = "https://wpso.dmhc.ca.gov/fe/search/"
DOWNLOAD_DIR = "data/raw/financial_statements"
SCRAPE_BASE = "http://api.scraperapi.com"

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
    params = {
        'api_key': API_KEY,
        'url': target_url,
        'ultra_premium': 'true'
    }
    return f"{SCRAPE_BASE}?{urlencode(params)}"

def download_page(url):
    """Download a page via ScraperAPI"""
    scraper_url = get_scraperapi_url(url)
    try:
        response = requests.get(scraper_url, timeout=120)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return None

def extract_viewstate(html):
    """Extract ASP.NET viewstate and eventvalidation from page"""
    viewstate = re.search(r'id="__VIEWSTATE" value="([^"]+)"', html)
    eventval = re.search(r'id="__EVENTVALIDATION" value="([^"]+)"', html)
    viewgen = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]+)"', html)
    
    return {
        '__VIEWSTATE': viewstate.group(1) if viewstate else '',
        '__EVENTVALIDATION': eventval.group(1) if eventval else '',
        '__VIEWSTATEGENERATOR': viewgen.group(1) if viewgen else 'C2EE9ABB'
    }

def search_health_plan(plan_name, plan_id, statement_type):
    """Search for financial statements for a specific health plan"""
    # First get the search page to capture viewstate
    html = download_page(BASE_URL)
    if not html:
        return []
    
    viewstate_data = extract_viewstate(html)
    
    # Build search POST data
    post_data = {
        '__VIEWSTATE': viewstate_data['__VIEWSTATE'],
        '__EVENTVALIDATION': viewstate_data['__EVENTVALIDATION'],
        '__VIEWSTATEGENERATOR': viewstate_data['__VIEWSTATEGENERATOR'],
        '__EVENTTARGET': '',
        '__EVENTARGUMENT': '',
        'ctl00$ctl00$MainContent$MainContent$ddlHPType': '0',  # Any type
        'ctl00$ctl00$MainContent$MainContent$ddlHP': plan_id,
        'ctl00$ctl00$MainContent$MainContent$ddlStatementType': statement_type,
        'ctl00$ctl00$MainContent$MainContent$btnSearch': 'Search'
    }
    
    # Submit search via ScraperAPI (POST)
    scraper_url = get_scraperapi_url(BASE_URL)
    try:
        response = requests.post(scraper_url, data=post_data, timeout=120)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error searching for {plan_name}: {e}")
        return None

def extract_pdf_links(html):
    """Extract PDF download links from search results"""
    links = []
    # Pattern for PDF links
    pattern = r'href="(/fe/document/[^"]+\.pdf)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, html, re.IGNORECASE)
    
    for link, text in matches:
        full_url = f"https://wpso.dmhc.ca.gov{link}"
        links.append({
            'url': full_url,
            'text': text.strip(),
            'filename': link.split('/')[-1]
        })
    
    return links

def download_pdf(pdf_url, filename, plan_name, doc_type):
    """Download a PDF file"""
    # Create safe filename
    safe_plan = re.sub(r'[^\w\s-]', '', plan_name).strip().replace(' ', '_')
    safe_type = re.sub(r'[^\w\s-]', '', doc_type).strip().replace(' ', '_')
    
    # Add timestamp to filename to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d")
    output_filename = f"{safe_plan}_{safe_type}_{timestamp}_{filename}"
    output_path = os.path.join(DOWNLOAD_DIR, output_filename)
    
    # Download via ScraperAPI
    scraper_url = get_scraperapi_url(pdf_url)
    try:
        response = requests.get(scraper_url, timeout=120, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        print(f"  ✓ Downloaded: {output_filename} ({file_size:,} bytes)")
        return {
            'filename': output_filename,
            'path': output_path,
            'url': pdf_url,
            'size': file_size,
            'plan': plan_name,
            'type': doc_type
        }
    except Exception as e:
        print(f"  ✗ Error downloading {filename}: {e}")
        return None

def main():
    """Main execution"""
    print("=" * 70)
    print("DMHC Financial Statement PDF Downloader")
    print("Using ScraperAPI with ultra_premium")
    print("=" * 70)
    
    # Ensure download directory exists
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Track downloads
    all_downloads = []
    download_count = 0
    
    # Process each health plan
    for plan_name, plan_id in target_plans.items():
        print(f"\n{'='*70}")
        print(f"Searching: {plan_name}")
        print(f"{'='*70}")
        
        for stmt_code, stmt_name in statement_types.items():
            print(f"\n  Document Type: {stmt_name}")
            
            # Search for documents
            search_html = search_health_plan(plan_name, plan_id, stmt_code)
            if not search_html:
                print(f"    ✗ Search failed")
                continue
            
            # Extract PDF links
            pdf_links = extract_pdf_links(search_html)
            if not pdf_links:
                print(f"    No PDFs found")
                continue
            
            print(f"    Found {len(pdf_links)} PDF(s)")
            
            # Download each PDF
            for pdf_info in pdf_links:
                result = download_pdf(
                    pdf_info['url'], 
                    pdf_info['filename'],
                    plan_name,
                    stmt_name
                )
                if result:
                    all_downloads.append(result)
                    download_count += 1
                    
                    # Report progress every 5 downloads
                    if download_count % 5 == 0:
                        print(f"\n{'='*70}")
                        print(f"PROGRESS REPORT: {download_count} downloads completed")
                        print(f"{'='*70}")
                
                # Be nice to the API
                time.sleep(1)
        
        # Pause between plans
        time.sleep(2)
    
    # Save download manifest
    manifest_path = os.path.join(DOWNLOAD_DIR, "download_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump({
            'downloaded_at': datetime.now().isoformat(),
            'total_downloads': len(all_downloads),
            'downloads': all_downloads
        }, f, indent=2)
    
    print(f"\n{'='*70}")
    print(f"DOWNLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"Total PDFs downloaded: {len(all_downloads)}")
    print(f"Manifest saved to: {manifest_path}")
    print(f"Files saved to: {DOWNLOAD_DIR}")
    
    return all_downloads

if __name__ == "__main__":
    downloads = main()
