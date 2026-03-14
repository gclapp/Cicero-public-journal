"""
Celery Tasks for Background Jobs
"""

from celery import Celery
from flask import current_app
from models import db, WatchSearch, Watch, SearchSource, SearchLog
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re

# Initialize Celery
celery = Celery('tasks')
celery.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Import scrapers
import sys
sys.path.insert(0, '/var/www/cicero/scripts')

@celery.task
def run_watch_search(search_id):
    """Run a watch search across all configured sources"""
    from app import app
    
    with app.app_context():
        search = WatchSearch.query.get(search_id)
        if not search:
            return {'error': 'Search not found'}
        
        results = {
            'search_id': search_id,
            'sources_checked': [],
            'watches_found': 0
        }
        
        for source_name in search.sources:
            log = SearchLog(
                search_id=search_id,
                source=source_name,
                status='running',
                started_at=datetime.utcnow()
            )
            db.session.add(log)
            db.session.commit()
            
            try:
                watches = scrape_source(source_name, search)
                
                for watch_data in watches:
                    # Check if watch already exists
                    existing = Watch.query.filter_by(
                        source=watch_data['source'],
                        source_url=watch_data['source_url']
                    ).first()
                    
                    if not existing:
                        watch = Watch(
                            search_id=search_id,
                            **watch_data
                        )
                        db.session.add(watch)
                        results['watches_found'] += 1
                
                log.status = 'success'
                log.watches_found = len(watches)
                
                # Update source last search time
                source = SearchSource.query.filter_by(name=source_name).first()
                if source:
                    source.last_search = datetime.utcnow()
                    source.watches_found += len(watches)
                
            except Exception as e:
                log.status = 'error'
                log.error_message = str(e)
            
            log.completed_at = datetime.utcnow()
            db.session.commit()
            
            results['sources_checked'].append({
                'source': source_name,
                'status': log.status,
                'watches_found': log.watches_found
            })
        
        # Update search last run time
        search.last_run = datetime.utcnow()
        db.session.commit()
        
        return results

def scrape_source(source_name, search):
    """Scrape a specific source for watches"""
    watches = []
    
    if source_name == 'chrono24':
        watches = scrape_chrono24(search)
    elif source_name == 'ebay':
        watches = scrape_ebay(search)
    elif source_name == 'bobs_watches':
        watches = scrape_bobs_watches(search)
    elif source_name == 'bulang_sons':
        watches = scrape_bulang_sons(search)
    elif source_name == 'bezel':
        watches = scrape_bezel(search)
    elif source_name == 'crown_and_caliber':
        watches = scrape_crown_and_caliber(search)
    
    return watches

def scrape_chrono24(search):
    """Scrape Chrono24 for watches"""
    watches = []
    
    for model in search.model_numbers:
        url = f"https://www.chrono24.com/{search.brand.lower()}/ref-{model}.htm"
        
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                listings = soup.select('.article-item-container')
                
                for listing in listings[:20]:  # Limit to 20 per model
                    try:
                        # Extract data from listing
                        title_elem = listing.select_one('img')
                        title = title_elem['alt'] if title_elem else ''
                        
                        link_elem = listing.select_one('a[href]')
                        link = link_elem['href'] if link_elem else ''
                        if link and not link.startswith('http'):
                            link = f"https://www.chrono24.com{link}"
                        
                        # Extract year
                        year_match = re.search(r'(19[7-9]\d|20[0-2]\d)', title)
                        year = int(year_match.group(1)) if year_match else None
                        
                        if year and search.year_min <= year <= search.year_max:
                            watch = {
                                'reference': model,
                                'year': year,
                                'dial_color': extract_dial_color(title),
                                'dial_type': title[:100],
                                'case_type': extract_case_type(title),
                                'size': '36mm',
                                'bracelet': 'Unknown',
                                'price': extract_price(listing),
                                'source': 'Chrono24',
                                'source_url': link,
                                'image_url': extract_image_url(listing),
                            }
                            watches.append(watch)
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error scraping Chrono24: {e}")
    
    return watches

def scrape_ebay(search):
    """Scrape eBay for watches"""
    watches = []
    # Implementation similar to existing script
    return watches

def scrape_bobs_watches(search):
    """Scrape Bob's Watches"""
    watches = []
    # Implementation
    return watches

def scrape_bulang_sons(search):
    """Scrape Bulang & Sons"""
    watches = []
    # Implementation
    return watches

def scrape_bezel(search):
    """Scrape Bezel"""
    watches = []
    # Implementation
    return watches

def scrape_crown_and_caliber(search):
    """Scrape Crown & Caliber"""
    watches = []
    # Implementation
    return watches

# Helper functions
def extract_dial_color(text):
    """Extract dial color from text"""
    text_lower = text.lower()
    colors = {
        'blue': 'blue',
        'black': 'black',
        'champagne': 'champagne',
        'silver': 'silver',
        'white': 'white',
        'linen': 'linen'
    }
    for color, value in colors.items():
        if color in text_lower:
            return value
    return 'unknown'

def extract_case_type(text):
    """Extract case type from text"""
    text_lower = text.lower()
    if 'two-tone' in text_lower or 'two tone' in text_lower:
        return 'Two-tone'
    elif 'gold' in text_lower and 'steel' not in text_lower:
        return 'Gold'
    elif 'steel' in text_lower or 'stainless' in text_lower:
        return 'Steel'
    return 'Unknown'

def extract_price(listing):
    """Extract price from listing"""
    try:
        price_elem = listing.select_one('[class*="price"], .amount')
        if price_elem:
            price_text = price_elem.text
            match = re.search(r'[\$€£]?([\d,]+(?:\.\d{2})?)', price_text)
            if match:
                return float(match.group(1).replace(',', ''))
    except:
        pass
    return None

def extract_image_url(listing):
    """Extract image URL from listing"""
    try:
        img = listing.select_one('img')
        if img:
            return img.get('src') or img.get('data-src')
    except:
        pass
    return None

# Scheduled tasks
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Run all active searches daily at 2 AM and 5 PM UTC
    sender.add_periodic_task(
        crontab(hour='2,17', minute='0'),
        run_all_searches.s(),
        name='run-all-searches-twice-daily'
    )

@celery.task
def run_all_searches():
    """Run all active searches"""
    from app import app
    
    with app.app_context():
        active_searches = WatchSearch.query.filter_by(status='active').all()
        
        for search in active_searches:
            run_watch_search.delay(search.id)
        
        return {
            'searches_triggered': len(active_searches),
            'timestamp': datetime.utcnow().isoformat()
        }
