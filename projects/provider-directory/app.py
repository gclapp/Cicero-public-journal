#!/usr/bin/env python3
"""Web application for viewing and interacting with provider data."""

from flask import Flask, render_template, jsonify, request
import sqlite3
import json
from pathlib import Path

app = Flask(__name__)

DB_PATH = Path(__file__).parent / "data" / "providers.db"


def get_db_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Main page with provider listing."""
    return render_template('index.html')


@app.route('/api/providers')
def get_providers():
    """API endpoint to get providers with filtering and pagination."""
    conn = get_db_connection()
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    state = request.args.get('state', '')
    city = request.args.get('city', '')
    search = request.args.get('search', '')
    
    # Build query
    where_clauses = ["source = 'healthgrades'"]
    params = []
    
    if state:
        where_clauses.append("state = ?")
        params.append(state)
    
    if city:
        where_clauses.append("city LIKE ?")
        params.append(f"%{city}%")
    
    if search:
        where_clauses.append("name LIKE ?")
        params.append(f"%{search}%")
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    count_sql = f"SELECT COUNT(*) FROM providers WHERE {where_sql}"
    total = conn.execute(count_sql, params).fetchone()[0]
    
    # Get providers
    offset = (page - 1) * per_page
    query = f"""
        SELECT name, credentials, specialties, street, city, state, zip, phone,
               accepting_new_patients, scraped_at
        FROM providers
        WHERE {where_sql}
        ORDER BY state, city, name
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    
    rows = conn.execute(query, params).fetchall()
    conn.close()
    
    providers = []
    for row in rows:
        providers.append({
            'name': row['name'],
            'credentials': row['credentials'],
            'specialties': json.loads(row['specialties']) if row['specialties'] else [],
            'street': row['street'],
            'city': row['city'],
            'state': row['state'],
            'zip': row['zip'],
            'phone': row['phone'],
            'accepting_new_patients': row['accepting_new_patients'],
            'scraped_at': row['scraped_at']
        })
    
    return jsonify({
        'providers': providers,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@app.route('/api/states')
def get_states():
    """Get list of states with provider counts."""
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT state, COUNT(*) as count
        FROM providers
        WHERE source = 'healthgrades' AND state IS NOT NULL AND state != ''
        GROUP BY state
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    
    return jsonify([{'state': row['state'], 'count': row['count']} for row in rows])


@app.route('/api/stats')
def get_stats():
    """Get database statistics."""
    conn = get_db_connection()
    
    total = conn.execute("SELECT COUNT(*) FROM providers WHERE source = 'healthgrades'").fetchone()[0]
    
    states = conn.execute("""
        SELECT COUNT(DISTINCT state) 
        FROM providers 
        WHERE source = 'healthgrades' AND state IS NOT NULL
    """).fetchone()[0]
    
    cities = conn.execute("""
        SELECT COUNT(DISTINCT city) 
        FROM providers 
        WHERE source = 'healthgrades' AND city IS NOT NULL
    """).fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_providers': total,
        'states': states,
        'cities': cities
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
