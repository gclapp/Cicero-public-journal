#!/usr/bin/env python3
"""
Resy Restaurant List Manager
Web interface for managing restaurant preferences
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import json
import hashlib
import os
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from trips import (
    get_trips_from_cache, get_upcoming_trips, 
    skip_date, unskip_date, get_skipped_dates_list, is_date_skipped
)
from monitoring import (
    load_monitoring_data, log_scan, log_booking, log_error, 
    resolve_error, get_system_health, get_scan_history, 
    get_error_summary, get_log_files, read_log_file,
    get_reservation_attempts, get_attempts_summary
)

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.template_filter('format_date')
def format_date_filter(date_str):
    """Format date string for display"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%A, %B %d, %Y')
    except:
        return date_str

# Data directory
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Resy credentials
RESY_CREDENTIALS_PATH = Path.home() / ".openclaw" / "config" / "resy-credentials.json"

# NYC Restaurant database
NYC_RESTAURANTS_FILE = DATA_DIR / "nyc_restaurants.json"

def load_resy_credentials():
    """Load Resy API credentials"""
    if RESY_CREDENTIALS_PATH.exists():
        with open(RESY_CREDENTIALS_PATH) as f:
            return json.load(f)
    return None

RESTAURANTS_FILE = DATA_DIR / "restaurants.json"
USERS_FILE = DATA_DIR / "users.json"
RESERVATIONS_FILE = DATA_DIR / "reservations.json"

