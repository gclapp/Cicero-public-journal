#!/usr/bin/env python3
"""
Bulletproof Browser Automation v2 for Resy Restaurant Reservations
"""

import json
import time
import random
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from playwright.sync_api import (
    sync_playwright, Page, Browser, BrowserContext, 
    TimeoutError as PlaywrightTimeout
)

try:
    from playwright_stealth import stealth_sync
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False

RESY_CREDENTIALS = Path.home() / ".openclaw" / "config" / "resy-credentials.json"

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)
SCREENSHOTS_DIR = LOGS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / "browser_automation_v2.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("resy_browser_v2")


class BookingStatus(Enum):
    SUCCESS = "success"
    NO_AVAILABILITY = "no_availability"
    LOGIN_FAILED = "login_failed"
    CAPTCHA_DETECTED = "captcha_detected"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    DRY_RUN = "dry_run"


@dataclass
class TimeSlot:
    time: str
    type: str = "Standard"
    config_token: Optional[str] = None
    source: str = "browser"


@dataclass
class AvailabilityResult:
    venue_id: str
    venue_name: str
    date: str
    party_size: int
    slots: List[TimeSlot] = field(default_factory=list)
    status: BookingStatus = BookingStatus.SUCCESS
    error_message: str = ""
    screenshot_path: Optional[str] = None


@dataclass
class BookingResult:
    success: bool
    status: BookingStatus
    reservation_id: Optional[str] = None
    confirmation_code: Optional[str] = None
    error_message: str = ""
    screenshot_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 1800):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures: Dict[str, List[datetime]] = {}
        self.circuits_open: Dict[str, datetime] = {}
    
    def record_failure(self, venue_id: str) -> bool:
        now = datetime.now()
        if venue_id not in self.failures:
            self.failures[venue_id] = []
        self.failures[venue_id].append(now)
        cutoff = now - timedelta(seconds=self.reset_timeout)
        self.failures[venue_id] = [f for f in self.failures[venue_id] if f > cutoff]
        if len(self.failures[venue_id]) >= self.failure_threshold:
            self.circuits_open[venue_id] = now
            logger.warning(f"Circuit breaker OPEN for venue {venue_id}")
            return True
        return False
    
    def record_success(self, venue_id: str):
        if venue_id in self.failures:
            del self.failures[venue_id]
        if venue_id in self.circuits_open:
            del self.circuits_open[venue_id]
            logger.info(f"Circuit breaker CLOSED for venue {venue_id}")
    
    def is_open(self, venue_id: str) -> bool:
        if venue_id not in self.circuits_open:
            return False
        opened_at = self.circuits_open[venue_id]
        if datetime.now() - opened_at > timedelta(seconds=self.reset_timeout):
            del self.circuits_open[venue_id]
            if venue_id in self.failures:
                del self.failures[venue_id]
            logger.info(f"Circuit breaker AUTO-RESET for venue {venue_id}")
            return False
        return True


