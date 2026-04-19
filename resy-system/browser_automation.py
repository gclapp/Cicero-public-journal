#!/usr/bin/env python3
"""
Browser Automation Fallback for Resy Booking

When the API returns 500 errors, this module uses browser automation
to check availability and make reservations through the Resy website.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

# Browser automation
from playwright.sync_api import sync_playwright, Page, Browser, expect

# Resy credentials
RESY_CREDENTIALS = Path.home() / ".openclaw" / "config" / "resy-credentials.json"

def load_resy_credentials():
    """Load Resy credentials"""
    with open(RESY_CREDENTIALS) as f:
        return json.load(f)

class ResyBrowserAutomation:
    """Browser automation for Resy when API fails"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False
    
    def start(self):
        """Start browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page(viewport={'width': 1280, 'height': 800})
        
    def stop(self):
        """Stop browser"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
            
    def login(self) -> bool:
        """Login to Resy"""
        creds = load_resy_credentials()
        
        print("Logging into Resy...")
        self.page.goto("https://resy.com")
        
        # Wait for page to load
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        # Click login button
        try:
            login_btn = self.page.locator('button:has-text("Log in")').first
            if login_btn.is_visible():
                login_btn.click()
                time.sleep(1)
        except:
            pass
        
        # Check if already logged in
        try:
            profile_btn = self.page.locator('[data-testid="profile-button"]').first
            if profile_btn.is_visible():
                print("Already logged in!")
                return True
        except:
            pass
        
        # Enter credentials
        try:
            # Use the auth token approach instead of password
            # Set the auth token in localStorage
            self.page.evaluate(f"""
                localStorage.setItem('resy_auth_token', '{creds['auth_token']}');
                localStorage.setItem('resy_api_key', '{creds['api_key']}');
            """)
            
            # Refresh to apply token
            self.page.goto("https://resy.com")
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
            
            # Check if logged in now
            try:
                profile_btn = self.page.locator('[data-testid="profile-button"]').first
                if profile_btn.is_visible():
                    print("Logged in via token!")
                    return True
            except:
                pass
                
        except Exception as e:
            print(f"Login error: {e}")
            
        print("⚠️  Could not confirm login status")
        return False
    
    def check_availability(
        self, 
        venue_slug: str, 
        date: str, 
        party_size: int
    ) -> List[Dict[str, Any]]:
        """
        Check availability for a restaurant
        
        Args:
            venue_slug: Restaurant URL slug (e.g., "the-naked-pig")
            date: Date in YYYY-MM-DD format
            party_size: Number of guests
            
        Returns:
            List of available time slots
        """
        url = f"https://resy.com/cities/new-york-ny/venues/{venue_slug}"
        
        print(f"Checking {venue_slug} for {date}...")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        slots = []
        
        try:
            # Set party size
            party_dropdown = self.page.locator('select[name="party_size"]').first
            if party_dropdown.is_visible():
                party_dropdown.select_option(str(party_size))
                time.sleep(1)
            
            # Click date picker
            date_input = self.page.locator('input[placeholder*="Date"], button:has-text("Date")').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(1)
                
                # Select date
                date_btn = self.page.locator(f'text={date}').first
                if date_btn.is_visible():
                    date_btn.click()
                    time.sleep(2)
            
            # Look for time slots
            time_buttons = self.page.locator('button:has-text(":")').all()
            
            for btn in time_buttons:
                text = btn.inner_text()
                if any(x in text for x in [":00", ":30"]):
                    slots.append({
                        'time': text.strip(),
                        'available': True
                    })
                    
        except Exception as e:
            print(f"Error checking availability: {e}")
            
        print(f"Found {len(slots)} time slots")
        return slots
    
    def book_reservation(
        self, 
        venue_slug: str, 
        date: str, 
        time_slot: str, 
        party_size: int
    ) -> bool:
        """
        Book a reservation through the browser
        
        Args:
            venue_slug: Restaurant URL slug
            date: Date in YYYY-MM-DD format  
            time_slot: Time to book (e.g., "7:00 PM")
            party_size: Number of guests
            
        Returns:
            True if booking successful
        """
        url = f"https://resy.com/cities/new-york-ny/venues/{venue_slug}"
        
        print(f"Booking {venue_slug} for {date} at {time_slot}...")
        self.page.goto(url)
        self.page.wait_for_load_state("networkidle")
        time.sleep(2)
        
        try:
            # Set party size
            party_dropdown = self.page.locator('select[name="party_size"]').first
            if party_dropdown.is_visible():
                party_dropdown.select_option(str(party_size))
                time.sleep(1)
            
            # Click date picker and select date
            date_input = self.page.locator('input[placeholder*="Date"]').first
            if date_input.is_visible():
                date_input.click()
                time.sleep(1)
                
                # Try to find and click the date
                date_cell = self.page.locator(f'text="{date}"').first
                if date_cell.is_visible():
                    date_cell.click()
                    time.sleep(2)
            
            # Click the time slot
            time_btn = self.page.locator(f'button:has-text("{time_slot}")').first
            if time_btn.is_visible():
                time_btn.click()
                time.sleep(2)
                
                # Confirm booking
                confirm_btn = self.page.locator('button:has-text("Confirm"), button:has-text("Book")').first
                if confirm_btn.is_visible():
                    confirm_btn.click()
                    time.sleep(3)
                    
                    # Check for success
                    success = self.page.locator('text="Reservation Confirmed"').first
                    if success.is_visible():
                        print("✅ Booking confirmed!")
                        return True
                        
        except Exception as e:
            print(f"Booking error: {e}")
            
        print("❌ Booking failed")
        return False


def check_availability_with_fallback(
    venue_id: int,
    venue_slug: str, 
    date: str, 
    party_size: int
) -> List[Dict[str, Any]]:
    """
    Check availability using API first, fallback to browser if API fails
    
    Args:
        venue_id: Resy venue ID
        venue_slug: Restaurant URL slug
        date: Date in YYYY-MM-DD format
        party_size: Number of guests
        
    Returns:
        List of available slots
    """
    # Try API first
    from calendar_scanner import find_resy_reservations
    
    result, status = find_resy_reservations(venue_id, date, party_size)
    
    if status == 'success' and result:
        # Parse API response
        slots = []
        venues = result.get('results', {}).get('venues', [])
        for venue in venues:
            for slot in venue.get('slots', []):
                slots.append({
                    'time': slot.get('date', {}).get('start', ''),
                    'type': slot.get('config', {}).get('type', 'Standard'),
                    'source': 'api'
                })
        if slots:
            return slots
    
    # API failed or returned no results, try browser
    print(f"API failed ({status}), trying browser automation...")
    
    with ResyBrowserAutomation(headless=True) as browser:
        browser.login()
        return browser.check_availability(venue_slug, date, party_size)


if __name__ == "__main__":
    # Test the browser automation
    print("Testing Resy Browser Automation")
    print("=" * 70)
    
    with ResyBrowserAutomation(headless=False) as browser:
        browser.login()
        
        # Check The Naked Pig
        slots = browser.check_availability("the-naked-pig", "2026-05-17", 2)
        
        print(f"\nAvailable slots:")
        for slot in slots:
            print(f"  - {slot['time']}")