def init_files():
    """Initialize data files if they don't exist"""
    if not RESTAURANTS_FILE.exists():
        with open(RESTAURANTS_FILE, 'w') as f:
            json.dump({"restaurants": []}, f)
    
    if not USERS_FILE.exists():
        # Create default admin user (geoff)
        default_users = {
            "users": [
                {
                    "email": "[REDACTED]",
                    "password_hash": hashlib.sha256("changeme123".encode()).hexdigest(),
                    "is_admin": True,
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f)
    
    if not RESERVATIONS_FILE.exists():
        with open(RESERVATIONS_FILE, 'w') as f:
            json.dump({"reservations": []}, f)

def load_restaurants():
    """Load restaurant list"""
    with open(RESTAURANTS_FILE) as f:
        return json.load(f)

def save_restaurants(data):
    """Save restaurant list"""
    with open(RESTAURANTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    """Load users"""
    with open(USERS_FILE) as f:
        return json.load(f)

def save_users(data):
    """Save users"""
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_reservations():
    """Load reservation history"""
    with open(RESERVATIONS_FILE) as f:
        return json.load(f)

def save_reservations(data):
    """Save reservation history"""
    with open(RESERVATIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_nyc_restaurants():
    """Load local NYC restaurant database"""
    if NYC_RESTAURANTS_FILE.exists():
        with open(NYC_RESTAURANTS_FILE) as f:
            return json.load(f)
    return {'restaurants': []}

def search_local_restaurants(query):
    """Search local restaurant database by name"""
    db = load_nyc_restaurants()
    restaurants = db.get('restaurants', [])
    
    if not query:
        return restaurants[:10]
    
    query_lower = query.lower()
    matches = []
    
    for r in restaurants:
        name = r.get('name', '').lower()
        restaurant_type = r.get('type', '').lower()
        neighborhood = r.get('neighborhood', '').lower()
        
        # Score matches
        score = 0
        if query_lower in name:
            score += 10
        if query_lower in restaurant_type:
            score += 5
        if query_lower in neighborhood:
            score += 3
        
        if score > 0:
            matches.append((score, r))
    
    # Sort by score and return top matches
    matches.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in matches[:10]]

def get_venue_details(venue_id):
    """Get detailed venue info including images and coordinates"""
    import urllib.request
    import urllib.error
    
    creds = load_resy_credentials()
    if not creds:
        return None
    
    url = f"https://api.resy.com/3/venue?id={venue_id}"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            venue = json.loads(response.read().decode())
            
            # Extract key info
            location = venue.get('location', {})
            images = venue.get('images', [])
            
            # Get the best image (usually first one)
            image_url = images[0] if images else None
            
            # Get description from content
            description = ""
            for content in venue.get('content', []):
                if content.get('name') == 'why_we_like_it':
                    description = content.get('body', '')
                    break
            
            # Get rating from rater list
            rater_list = venue.get('rater', [])
            rating = rater_list[0].get('score') if rater_list else None
            reviews = rater_list[0].get('total') if rater_list else 0
            
            return {
                'id': venue_id,
                'name': venue.get('name'),
                'image_url': image_url,
                'description': description,
                'address': location.get('address_1'),
                'neighborhood': location.get('neighborhood'),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'phone': venue.get('contact', {}).get('phone_number'),
                'website': venue.get('contact', {}).get('url'),
                'rating': rating,
                'reviews': reviews,
                'price': '$' * venue.get('price_range_id', 1)
            }
            
    except Exception as e:
        print(f"Error fetching venue {venue_id}: {e}")
        return None

def search_resy_venues(query, lat, long, day, party_size=2):
    """Search Resy for venues by name/location"""
    import urllib.request
    import urllib.error
    
    creds = load_resy_credentials()
    if not creds:
        return {'error': 'Resy credentials not configured'}
    
    # Use the browse endpoint - it returns popular venues
    url = f"https://api.resy.com/3/venues?lat={lat}&long={long}&day={day}&party_size={party_size}"
    
    headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Get all venues
            venues = data.get('results', {}).get('venues', [])
            
            # Filter by query if provided
            if query:
                query_lower = query.lower()
                venues = [v for v in venues if query_lower in v.get('name', '').lower()]
            
            # Format results
            results = []
            for venue in venues[:10]:  # Limit to 10 results
                location = venue.get('location', {})
                venue_id = venue.get('id', {}).get('resy')
                results.append({
                    'id': venue_id,
                    'venue_id': venue_id,
                    'name': venue.get('name'),
                    'type': venue.get('type', 'Restaurant'),
                    'neighborhood': location.get('neighborhood', ''),
                    'address': location.get('address_1', ''),
                    'rating': venue.get('rater', [{}])[0].get('score'),
                    'reviews': venue.get('rater', [{}])[0].get('total', 0),
                    'price': '$' * venue.get('price_range_id', 1)
                })
            
            return {'venues': results}
            
    except urllib.error.HTTPError as e:
        return {'error': f'API Error: {e.code}'}
    except Exception as e:
        return {'error': str(e)}

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        users = load_users()
        user = next((u for u in users['users'] if u['email'] == session['user_email']), None)
        if not user or not user.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Main page - restaurant list"""
    data = load_restaurants()
    return render_template('index.html', restaurants=data['restaurants'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        users = load_users()
        password_hash = hash_password(password)
        
        user = next((u for u in users['users'] if u['email'] == email and u['password_hash'] == password_hash), None)
        
        if user:
            session['user_email'] = email
            session['is_admin'] = user.get('is_admin', False)
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/restaurants', methods=['GET', 'POST'])
@login_required
def api_restaurants():
    """API for restaurant list"""
    if request.method == 'GET':
        data = load_restaurants()
        return jsonify(data)
    
    elif request.method == 'POST':
        data = request.json
        action = data.get('action')
        
        restaurants_data = load_restaurants()
        restaurants = restaurants_data['restaurants']
        
        if action == 'add':
            new_restaurant = {
                'id': len(restaurants) + 1,
                'name': data['name'],
                'venue_id': data['venue_id'],
                'city': data.get('city', 'NYC'),
                'cuisine': data.get('cuisine', ''),
                'priority': len(restaurants) + 1,
                'notes': data.get('notes', ''),
                'added_at': datetime.now().isoformat(),
                'last_booked': None
            }
            restaurants.append(new_restaurant)
            save_restaurants(restaurants_data)
            return jsonify({'success': True, 'restaurant': new_restaurant})
        
        elif action == 'remove':
            restaurant_id = data.get('id')
            restaurants = [r for r in restaurants if r['id'] != restaurant_id]
            # Reorder priorities
            for i, r in enumerate(restaurants):
                r['priority'] = i + 1
            save_restaurants(restaurants_data)
            return jsonify({'success': True})
        
        elif action == 'reorder':
            new_order = data.get('order', [])  # List of IDs in new order
            restaurants_map = {r['id']: r for r in restaurants}
            new_restaurants = []
            for rid in new_order:
                if rid in restaurants_map:
                    restaurants_map[rid]['priority'] = len(new_restaurants) + 1
                    new_restaurants.append(restaurants_map[rid])
            restaurants_data['restaurants'] = new_restaurants
            save_restaurants(restaurants_data)
            return jsonify({'success': True})
        
        elif action == 'mark_booked':
            restaurant_id = data.get('id')
            for r in restaurants:
                if r['id'] == restaurant_id:
                    r['last_booked'] = datetime.now().isoformat()
                    # Move to bottom of priority
                    r['priority'] = len(restaurants) + 100
                    break
            # Reorder
            restaurants.sort(key=lambda x: x['priority'])
            for i, r in enumerate(restaurants):
                r['priority'] = i + 1
            save_restaurants(restaurants_data)
            return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Unknown action'})

@app.route('/api/restaurants/nyc')
def api_restaurants_nyc():
    """Get NYC restaurants for automation"""
    data = load_restaurants()
    nyc_restaurants = [r for r in data['restaurants'] if r.get('city', 'NYC') == 'NYC']
    return jsonify({'restaurants': nyc_restaurants})

@app.route('/admin/users')
@admin_required
def admin_users():
    """User management page"""
    users = load_users()
    return render_template('users.html', users=users['users'])

@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
@admin_required
def api_users():
    """API for user management"""
    if request.method == 'GET':
        users = load_users()
        # Don't return password hashes
        safe_users = [{'email': u['email'], 'is_admin': u.get('is_admin', False), 
                      'created_at': u.get('created_at', '')} for u in users['users']]
        return jsonify({'users': safe_users})
    
    elif request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        is_admin = data.get('is_admin', False)
        
        users = load_users()
        
        # Check if user exists
        if any(u['email'] == email for u in users['users']):
            return jsonify({'success': False, 'error': 'User already exists'})
        
        new_user = {
            'email': email,
            'password_hash': hash_password(password),
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat()
        }
        users['users'].append(new_user)
        save_users(users)
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        email = request.json.get('email')
        users = load_users()
        users['users'] = [u for u in users['users'] if u['email'] != email]
        save_users(users)
        return jsonify({'success': True})

@app.route('/api/reservations', methods=['GET', 'POST'])
@login_required
def api_reservations():
    """API for reservation history"""
    if request.method == 'GET':
        data = load_reservations()
        return jsonify(data)
    
    elif request.method == 'POST':
        data = request.json
        reservations_data = load_reservations()
        
        new_reservation = {
            'id': len(reservations_data['reservations']) + 1,
            'restaurant_name': data['restaurant_name'],
            'venue_id': data['venue_id'],
            'date': data['date'],
            'time': data['time'],
            'party_size': data['party_size'],
            'confirmation_code': data.get('confirmation_code', ''),
            'created_at': datetime.now().isoformat()
        }
        reservations_data['reservations'].append(new_reservation)
        save_reservations(reservations_data)
        
        return jsonify({'success': True, 'reservation': new_reservation})

@app.route('/trips')
@login_required
def trips_page():
    """Trips page showing upcoming trips and reservation status"""
    # Refresh trips data
    trips = get_upcoming_trips()
    return render_template('trips.html', trips=trips)

@app.route('/api/trips')
@login_required
def api_trips():
    """API for trips data"""
    # Refresh trips from calendar
    trips = get_upcoming_trips()
    return jsonify({'trips': trips})

@app.route('/api/trips/refresh')
@login_required
def api_trips_refresh():
    """Force refresh trips from calendar"""
    trips = get_upcoming_trips()
    return jsonify({'success': True, 'trips': trips, 'count': len(trips)})

@app.route('/api/trips/skip', methods=['POST'])
@login_required
def api_skip_date():
    """Skip a date - don't look for reservations on this date"""
    data = request.json
    date_str = data.get('date')
    reason = data.get('reason', '')
    
    if not date_str:
        return jsonify({'success': False, 'error': 'Date required'}), 400
    
    success = skip_date(date_str, reason)
    if success:
        return jsonify({
            'success': True, 
            'message': f'Skipped {date_str}',
            'date': date_str,
            'reason': reason
        })
    else:
        return jsonify({
            'success': False, 
            'error': 'Date already skipped'
        }), 400

@app.route('/api/trips/unskip', methods=['POST'])
@login_required
def api_unskip_date():
    """Unskip a date - resume looking for reservations"""
    data = request.json
    date_str = data.get('date')
    
    if not date_str:
        return jsonify({'success': False, 'error': 'Date required'}), 400
    
    unskip_date(date_str)
    return jsonify({
        'success': True, 
        'message': f'Unskipped {date_str}',
        'date': date_str
    })

@app.route('/api/trips/skipped')
@login_required
def api_skipped_dates():
    """Get list of skipped dates"""
    skipped = get_skipped_dates_list()
    return jsonify({'skipped': skipped})

# Resy Search API
@app.route('/api/resy/search')
@login_required
def api_resy_search():
    """Search for restaurants - uses local database first, falls back to Resy API"""
    query = request.args.get('q', '')
    city = request.args.get('city', 'nyc')  # Default to NYC
    
    # First search local database (for NYC)
    if city == 'nyc':
        local_results = search_local_restaurants(query)
        if local_results:
            return jsonify({
                'venues': local_results,
                'source': 'local_database'
            })
    
    # Fall back to Resy API browse
    cities = {
        'nyc': {'lat': 40.7128, 'long': -74.0060, 'name': 'New York'},
        'la': {'lat': 34.0522, 'long': -118.2437, 'name': 'Los Angeles'},
        'sf': {'lat': 37.7749, 'long': -122.4194, 'name': 'San Francisco'},
        'chi': {'lat': 41.8781, 'long': -87.6298, 'name': 'Chicago'},
        'mia': {'lat': 25.7617, 'long': -80.1918, 'name': 'Miami'}
    }
    
    city_data = cities.get(city, cities['nyc'])
    
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    results = search_resy_venues(
        query=query,
        lat=city_data['lat'],
        long=city_data['long'],
        day=tomorrow,
        party_size=2
    )
    
    # If Resy API returns an error, return empty venues array with error message
    if 'error' in results:
        return jsonify({
            'venues': [],
            'error': results['error'],
            'source': 'resy_api'
        })
    
    results['source'] = 'resy_api'
    return jsonify(results)

@app.route('/api/resy/venue/<venue_id>')
@login_required
def api_resy_venue_details(venue_id):
    """Get detailed venue info including images and map coordinates"""
    details = get_venue_details(venue_id)
    if details:
        return jsonify(details)
    return jsonify({'error': 'Venue not found'}), 404

# Monitoring routes
@app.route('/admin/monitoring')
@admin_required
def monitoring_page():
    """System monitoring dashboard"""
    health = get_system_health()
    log_files = get_log_files()
    return render_template('monitoring.html', 
                          health=health, 
                          recent_errors=health['recent_errors'],
                          log_files=log_files)

@app.route('/api/monitoring/health')
@admin_required
def api_monitoring_health():
    """API for system health"""
    return jsonify(get_system_health())

@app.route('/api/monitoring/resolve-error', methods=['POST'])
@admin_required
def api_resolve_error():
    """Mark an error as resolved"""
    data = request.json
    index = data.get('index')
    success = resolve_error(index)
    return jsonify({'success': success})

@app.route('/api/monitoring/logs/<log_name>')
@admin_required
def api_view_log(log_name):
    """View log file contents"""
    content = read_log_file(log_name, lines=100)
    return jsonify({'content': content})

@app.route('/logs')
@login_required
def logs_page():
    """Reservation attempts log page"""
    return render_template('logs.html')

@app.route('/api/attempts')
@login_required
def api_attempts():
    """Get reservation attempts with filtering"""
    try:
        days = request.args.get('days', 7, type=int)
        status = request.args.get('status', None)
        trip_date = request.args.get('trip_date', None)
        
        attempts = get_reservation_attempts(
            days=days,
            trip_date=trip_date,
            status=status,
            limit=100
        )
        
        summary = get_attempts_summary(days=days)
        
        return jsonify({
            'success': True,
            'attempts': attempts,
            'summary': summary,
            'count': len(attempts)
        })
    except Exception as e:
        log_error('web_ui', 'api_error', f"Failed to get attempts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan-and-book', methods=['POST'])
@login_required
def api_scan_and_book():
    """Manually trigger calendar scan and booking process"""
    try:
        import subprocess
        import sys
        
        # Run the calendar scanner
        result = subprocess.run(
            [sys.executable, str(Path(__file__).parent / 'calendar_scanner.py')],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Parse the output to get stats
        output = result.stdout + result.stderr
        
        # Extract stats from output
        restaurants_checked = 0
        reservations_found = 0
        reservations_made = 0
        
        for line in output.split('\n'):
            if 'Checked' in line and 'restaurants' in line:
                try:
                    restaurants_checked = int(line.split('Checked')[1].split('restaurants')[0].strip())
                except:
                    pass
            elif 'Found' in line and 'available slots' in line:
                try:
                    reservations_found = int(line.split('Found')[1].split('available slots')[0].strip())
                except:
                    pass
            elif 'Made' in line and 'reservations' in line:
                try:
                    reservations_made = int(line.split('Made')[1].split('reservations')[0].strip())
                except:
                    pass
        
        return jsonify({
            'success': True,
            'restaurants_checked': restaurants_checked,
            'reservations_found': reservations_found,
            'reservations_made': reservations_made,
            'output': output[-500:]  # Last 500 chars for debugging
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Scan timed out after 5 minutes'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Error handlers to log UI errors
@app.errorhandler(500)
def internal_error(error):
    log_error('web_ui', 'server_error', str(error), 
              {'path': request.path, 'method': request.method},
              session.get('user_email'))
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    log_error('web_ui', 'not_found', f"Page not found: {request.path}",
              {'path': request.path, 'method': request.method},
              session.get('user_email'))
    return jsonify({'error': 'Not found'}), 404

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        health = get_system_health()
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'last_scan': health.get('last_scan_time'),
            'last_booking': health.get('last_booking_time'),
            'total_bookings': health.get('total_bookings', 0)
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    init_files()
    app.run(host='0.0.0.0', port=5000, debug=True)