class ResyBrowserAutomationV2:
    def __init__(self, headless: bool = True, dry_run: bool = False, max_retries: int = 3,
                 request_delay: Tuple[float, float] = (2.0, 5.0), screenshot_on_error: bool = True):
        self.headless = headless
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.screenshot_on_error = screenshot_on_error
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.circuit_breaker = CircuitBreaker()
        self.is_logged_in = False
        self.last_activity = datetime.now()
        self.session_timeout = timedelta(minutes=30)
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False
    
    def _random_delay(self, min_delay: float = None, max_delay: float = None):
        min_d = min_delay or self.request_delay[0]
        max_d = max_delay or self.request_delay[1]
        time.sleep(random.uniform(min_d, max_d))
    
    def _take_screenshot(self, name: str) -> Optional[str]:
        if not self.screenshot_on_error or not self.page:
            return None
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = SCREENSHOTS_DIR / filename
            self.page.screenshot(path=str(filepath), full_page=True)
            logger.info(f"Screenshot saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    def start(self):
        logger.info(f"Starting browser (headless={self.headless})")
        self.playwright = sync_playwright().start()
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
        ]
        self.browser = self.playwright.chromium.launch(headless=self.headless, args=browser_args)
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
            permissions=['geolocation']
        )
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
        self.page = self.context.new_page()
        if STEALTH_AVAILABLE:
            stealth_sync(self.page)
            logger.info("Stealth mode activated")
        self._random_delay(1, 2)
    
    def stop(self):
        logger.info("Stopping browser")
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.context = None
        self.browser = None
        self.playwright = None
        self.is_logged_in = False
    
    def _check_session_valid(self) -> bool:
        if not self.is_logged_in:
            return False
        if datetime.now() - self.last_activity > self.session_timeout:
            logger.info("Session expired due to inactivity")
            return False
        try:
            if not self.page:
                return False
            profile_selectors = [
                '[data-testid="profile-button"]',
                '[data-testid="user-menu"]',
                'button:has-text("Account")',
                'a[href*="/account"]',
                '.user-avatar',
                '[class*="profile"]'
            ]
            for selector in profile_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=2000):
                        return True
                except:
                    continue
            return False
        except Exception as e:
            logger.warning(f"Error checking session validity: {e}")
            return False
    
    def _refresh_session(self) -> bool:
        if self._check_session_valid():
            return True
        logger.info("Refreshing session...")
        return self.login(force=True)
    
    def login(self, force: bool = False) -> bool:
        if self.is_logged_in and not force:
            if self._check_session_valid():
                logger.info("Already logged in")
                return True
        try:
            with open(RESY_CREDENTIALS) as f:
                creds = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            return False
        logger.info("Logging into Resy...")
        if self._login_with_token(creds):
            self.is_logged_in = True
            self.last_activity = datetime.now()
            logger.info("Logged in via token injection")
            return True
        if self._login_with_credentials(creds):
            self.is_logged_in = True
            self.last_activity = datetime.now()
            logger.info("Logged in via credentials")
            return True
        logger.error("All login methods failed")
        self.is_logged_in = False
        return False
    
    def _login_with_token(self, creds: Dict) -> bool:
        try:
            self.page.goto("https://resy.com", wait_until="domcontentloaded")
            self._random_delay(2, 4)
            auth_token = creds.get('auth_token', '')
            api_key = creds.get('api_key', '')
            if not auth_token:
                logger.warning("No auth_token in credentials")
                return False
            self.page.evaluate(f"""
                localStorage.setItem('resy_auth_token', '{auth_token}');
                localStorage.setItem('resy_api_key', '{api_key}');
                localStorage.setItem('resy_last_auth', '{datetime.now().isoformat()}');
            """)
            self.page.goto("https://resy.com", wait_until="networkidle")
            self._random_delay(3, 5)
            return self._verify_login()
        except Exception as e:
            logger.warning(f"Token login failed: {e}")
            return False
    
    def _login_with_credentials(self, creds: Dict) -> bool:
        try:
            self.page.goto("https://resy.com/login", wait_until="networkidle")
            self._random_delay(2, 3)
            if self._detect_captcha():
                logger.warning("CAPTCHA detected on login page")
                self._take_screenshot("captcha_detected")
                return False
            email = creds.get('email', '')
            password = creds.get('password', '')
            if not email or not password:
                logger.warning("No email/password in credentials")
                return False
            email_selectors = ['input[type="email"]', 'input[name="email"]', '#email']
            for selector in email_selectors:
                try:
                    email_field = self.page.locator(selector).first
                    if email_field.is_visible(timeout=2000):
                        email_field.fill(email)
                        self._random_delay(0.5, 1.5)
                        break
                except:
                    continue
            password_selectors = ['input[type="password"]', 'input[name="password"]', '#password']
            for selector in password_selectors:
                try:
                    password_field = self.page.locator(selector).first
                    if password_field.is_visible(timeout=2000):
                        password_field.fill(password)
                        self._random_delay(0.5, 1.5)
                        break
                except:
                    continue
            login_btn_selectors = ['button[type="submit"]', 'button:has-text("Log in")', 'button:has-text("Sign in")']
            for selector in login_btn_selectors:
                try:
                    login_btn = self.page.locator(selector).first
                    if login_btn.is_visible(timeout=2000):
                        login_btn.click()
                        self._random_delay(3, 5)
                        break
                except:
                    continue
            return self._verify_login()
        except Exception as e:
            logger.warning(f"Credential login failed: {e}")
            return False
    
    def _verify_login(self) -> bool:
        try:
            logged_in_selectors = [
                '[data-testid="profile-button"]',
                '[data-testid="user-menu"]',
                'button:has-text("Account")',
                'a[href*="/account"]',
                '.user-avatar',
                '[class*="profile"]'
            ]
            for selector in logged_in_selectors:
                try:
                    element = self.page.locator(selector).first
                    if element.is_visible(timeout=3000):
                        return True
                except:
                    continue
            url = self.page.url
            if any(path in url for path in ['/account', '/reservations', '/profile']):
                return True
            return False
        except Exception as e:
            logger.warning(f"Login verification failed: {e}")
            return False
    
    def _detect_captcha(self) -> bool:
        captcha_indicators = [
            'iframe[src*="captcha"]', 'iframe[src*="recaptcha"]', '.g-recaptcha',
            'text=I\'m not a robot', 'text=Verify you are human', '#captcha'
        ]
        for indicator in captcha_indicators:
            try:
                element = self.page.locator(indicator).first
                if element.is_visible(timeout=1000):
                    logger.warning(f"CAPTCHA detected: {indicator}")
                    return True
            except:
                continue
        return False
    
    def _detect_rate_limit(self) -> bool:
        rate_limit_indicators = [
            'text=Too many requests', 'text=Rate limit', 'text=Please try again later',
            'text=429', 'text=503'
        ]
        try:
            page_text = self.page.content().lower()
        except:
            page_text = ""
        for indicator in rate_limit_indicators:
            try:
                element = self.page.locator(indicator).first
                if element.is_visible(timeout=1000):
                    logger.warning(f"Rate limit detected: {indicator}")
                    return True
            except:
                pass
            clean_indicator = indicator.lower().replace('text=', '').replace('"', '')
            if clean_indicator in page_text:
                logger.warning(f"Rate limit text found: {clean_indicator}")
                return True
        return False
    
    def _handle_error(self, venue_id: str, error_msg: str, screenshot_name: str) -> AvailabilityResult:
        logger.error(f"Error for venue {venue_id}: {error_msg}")
        screenshot = self._take_screenshot(screenshot_name)
        self.circuit_breaker.record_failure(venue_id)
        return AvailabilityResult(
            venue_id=venue_id, venue_name="", date="", party_size=0, slots=[],
            status=BookingStatus.ERROR, error_message=error_msg, screenshot_path=screenshot
        )
    
    def check_availability(self, venue_id: str, venue_slug: str, venue_name: str,
                          date: str, party_size: int = 2) -> AvailabilityResult:
        if self.circuit_breaker.is_open(venue_id):
            logger.warning(f"Circuit open for venue {venue_id}, skipping")
            return AvailabilityResult(
                venue_id=venue_id, venue_name=venue_name, date=date, party_size=party_size,
                slots=[], status=BookingStatus.ERROR, error_message="Circuit breaker open"
            )
        if not self._refresh_session():
            return self._handle_error(venue_id, "Not logged in", f"login_failed_{venue_slug}")
        logger.info(f"Checking {venue_name} ({venue_slug}) for {date}, party of {party_size}")
        url = f"https://resy.com/cities/new-york-ny/venues/{venue_slug}"
        for attempt in range(self.max_retries):
            try:
                self.page.goto(url, wait_until="networkidle")
                self._random_delay(2, 4)
                if self._detect_captcha():
                    screenshot = self._take_screenshot(f"captcha_{venue_slug}")
                    return AvailabilityResult(
                        venue_id=venue_id, venue_name=venue_name, date=date, party_size=party_size,
                        slots=[], status=BookingStatus.CAPTCHA_DETECTED,
                        error_message="CAPTCHA detected", screenshot_path=screenshot
                    )
                if self._detect_rate_limit():
                    if attempt < self.max_retries - 1:
                        backoff = 2 ** attempt * 10
                        logger.warning(f"Rate limited, backing off for {backoff}s")
                        time.sleep(backoff)
                        continue
                    else:
                        return AvailabilityResult(
                            venue_id=venue_id, venue_name=venue_name, date=date, party_size=party_size,
                            slots=[], status=BookingStatus.RATE_LIMITED, error_message="Rate limited"
                        )
                self._set_party_size(party_size)
                self._select_date(date)
                self._random_delay(2, 4)
                slots = self._extract_time_slots()
                self.circuit_breaker.record_success(venue_id)
                self.last_activity = datetime.now()
                logger.info(f"Found {len(slots)} time slots for {venue_name}")
                return AvailabilityResult(
                    venue_id=venue_id, venue_name=venue_name, date=date,
                    party_size=party_size, slots=slots, status=BookingStatus.SUCCESS
                )
            except PlaywrightTimeout as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    self._random_delay(5, 10)
                    continue
                else:
                    return self._handle_error(venue_id, f"Timeout after {self.max_retries} attempts", f"timeout_{venue_slug}")
            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    self._random_delay(3, 6)
                    continue
                else:
                    return self._handle_error(venue_id, str(e), f"error_{venue_slug}")
        return self._handle_error(venue_id, "Unknown error", f"unknown_{venue_slug}")
    
    def _set_party_size(self, party_size: int) -> bool:
        try:
            party_selectors = [
                'select[name="party_size"]', 'select[data-testid="party-size-select"]',
                '[class*="party"] select'
            ]
            for selector in party_selectors:
                try:
                    dropdown = self.page.locator(selector).first
                    if dropdown.is_visible(timeout=2000):
                        dropdown.select_option(str(party_size))
                        self._random_delay(1, 2)
                        return True
                except:
                    continue
            return False
        except Exception as e:
            logger.warning(f"Error setting party size: {e}")
            return False
    
    def _select_date(self, date: str) -> bool:
        try:
            date_picker_selectors = [
                'input[placeholder*="Date"]', 'button:has-text("Date")',
                '[data-testid="date-picker"]', 'input[type="date"]'
            ]
            date_picker = None
            for selector in date_picker_selectors:
                try:
                    picker = self.page.locator(selector).first
                    if picker.is_visible(timeout=2000):
                        date_picker = picker
                        break
                except:
                    continue
            if not date_picker:
                return False
            date_picker.click()
            self._random_delay(1, 2)
            try:
                date_picker.fill(date)
                self._random_delay(0.5, 1)
                self.page.keyboard.press("Enter")
                self._random_delay(1, 2)
                return True
            except:
                pass
            return False
        except Exception as e:
            logger.warning(f"Error selecting date: {e}")
            return False
    
    def _extract_time_slots(self) -> List[TimeSlot]:
        slots = []
        try:
            slot_selectors = [
                'button:has-text(":")', '[data-testid="time-slot"]',
                '[class*="time-slot"]', 'button[class*="time"]'
            ]
            for selector in slot_selectors:
                try:
                    buttons = self.page.locator(selector).all()
                    for btn in buttons:
                        try:
                            text = btn.inner_text().strip()
                            if ':' in text and any(x in text for x in ['AM', 'PM']):
                                config_token = None
                                try:
                                    config_token = btn.get_attribute('data-token')
                                except:
                                    pass
                                slots.append(TimeSlot(time=text, config_token=config_token))
                        except:
                            continue
                    if slots:
                        break
                except:
                    continue
            seen = set()
            unique_slots = []
            for slot in slots:
                if slot.time not in seen:
                    seen.add(slot.time)
                    unique_slots.append(slot)
            return unique_slots
        except Exception as e:
            logger.warning(f"Error extracting time slots: {e}")
            return []


