#!/usr/bin/env python3
"""
Vitus - Lose It! Integration
Fetches and parses nutrition data from daily Lose It! emails via IMAP
Flock locking: prevents overlapping runs
"""

import imaplib
import email
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Optional, List

# Add workspace scripts for flock utilities
sys.path.insert(0, str(Path.home() / '.openclaw' / 'workspace' / 'scripts'))
from flock_utils import acquire_lock, LockHeldError

# Configuration
IMAP_SERVER = 'imap.gmail.com'
EMAIL_ACCOUNT = '[REDACTED]'
CREDENTIALS_FILE = Path.home() / '.openclaw' / 'credentials' / 'email-credentials.json'
DATA_DIR = Path.home() / '.openclaw' / 'workspace' / 'data' / 'nutrition'


class LoseItIntegration:
    def __init__(self):
        self.data_dir = DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.data_dir / 'loseit-cache.json'
        
    def get_credentials(self) -> Dict:
        """Get email credentials from stored config"""
        if CREDENTIALS_FILE.exists():
            with open(CREDENTIALS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def connect_imap(self) -> Optional[imaplib.IMAP4_SSL]:
        """Connect to Gmail IMAP"""
        creds = self.get_credentials()
        app_password = creds.get('app_password', '')
        
        if not app_password:
            print("No app password found in credentials")
            return None
        
        try:
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
            mail.login(EMAIL_ACCOUNT, app_password)
            return mail
        except Exception as e:
            print(f"IMAP connection failed: {e}")
            return None
    
    def fetch_loseit_emails(self, days_back: int = 2) -> List[Dict]:
        """Fetch Lose It! daily report emails from inbox"""
        mail = self.connect_imap()
        if not mail:
            return []
        
        emails = []
        try:
            mail.select('inbox')
            
            # Search for Lose It! emails from last N days
            since_date = (datetime.now() - timedelta(days=days_back)).strftime('%d-%b-%Y')
            search_criteria = f'(FROM "donotreply@loseit.com" SINCE "{since_date}")'
            
            _, message_ids = mail.search(None, search_criteria)
            
            for msg_id in message_ids[0].split():
                try:
                    _, msg_data = mail.fetch(msg_id, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    subject = msg['Subject']
                    date_str = msg['Date']
                    
                    # Extract HTML body
                    html_body = None
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == 'text/html':
                                html_body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                break
                    else:
                        html_body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                    
                    if html_body and ('Daily Report' in subject or 'Daily Summary' in subject):
                        emails.append({
                            'subject': subject,
                            'email_date': date_str,
                            'html': html_body
                        })
                        
                except Exception as e:
                    print(f"Error parsing email {msg_id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error fetching emails: {e}")
        finally:
            mail.logout()
        
        return emails
    
    def parse_nutrition_data(self, html_content: str, subject: str = None, email_date: str = None) -> Dict:
        """Parse Lose It! daily report HTML - text-based approach for reliability"""
        soup = BeautifulSoup(html_content, 'html.parser')
        text = soup.get_text()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        # Extract date from subject (e.g., "Lose It! Daily Summary for Wed, May 6th")
        report_date = datetime.now().strftime('%Y-%m-%d')
        
        # First try to get year from email date header
        email_year = None
        if email_date:
            try:
                # Parse email date like "Thu, 30 Apr 2026 15:10:55 +0000"
                email_dt = datetime.strptime(email_date[:16], '%a, %d %b %Y')
                email_year = email_dt.year
            except:
                pass
        
        if subject:
            # Try pattern with year first
            date_match = re.search(r'for \w+,? ([A-Za-z]+ \d{1,2})(?:st|nd|rd|th)?,? (\d{4})', subject)
            if date_match:
                try:
                    date_str = f"{date_match.group(1)} {date_match.group(2)}"
                    report_date = datetime.strptime(date_str, '%B %d %Y').strftime('%Y-%m-%d')
                except:
                    pass
            else:
                # Try pattern without year - use email year or current year
                date_match = re.search(r'for \w+,? ([A-Za-z]+ \d{1,2})(?:st|nd|rd|th)?', subject)
                if date_match:
                    try:
                        year = email_year if email_year else datetime.now().year
                        date_str = f"{date_match.group(1)} {year}"
                        # Try full month name first, then abbreviated
                        try:
                            report_date = datetime.strptime(date_str, '%B %d %Y').strftime('%Y-%m-%d')
                        except:
                            report_date = datetime.strptime(date_str, '%b %d %Y').strftime('%Y-%m-%d')
                    except:
                        pass
        
        data = {
            'date': report_date,
            'food_calories': None,
            'exercise_calories': None,
            'net_calories': None,
            'deficit': None,
            'weight': None,
            'meals': [],
            'macros': {
                'carbs': None,
                'fat': None,
                'protein': None
            }
        }
        
        # Parse by looking for patterns in consecutive lines
        for i, line in enumerate(lines):
            # Food calories
            if 'Food calories consumed' in line or line == 'Food calories consumed':
                if i + 1 < len(lines):
                    try:
                        val = lines[i + 1].replace(',', '').replace('cals', '').strip()
                        data['food_calories'] = int(val)
                    except:
                        pass
            
            # Exercise calories
            elif 'Exercise calories burned' in line or line == 'Exercise calories burned':
                if i + 1 < len(lines):
                    try:
                        val = lines[i + 1].replace(',', '').replace('cals', '').strip()
                        data['exercise_calories'] = int(val)
                    except:
                        pass
            
            # Net calories
            elif 'Net calories for the day' in line or line == 'Net calories for the day':
                if i + 1 < len(lines):
                    try:
                        val = lines[i + 1].replace(',', '').replace('cals', '').strip()
                        data['net_calories'] = int(val)
                    except:
                        pass
            
            # Daily calorie budget (to calculate deficit)
            elif 'Daily calorie budget' in line or line == 'Daily calorie budget':
                if i + 1 < len(lines):
                    try:
                        budget = int(lines[i + 1].replace(',', '').strip())
                        if data['net_calories']:
                            data['deficit'] = budget - data['net_calories']
                    except:
                        pass
            
            # Weight
            elif 'Weight' in line and i + 1 < len(lines):
                val = lines[i + 1].strip()
                if val and val != '-' and 'lbs' not in line:
                    try:
                        data['weight'] = float(val)
                    except:
                        pass
            
            # Macros - look for "Protein" followed by number with g
            elif line == 'Protein' or line == 'Protein(g)':
                if i + 1 < len(lines):
                    val = lines[i + 1].replace('g', '').replace(',', '').strip()
                    try:
                        data['macros']['protein'] = int(val)
                    except:
                        pass
            
            elif line == 'Carbohydrates':
                if i + 1 < len(lines):
                    val = lines[i + 1].replace('g', '').replace(',', '').strip()
                    try:
                        data['macros']['carbs'] = int(val)
                    except:
                        pass
            
            elif line == 'Fat':
                if i + 1 < len(lines):
                    val = lines[i + 1].replace('g', '').replace(',', '').strip()
                    try:
                        data['macros']['fat'] = int(val)
                    except:
                        pass
        
        # Parse meals
        current_meal = None
        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 3:
                first_cell = cells[0].get_text(strip=True)
                
                # Check if this is a meal header
                if first_cell in ['Breakfast', 'Lunch', 'Dinner', 'Snacks']:
                    try:
                        calories = int(cells[-1].get_text(strip=True).replace(',', ''))
                        current_meal = {
                            'name': first_cell,
                            'calories': calories,
                            'items': []
                        }
                        data['meals'].append(current_meal)
                    except:
                        pass
                elif current_meal and first_cell and not first_cell.startswith('Nutrient'):
                    # This is a food item
                    try:
                        calories = int(cells[-1].get_text(strip=True).replace(',', ''))
                        item = {
                            'name': first_cell,
                            'serving': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'calories': calories
                        }
                        current_meal['items'].append(item)
                    except:
                        pass
        
        return data
    
    def get_latest_nutrition(self) -> Optional[Dict]:
        """Get the most recent day's nutrition data"""
        # First check cache
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    cache_date = cache.get('date', '')
                    today = datetime.now().strftime('%Y-%m-%d')
                    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
                    
                    # Use cache if it's from today or yesterday
                    if cache_date in [today, yesterday]:
                        return cache
            except:
                pass
        
        # Fetch fresh data
        emails = self.fetch_loseit_emails(days_back=2)
        if not emails:
            return None
        
        # Parse the most recent email
        latest = emails[-1]  # Last one is most recent
        data = self.parse_nutrition_data(latest['html'], latest.get('subject'), latest.get('email_date'))
        
        # Save to cache
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        return data
    
    def get_yesterday_nutrition(self) -> Optional[Dict]:
        """Get yesterday's nutrition data for morning briefing"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Check if we have cached data for yesterday
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache = json.load(f)
                    if cache.get('date') == yesterday:
                        return cache
            except:
                pass
        
        # Fetch and find yesterday's data
        emails = self.fetch_loseit_emails(days_back=3)
        for email_data in emails:
            data = self.parse_nutrition_data(email_data['html'], email_data.get('subject'), email_data.get('email_date'))
            if data.get('date') == yesterday:
                return data
        
        return None
    
    def save_to_history(self, data: Dict):
        """Save nutrition data to historical record"""
        history_file = self.data_dir / 'nutrition-history.json'
        
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Add new entry or update existing
        existing = [h for h in history if h.get('date') == data.get('date')]
        if existing:
            existing[0].update(data)
        else:
            history.append(data)
        
        # Keep only last 90 days
        cutoff = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        history = [h for h in history if h.get('date', '') >= cutoff]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def analyze_trends(self) -> Dict:
        """Analyze nutrition trends over time"""
        history_file = self.data_dir / 'nutrition-history.json'
        
        if not history_file.exists():
            return {}
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except:
            return {}
        
        if len(history) < 3:
            return {'message': 'Not enough data for trend analysis'}
        
        # Calculate 7-day averages
        recent = history[-7:]
        avg_calories = sum(h.get('food_calories', 0) for h in recent if h.get('food_calories')) / len([h for h in recent if h.get('food_calories')])
        avg_protein = sum(h.get('macros', {}).get('protein', 0) for h in recent if h.get('macros', {}).get('protein')) / len([h for h in recent if h.get('macros', {}).get('protein')]) if any(h.get('macros', {}).get('protein') for h in recent) else 0
        
        return {
            '7_day_avg_calories': round(avg_calories, 0),
            '7_day_avg_protein': round(avg_protein, 0),
            'days_logged': len(history),
            'recent_entries': len(recent)
        }


def main():
    """CLI for testing Lose It! integration"""
    integration = LoseItIntegration()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == 'latest':
            data = integration.get_latest_nutrition()
            if data:
                print(json.dumps(data, indent=2))
            else:
                print("No nutrition data found")
        elif cmd == 'yesterday':
            data = integration.get_yesterday_nutrition()
            if data:
                print(json.dumps(data, indent=2))
            else:
                print("No yesterday's nutrition data found")
        elif cmd == 'trends':
            trends = integration.analyze_trends()
            print(json.dumps(trends, indent=2))
        elif cmd == 'fetch':
            emails = integration.fetch_loseit_emails()
            print(f"Found {len(emails)} Lose It! emails")
            for e in emails:
                print(f"  - {e['subject']}")
        else:
            print("Usage: python3 loseit_integration.py [latest|yesterday|trends|fetch]")
    else:
        # Default: get latest
        data = integration.get_latest_nutrition()
        if data:
            print(f"Latest nutrition data ({data.get('date')}):")
            print(f"  Calories: {data.get('food_calories', 'N/A')}")
            print(f"  Protein: {data.get('macros', {}).get('protein', 'N/A')}g")
            print(f"  Weight: {data.get('weight', 'N/A')} lbs")
        else:
            print("No nutrition data available")


if __name__ == '__main__':
    try:
        with acquire_lock("loseit-integration"):
            main()
    except LockHeldError:
        print("[loseit-integration] Lock held by another instance, skipping")
