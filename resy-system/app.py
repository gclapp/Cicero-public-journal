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
import uuid

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
from circuit_breaker import (
    get_all_venue_statuses, get_problematic_venues, 
    reset_circuit, is_circuit_open
)

app = Flask(__name__)

# Load version info
VERSION_FILE = Path(__file__).parent / "version.json"
def load_version():
    """Load version information"""
    if VERSION_FILE.exists():
        with open(VERSION_FILE) as f:
            return json.load(f)
    return {
        "version": "v0.0.0_0",
        "date": "unknown",
        "counter": 0,
        "time": "00:00:00"
    }

# Make version available to all templates
@app.context_processor
def inject_version():
    return dict(app_version=load_version())

# Use a persistent secret key (stored in file) so sessions survive restarts
SECRET_KEY_FILE = Path(__file__).parent / "data" / ".secret_key"
if SECRET_KEY_FILE.exists():
    with open(SECRET_KEY_FILE, 'rb') as f:
        app.secret_key = f.read()
else:
    # Generate new secret key and save it
    app.secret_key = os.urandom(24)
    SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SECRET_KEY_FILE, 'wb') as f:
        f.write(app.secret_key)

# Upload configuration
UPLOAD_FOLDER = Path(__file__).parent / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

@app.template_filter('format_date')
def format_date_filter(date_str):
    """Format date string for display as MM-DD-YYYY"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%m-%d-%Y')
    except:
        return date_str

@app.template_filter('format_time_12h')
def format_time_12h_filter(time_str):
    """Convert 24-hour time to 12-hour AM/PM format"""
    if not time_str:
        return time_str
    try:
        # Handle both HH:MM and HH:MM:SS formats
        if len(time_str.split(':')) == 3:
            dt = datetime.strptime(time_str, '%H:%M:%S')
        else:
            dt = datetime.strptime(time_str, '%H:%M')
        return dt.strftime('%I:%M %p').lstrip('0')
    except:
        return time_str

@app.template_filter('format_datetime_pt')
def format_datetime_pt_filter(iso_str):
    """Convert ISO datetime to Pacific Time, formatted as MM-DD-YYYY HH:MM AM/PM"""
    if not iso_str:
        return None
    try:
        # Parse ISO format datetime
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        # Convert to Pacific Time (UTC-7 for PDT, UTC-8 for PST)
        # For simplicity, using UTC-7 (PDT) since it's currently April
        from datetime import timedelta
        pt_offset = timedelta(hours=-7)  # PDT (UTC-7)
        dt_pt = dt.replace(tzinfo=None) + pt_offset
        return dt_pt.strftime('%m-%d-%Y %I:%M %p').lstrip('0')
    except:
        return iso_str

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
                    "role": "admin",
                    "is_suspended": False,
                    "profile_image": None,
                    "created_at": datetime.now().isoformat()
                }
            ]
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f)
    else:
        # Migrate existing users to new schema
        migrate_users()
    
    if not RESERVATIONS_FILE.exists():
        with open(RESERVATIONS_FILE, 'w') as f:
            json.dump({"reservations": []}, f)

def migrate_users():
    """Migrate existing users to new schema with roles"""
    users = load_users()
    modified = False
    
    for user in users['users']:
        # Add role field if missing
        if 'role' not in user:
            # Default: existing admins stay admin, others become app_user
            if user.get('is_admin', False):
                user['role'] = 'admin'
            else:
                user['role'] = 'app_user'
            modified = True
        
        # Add is_suspended field if missing
        if 'is_suspended' not in user:
            user['is_suspended'] = False
            modified = True
        
        # Add profile_image field if missing
        if 'profile_image' not in user:
            user['profile_image'] = None
            modified = True
        
        # Add last_login field if missing
        if 'last_login' not in user:
            user['last_login'] = None
            modified = True
    
    if modified:
        save_users(users)

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

def search_local_restaurants(query, exclude_venue_ids=None):
    """Search local restaurant database by name"""
    db = load_nyc_restaurants()
    restaurants = db.get('restaurants', [])
    
    # Normalize exclude_venue_ids to strings for comparison
    if exclude_venue_ids is None:
        exclude_venue_ids = set()
    else:
        exclude_venue_ids = {str(vid) for vid in exclude_venue_ids if vid}
    
    if not query:
        # Filter out excluded venues even when no query
        return [r for r in restaurants[:20] if str(r.get('venue_id', '')) not in exclude_venue_ids]
    
    query_lower = query.lower()
    matches = []
    
    for r in restaurants:
        # Skip if venue_id is in exclude list
        if str(r.get('venue_id', '')) in exclude_venue_ids:
            continue
            
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
    return [r for _, r in matches[:20]]

def get_venue_details(venue_id):
    """Get detailed venue info - tries Resy API first, falls back to local database"""
    import urllib.request
    import urllib.error
    
    # First try to find in local database
    db = load_nyc_restaurants()
    local_venue = None
    for r in db.get('restaurants', []):
        if str(r.get('venue_id')) == str(venue_id):
            local_venue = r
            break
    
    # Try Resy API for full details
    creds = load_resy_credentials()
    if creds:
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
            print(f"Resy API error for venue {venue_id}: {e}")
    
    # Fall back to local data if Resy fails or no credentials
    if local_venue:
        return {
            'id': venue_id,
            'name': local_venue.get('name'),
            'image_url': None,
            'description': f"{local_venue.get('type', 'Restaurant')} in {local_venue.get('neighborhood', 'NYC')}",
            'address': f"{local_venue.get('neighborhood', 'NYC')}, New York",
            'neighborhood': local_venue.get('neighborhood'),
            'latitude': None,
            'longitude': None,
            'phone': None,
            'website': None,
            'rating': None,
            'reviews': 0,
            'price': local_venue.get('price', '$$$')
        }
    
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
            for venue in venues[:20]:  # Limit to 20 results
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

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_current_user():
    """Get current logged-in user data"""
    if 'user_email' not in session:
        return None
    users = load_users()
    return next((u for u in users['users'] if u['email'] == session['user_email']), None)

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        
        # Check if user is suspended
        user = get_current_user()
        if user and user.get('is_suspended', False):
            session.clear()
            flash('Your account has been suspended. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('login'))
        
        # Check if user is suspended
        if user.get('is_suspended', False):
            session.clear()
            flash('Your account has been suspended. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        # Check role - must be admin
        if user.get('role') != 'admin':
            flash('Admin access required', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

def app_user_required(f):
    """Decorator to require app_user or admin (not just calendar_user)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('login'))
        
        user = get_current_user()
        if not user:
            session.clear()
            return redirect(url_for('login'))
        
        # Check if user is suspended
        if user.get('is_suspended', False):
            session.clear()
            flash('Your account has been suspended. Please contact an administrator.', 'error')
            return redirect(url_for('login'))
        
        # Check role - must be app_user or admin
        role = user.get('role', 'app_user')
        if role not in ['admin', 'app_user']:
            flash('You do not have permission to access this feature.', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():
    """Main page - redirect to trips"""
    return redirect(url_for('trips_page'))

@app.route('/wishlist')
@app_user_required
def wishlist_page():
    """Wish List page - manage restaurant preferences"""
    return render_template('wishlist.html')

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
            # Check if user is suspended
            if user.get('is_suspended', False):
                flash('Your account has been suspended. Please contact an administrator.', 'error')
                return render_template('login.html')
            
            # Update last login time
            user['last_login'] = datetime.now().isoformat()
            save_users(users)
            
            session['user_email'] = email
            session['is_admin'] = user.get('role') == 'admin'
            session['user_role'] = user.get('role', 'app_user')
            session['profile_image'] = user.get('profile_image')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_current_user()
    return render_template('profile.html', user=user)

@app.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    # Support both JSON and form data
    if request.is_json:
        data = request.get_json()
        current_password = data.get('current_password')
        new_password = data.get('new_password')
    else:
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
    
    # Validate current password
    current_hash = hash_password(current_password)
    if current_hash != user['password_hash']:
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    # Validate new password
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
    
    # Update password
    users = load_users()
    for u in users['users']:
        if u['email'] == user['email']:
            u['password_hash'] = hash_password(new_password)
            break
    
    save_users(users)
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@app.route('/profile/upload-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Upload profile image"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'No image provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = UPLOAD_FOLDER / filename
        
        # Save file
        file.save(filepath)
        
        # Delete old image if exists
        old_image = user.get('profile_image')
        if old_image:
            old_path = UPLOAD_FOLDER / old_image
            if old_path.exists():
                old_path.unlink()
        
        # Update user record
        users = load_users()
        for u in users['users']:
            if u['email'] == user['email']:
                u['profile_image'] = filename
                break
        
        save_users(users)
        
        # Update session
        session['profile_image'] = filename
        
        return jsonify({
            'success': True,
            'image_url': f'/static/uploads/{filename}'
        })
    
    return jsonify({'success': False, 'error': 'Invalid file type'}), 400

@app.route('/profile/remove-image', methods=['POST'])
@login_required
def remove_profile_image():
    """Remove profile image"""
    user = get_current_user()
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    old_image = user.get('profile_image')
    if old_image:
        old_path = UPLOAD_FOLDER / old_image
        if old_path.exists():
            old_path.unlink()
    
    # Update user record
    users = load_users()
    for u in users['users']:
        if u['email'] == user['email']:
            u['profile_image'] = None
            break
    
    save_users(users)
    
    # Update session
    session['profile_image'] = None
    
    return jsonify({'success': True})

@app.route('/api/restaurants', methods=['GET', 'POST'])
@app_user_required
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
            venue_id = data['venue_id']
            
            # Check for duplicate by venue_id
            existing = None
            for r in restaurants:
                if r.get('venue_id') == venue_id:
                    existing = r
                    break
            
            if existing:
                return jsonify({
                    'success': False,
                    'error': 'duplicate',
                    'message': f'"{existing["name"]}" is already in your wish list',
                    'existing': existing
                })
            
            new_restaurant = {
                'id': len(restaurants) + 1,
                'name': data['name'],
                'venue_id': venue_id,
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

@app.route('/api/search-resy')
@app_user_required
def api_search_resy():
    """Search for restaurants - uses local database first, then Resy API"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    # Get currently saved restaurants to filter out
    saved_data = load_restaurants()
    saved_venue_ids = {r.get('venue_id') for r in saved_data.get('restaurants', []) if r.get('venue_id')}
    
    # First search local database (NYC restaurants) - WITHOUT filtering to check if matches exist
    all_local_results = search_local_restaurants(query, exclude_venue_ids=None)
    
    # Check if any matches were found but are already in wishlist
    excluded_count = 0
    for r in all_local_results:
        if r.get('venue_id') in saved_venue_ids:
            excluded_count += 1
    
    # Now get filtered results (excluding already saved)
    local_results = [r for r in all_local_results if r.get('venue_id') not in saved_venue_ids]
    
    if local_results:
        # Format as venues for frontend compatibility
        venues = []
        for r in local_results:
            venues.append({
                'venue_id': r.get('venue_id', ''),
                'name': r.get('name'),
                'type': r.get('type', 'Restaurant'),
                'neighborhood': r.get('neighborhood', ''),
                'price': r.get('price', '$$'),
                'source': 'local'
            })
        return jsonify({
            'venues': venues[:20],
            'source': 'local',
            'total_found': len(all_local_results),
            'excluded_count': excluded_count
        })
    
    # No local results - check if they were all excluded
    if excluded_count > 0:
        return jsonify({
            'venues': [],
            'source': 'local',
            'message': f'{excluded_count} restaurant(s) found but already in your wishlist',
            'excluded_count': excluded_count
        })
    
    # Fall back to Resy API browse if no local matches at all
    from datetime import date
    today = date.today().isoformat()
    results = search_resy_venues(query, 40.7128, -74.0060, today, 2)
    
    # Filter out already saved restaurants and limit to 20
    saved_venue_ids_str = {str(vid) for vid in saved_venue_ids}
    if 'venues' in results:
        results['venues'] = [v for v in results['venues'] if str(v.get('venue_id', '')) not in saved_venue_ids_str][:20]
    
    # Add info about search limitations
    if not results.get('venues') and not results.get('error'):
        results['message'] = 'No restaurants found. Try searching for a different name or cuisine type.'
    
    return jsonify(results)

@app.route('/admin/users')
@admin_required
def admin_users():
    """User management page"""
    users = load_users()
    return render_template('users.html', users=users['users'])

@app.route('/api/users', methods=['GET', 'POST', 'DELETE', 'PATCH'])
@admin_required
def api_users():
    """API for user management"""
    if request.method == 'GET':
        users = load_users()
        # Don't return password hashes
        safe_users = []
        for u in users['users']:
            safe_user = {
                'email': u['email'],
                'is_admin': u.get('role') == 'admin',
                'role': u.get('role', 'app_user'),
                'is_suspended': u.get('is_suspended', False),
                'profile_image': u.get('profile_image'),
                'created_at': u.get('created_at', '')
            }
            safe_users.append(safe_user)
        return jsonify({'users': safe_users})
    
    elif request.method == 'POST':
        data = request.json
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'app_user')
        is_admin = data.get('is_admin', False)
        
        # Support legacy is_admin field
        if is_admin:
            role = 'admin'
        
        # Validate role
        if role not in ['admin', 'app_user', 'calendar_user']:
            return jsonify({'success': False, 'error': 'Invalid role'})
        
        users = load_users()
        
        # Check if user exists
        if any(u['email'] == email for u in users['users']):
            return jsonify({'success': False, 'error': 'User already exists'})
        
        new_user = {
            'email': email,
            'password_hash': hash_password(password),
            'is_admin': role == 'admin',
            'role': role,
            'is_suspended': False,
            'profile_image': None,
            'created_at': datetime.now().isoformat()
        }
        users['users'].append(new_user)
        save_users(users)
        
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        email = request.json.get('email')
        
        # Prevent self-deletion
        if email == session.get('user_email'):
            return jsonify({'success': False, 'error': 'Cannot delete yourself'})
        
        users = load_users()
        
        # Find user and delete profile image if exists
        user_to_delete = next((u for u in users['users'] if u['email'] == email), None)
        if user_to_delete and user_to_delete.get('profile_image'):
            image_path = UPLOAD_FOLDER / user_to_delete['profile_image']
            if image_path.exists():
                image_path.unlink()
        
        users['users'] = [u for u in users['users'] if u['email'] != email]
        save_users(users)
        return jsonify({'success': True})
    
    elif request.method == 'PATCH':
        """Update user (suspend/unsuspend, change role)"""
        data = request.json
        email = data.get('email')
        action = data.get('action')
        
        users = load_users()
        user = next((u for u in users['users'] if u['email'] == email), None)
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'})
        
        # Prevent self-suspension
        if email == session.get('user_email') and action == 'suspend':
            return jsonify({'success': False, 'error': 'Cannot suspend yourself'})
        
        if action == 'suspend':
            user['is_suspended'] = True
        elif action == 'unsuspend':
            user['is_suspended'] = False
        elif action == 'change_role':
            new_role = data.get('role')
            if new_role not in ['admin', 'app_user', 'calendar_user']:
                return jsonify({'success': False, 'error': 'Invalid role'})
            user['role'] = new_role
            user['is_admin'] = new_role == 'admin'
        else:
            return jsonify({'success': False, 'error': 'Unknown action'})
        
        save_users(users)
        return jsonify({'success': True})

@app.route('/api/reservations', methods=['GET', 'POST'])
@app_user_required
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
@app_user_required
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
@app_user_required
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

@app.route('/api/reservations/cancel', methods=['POST'])
@app_user_required
def api_cancel_reservation():
    """Cancel a reservation on Resy"""
    data = request.json
    reservation_id = data.get('reservation_id')
    
    if not reservation_id:
        return jsonify({'success': False, 'error': 'Reservation ID required'}), 400
    
    # Load credentials
    creds = load_resy_credentials()
    if not creds:
        return jsonify({'success': False, 'error': 'Resy credentials not configured'}), 500
    
    import urllib.request
    import urllib.error
    
    # First, get the resy_token for this reservation
    resy_token = None
    try:
        url = "https://api.resy.com/3/user/reservations"
        headers = {
            "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
            "X-Resy-Auth-Token": creds["auth_token"],
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode())
            for res in res_data.get("reservations", []):
                if str(res.get("reservation_id")) == str(reservation_id):
                    resy_token = res.get("resy_token")
                    break
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to fetch reservation details: {str(e)}'}), 500
    
    if not resy_token:
        return jsonify({'success': False, 'error': 'Could not find reservation token'}), 404
    
    # Call Resy API to cancel using resy_token
    cancel_url = "https://api.resy.com/3/cancel"
    cancel_data = f"resy_token={resy_token}"
    
    cancel_headers = {
        "Authorization": f'ResyAPI api_key="{creds["api_key"]}"',
        "X-Resy-Auth-Token": creds["auth_token"],
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    req = urllib.request.Request(cancel_url, data=cancel_data.encode(), headers=cancel_headers, method='POST')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            # Remove from local reservations file
            reservations_data = load_reservations()
            reservations_data['reservations'] = [
                r for r in reservations_data['reservations'] 
                if str(r.get('resy_reservation_id')) != str(reservation_id)
            ]
            save_reservations(reservations_data)
            
            # Clear trips cache so page shows updated data
            from trips import TRIPS_CACHE_FILE
            if TRIPS_CACHE_FILE.exists():
                TRIPS_CACHE_FILE.unlink()
            
            return jsonify({'success': True, 'message': 'Reservation cancelled'})
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else 'Unknown error'
        return jsonify({'success': False, 'error': f'Resy API error: {e.code}', 'details': error_body}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Resy Search API
@app.route('/api/resy/search')
@app_user_required
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
@app_user_required
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
        restaurant = request.args.get('restaurant', None)
        
        attempts = get_reservation_attempts(
            days=days,
            trip_date=trip_date,
            status=status,
            limit=500
        )
        
        # Filter by restaurant name if provided
        if restaurant:
            attempts = [a for a in attempts if restaurant.lower() in a.get('restaurant_name', '').lower()]
        
        summary = get_attempts_summary(days=days)
        
        # Get unique restaurant names for filter dropdown
        all_restaurants = list(set(a.get('restaurant_name', '') for a in attempts if a.get('restaurant_name')))
        all_restaurants.sort()
        
        return jsonify({
            'success': True,
            'attempts': attempts,
            'summary': summary,
            'count': len(attempts),
            'restaurants': all_restaurants
        })
    except Exception as e:
        log_error('web_ui', 'api_error', f"Failed to get attempts: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/circuit-breaker')
@login_required
def api_circuit_breaker():
    """Get circuit breaker status for all venues"""
    try:
        problematic = get_problematic_venues()
        all_statuses = get_all_venue_statuses()
        
        return jsonify({
            'success': True,
            'problematic_venues': problematic,
            'total_venues': len(all_statuses),
            'circuit_open_count': len([v for v in all_statuses.values() if v.get('circuit_open', False)])
        })
    except Exception as e:
        log_error('web_ui', 'api_error', f"Failed to get circuit breaker data: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/circuit-breaker/reset', methods=['POST'])
@admin_required
def api_reset_circuit():
    """Reset circuit breaker for a venue"""
    try:
        data = request.json
        venue_id = data.get('venue_id')
        
        if not venue_id:
            return jsonify({'success': False, 'error': 'venue_id required'}), 400
        
        success = reset_circuit(venue_id)
        if success:
            return jsonify({'success': True, 'message': f'Circuit reset for venue {venue_id}'})
        else:
            return jsonify({'success': False, 'error': 'Venue not found'}), 404
    except Exception as e:
        log_error('web_ui', 'api_error', f"Failed to reset circuit: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scan-and-book', methods=['POST'])
@admin_required
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