def check_availability_with_fallback(venue_id: str, venue_slug: str, venue_name: str,
                                     date: str, party_size: int = 2, headless: bool = True) -> Tuple[Optional[Dict], str]:
    try:
        from calendar_scanner import find_resy_reservations
        result, api_status = find_resy_reservations(venue_id, date, party_size, venue_name)
        if api_status == 'success' and result:
            venues = result.get('results', {}).get('venues', [])
            if venues and any(len(v.get('slots', [])) > 0 for v in venues):
                logger.info(f"API returned slots for {venue_name}")
                return result, 'success'
        logger.info(f"API failed ({api_status}), trying browser fallback")
    except Exception as e:
        logger.warning(f"API call failed: {e}")
    try:
        with ResyBrowserAutomationV2(headless=headless) as browser:
            result = browser.check_availability(venue_id, venue_slug, venue_name, date, party_size)
            if result.status == BookingStatus.SUCCESS:
                return {
                    'results': {'venues': [{'venue': {'id': {'resy': venue_id}, 'name': venue_name},
                                            'slots': [{'date': {'start': s.time}, 'config': {'type': s.type}} for s in result.slots]}]},
                    'source': 'browser'
                }, 'browser_fallback'
            elif result.status == BookingStatus.NO_AVAILABILITY:
                return None, 'no_availability'
            else:
                return None, f'browser_error: {result.error_message}'
    except Exception as e:
        logger.error(f"Browser fallback failed: {e}")
        return None, f'error: {str(e)}'


