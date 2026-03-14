#!/usr/bin/env python3
"""
Cicero API - Flask Backend
Main application entry point
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
import os
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    'postgresql://cicero:password@localhost/cicero_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)
login_manager = LoginManager(app)

# Import models
from models import User, WatchSearch, Watch, SearchSource, SearchLog, UserPreference

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Health check endpoint
@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

# Watch Search Endpoints
@app.route('/api/searches', methods=['GET'])
# @login_required
def get_searches():
    """Get all watch searches for current user"""
    searches = WatchSearch.query.filter_by(status='active').all()
    return jsonify([search.to_dict() for search in searches])

@app.route('/api/searches', methods=['POST'])
# @login_required
def create_search():
    """Create a new watch search"""
    data = request.get_json()
    
    search = WatchSearch(
        name=data['name'],
        brand=data['brand'],
        model_numbers=data.get('modelNumbers', []),
        year_min=data.get('years', {}).get('min'),
        year_max=data.get('years', {}).get('max'),
        dial_colors=data.get('dialColors', []),
        case_materials=data.get('caseMaterials', []),
        sources=data.get('sources', ['chrono24']),
        schedule=data.get('schedule', 'daily')
    )
    
    db.session.add(search)
    db.session.commit()
    
    # Trigger immediate search
    from tasks import run_watch_search
    run_watch_search.delay(search.id)
    
    return jsonify(search.to_dict()), 201

@app.route('/api/searches/<int:search_id>', methods=['GET'])
def get_search(search_id):
    """Get a specific search"""
    search = WatchSearch.query.get_or_404(search_id)
    return jsonify(search.to_dict())

@app.route('/api/searches/<int:search_id>/run', methods=['POST'])
def run_search(search_id):
    """Manually trigger a search"""
    search = WatchSearch.query.get_or_404(search_id)
    
    from tasks import run_watch_search
    run_watch_search.delay(search.id)
    
    return jsonify({'message': 'Search started', 'search_id': search_id})

# Watch Endpoints
@app.route('/api/watches', methods=['GET'])
def get_watches():
    """Get all watches with filtering and sorting"""
    # Get query parameters
    search_id = request.args.get('search_id', type=int)
    status = request.args.get('status')
    sort_by = request.args.get('sort', 'date_added-desc')
    hide_sold = request.args.get('hide_sold', 'false').lower() == 'true'
    
    # Build query
    query = Watch.query
    
    if search_id:
        query = query.filter_by(search_id=search_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if hide_sold:
        query = query.filter(Watch.status != 'sold')
    
    # Apply sorting
    if sort_by == 'date_added-desc':
        query = query.order_by(Watch.date_added.desc())
    elif sort_by == 'date_added-asc':
        query = query.order_by(Watch.date_added.asc())
    elif sort_by == 'rating-desc':
        query = query.order_by(Watch.user_rating.desc().nulls_last())
    elif sort_by == 'rating-asc':
        query = query.order_by(Watch.user_rating.asc().nulls_last())
    elif sort_by == 'year-desc':
        query = query.order_by(Watch.year.desc())
    elif sort_by == 'year-asc':
        query = query.order_by(Watch.year.asc())
    elif sort_by == 'price-asc':
        query = query.order_by(Watch.price.asc().nulls_last())
    elif sort_by == 'price-desc':
        query = query.order_by(Watch.price.desc().nulls_last())
    
    watches = query.all()
    return jsonify([watch.to_dict() for watch in watches])

@app.route('/api/watches/<int:watch_id>', methods=['GET'])
def get_watch(watch_id):
    """Get a specific watch"""
    watch = Watch.query.get_or_404(watch_id)
    return jsonify(watch.to_dict())

@app.route('/api/watches/<int:watch_id>', methods=['PATCH'])
def update_watch(watch_id):
    """Update a watch (rating, status, notes)"""
    watch = Watch.query.get_or_404(watch_id)
    data = request.get_json()
    
    if 'user_rating' in data:
        watch.user_rating = data['user_rating']
    
    if 'status' in data:
        watch.status = data['status']
    
    if 'user_notes' in data:
        watch.user_notes = data['user_notes']
    
    db.session.commit()
    
    return jsonify(watch.to_dict())

@app.route('/api/watches/<int:watch_id>/rate', methods=['POST'])
def rate_watch(watch_id):
    """Rate a watch 1-5 stars"""
    watch = Watch.query.get_or_404(watch_id)
    data = request.get_json()
    rating = data.get('rating')
    
    if not rating or not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be 1-5'}), 400
    
    watch.user_rating = rating
    db.session.commit()
    
    return jsonify(watch.to_dict())

@app.route('/api/watches/<int:watch_id>/sold', methods=['POST'])
def mark_watch_sold(watch_id):
    """Mark a watch as sold"""
    watch = Watch.query.get_or_404(watch_id)
    watch.status = 'sold'
    db.session.commit()
    
    return jsonify(watch.to_dict())

# Search Sources Endpoints
@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get all search sources with last search time"""
    sources = SearchSource.query.filter_by(is_active=True).all()
    return jsonify([source.to_dict() for source in sources])

# Stats Endpoint
@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    total_watches = Watch.query.count()
    active_watches = Watch.query.filter(Watch.status != 'sold').count()
    blue_dials = Watch.query.filter_by(dial_color='blue').count()
    gold_cases = Watch.query.filter(
        Watch.case_type.ilike('%gold%') | Watch.case_type.ilike('%two-tone%')
    ).count()
    seventies = Watch.query.filter(Watch.year.between(1970, 1979)).count()
    
    return jsonify({
        'total_watches': total_watches,
        'active_watches': active_watches,
        'blue_dials': blue_dials,
        'gold_cases': gold_cases,
        'seventies_era': seventies,
        'last_updated': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