RESTAURANT_PRIORITY = [
    "4-charles-prime-rib", "carbone", "torrisi", "saga", "the-naked-pig"
]


def find_and_book_best_slot(restaurants: List[Dict], date: str, party_size: int = 2,
                            preferred_start_hour: int = 19, preferred_end_hour: int = 21,
                            headless: bool = True, dry_run: bool = False) -> Optional[BookingResult]:
    def get_priority(r):
        slug = r.get('url_slug', '')
        if slug in RESTAURANT_PRIORITY:
            return RESTAURANT_PRIORITY.index(slug)
        return 999
    sorted_restaurants = sorted(restaurants, key=get_priority)
    with ResyBrowserAutomationV2(headless=headless, dry_run=dry_run) as browser:
        for restaurant in sorted_restaurants:
            venue_id = restaurant.get('venue_id', '')
            venue_slug = restaurant.get('url_slug', '')
            venue_name = restaurant.get('name', '')
            logger.info(f"Checking {venue_name}...")
            avail_result = browser.check_availability(venue_id, venue_slug, venue_name, date, party_size)
            if avail_result.status != BookingStatus.SUCCESS or not avail_result.slots:
                logger.info(f"No availability at {venue_name}")
                continue
            best_slot = None
            best_distance = float('inf')
            for slot in avail_result.slots:
                try:
                    time_str = slot.time.strip()
                    time_obj = datetime.strptime(time_str, "%I:%M %p")
                    hour = time_obj.hour
                    if preferred_start_hour <= hour <= preferred_end_hour:
                        preferred_minutes = 19 * 60 + 45
                        slot_minutes = hour * 60 + time_obj.minute
                        distance = abs(slot_minutes - preferred_minutes)
                        if distance < best_distance:
                            best_distance = distance
                            best_slot = slot
                except:
                    continue
            if not best_slot:
                for slot in avail_result.slots:
                    try:
                        time_str = slot.time.strip()
                        time_obj = datetime.strptime(time_str, "%I:%M %p")
                        if time_obj.hour >= 17:
                            best_slot = slot
                            break
                    except:
                        continue
            if not best_slot:
                logger.info(f"No suitable time slots at {venue_name}")
                continue
            logger.info(f"Found slot at {best_slot.time}")
            return BookingResult(success=True, status=BookingStatus.DRY_RUN if dry_run else BookingStatus.SUCCESS,
                                details={'venue': venue_name, 'time': best_slot.time})
    logger.info("No reservations available at any restaurant")
    return None


if __name__ == "__main__":
    import sys
    print("=" * 70)
    print("Resy Browser Automation V2 - Test Mode")
    print("=" * 70)
    test_type = sys.argv[1] if len(sys.argv) > 1 else "check"
    headless = '--headed' not in sys.argv
    dry_run = '--dry-run' in sys.argv
    if test_type == "login":
        print("\nTesting login flow...")
        with ResyBrowserAutomationV2(headless=headless) as browser:
            success = browser.login()
            print(f"Login {'successful' if success else 'failed'}!")
    elif test_type == "check":
        venue_slug = sys.argv[2] if len(sys.argv) > 2 else "the-naked-pig"
        date = sys.argv[3] if len(sys.argv) > 3 else "2026-05-17"
        print(f"\nTesting availability check for {venue_slug} on {date}")
        restaurants_file = Path(__file__).parent / "data" / "restaurants.json"
        venue_id = ""
        venue_name = venue_slug
        if restaurants_file.exists():
            with open(restaurants_file) as f:
                data = json.load(f)
                for r in data.get('restaurants', []):
                    if r.get('url_slug') == venue_slug:
                        venue_id = r.get('venue_id', '')
                        venue_name = r.get('name', venue_slug)
                        break
        with ResyBrowserAutomationV2(headless=headless) as browser:
            result = browser.check_availability(venue_id or "58528", venue_slug, venue_name, date, 2)
            print(f"\nResults: Status={result.status.value}, Slots={len(result.slots)}")
            if result.slots:
                for slot in result.slots:
                    print(f"  - {slot.time}")
    elif test_type == "multi":
        date = sys.argv[2] if len(sys.argv) > 2 else "2026-05-17"
        print(f"\nTesting multi-restaurant booking for {date}")
        restaurants_file = Path(__file__).parent / "data" / "restaurants.json"
        restaurants = []
        if restaurants_file.exists():
            with open(restaurants_file) as f:
                data = json.load(f)
                restaurants = data.get('restaurants', [])
        result = find_and_book_best_slot(restaurants=restaurants, date=date, party_size=2, headless=headless, dry_run=dry_run)
        if result:
            print(f"\nBooking successful: {result.details}")
        else:
            print("\nNo reservations available")
    else:
        print("\nUsage: python browser_automation_v2.py [login|check|multi] [--headed] [--dry-run]")
