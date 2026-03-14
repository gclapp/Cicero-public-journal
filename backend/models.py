"""
Database Models for Cicero API
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100))
    timezone = db.Column(db.String(50), default='America/Los_Angeles')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    searches = db.relationship('WatchSearch', backref='user', lazy=True)
    preferences = db.relationship('UserPreference', backref='user', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'timezone': self.timezone,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class WatchSearch(db.Model):
    __tablename__ = 'watch_searches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    model_numbers = db.Column(db.ARRAY(db.String))
    year_min = db.Column(db.Integer)
    year_max = db.Column(db.Integer)
    dial_colors = db.Column(db.ARRAY(db.String))
    case_materials = db.Column(db.ARRAY(db.String))
    sources = db.Column(db.ARRAY(db.String))
    status = db.Column(db.String(50), default='active')
    schedule = db.Column(db.String(50), default='daily')
    last_run = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    watches = db.relationship('Watch', backref='search', lazy=True)
    logs = db.relationship('SearchLog', backref='search', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'modelNumbers': self.model_numbers,
            'years': {'min': self.year_min, 'max': self.year_max},
            'dialColors': self.dial_colors,
            'caseMaterials': self.case_materials,
            'sources': self.sources,
            'status': self.status,
            'schedule': self.schedule,
            'lastRun': self.last_run.isoformat() if self.last_run else None,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'watchesFound': len(self.watches)
        }

class Watch(db.Model):
    __tablename__ = 'watches'
    
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('watch_searches.id'), nullable=False)
    reference = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer)
    dial_color = db.Column(db.String(50))
    dial_type = db.Column(db.String(100))
    case_type = db.Column(db.String(100))
    size = db.Column(db.String(20))
    bracelet = db.Column(db.String(50))
    price = db.Column(db.Numeric(10, 2))
    currency = db.Column(db.String(3), default='USD')
    source = db.Column(db.String(100), nullable=False)
    source_url = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.Text)
    local_image_path = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending_review')
    user_rating = db.Column(db.Integer)
    user_notes = db.Column(db.Text)
    date_added = db.Column(db.Date, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'searchId': self.search_id,
            'reference': self.reference,
            'year': self.year,
            'dialColor': self.dial_color,
            'dialType': self.dial_type,
            'case': self.case_type,
            'size': self.size,
            'bracelet': self.bracelet,
            'price': str(self.price) if self.price else None,
            'source': self.source,
            'link': self.source_url,
            'imageUrl': self.image_url,
            'localImagePath': self.local_image_path,
            'status': self.status,
            'userRating': self.user_rating,
            'userNotes': self.user_notes,
            'dateAdded': self.date_added.isoformat() if self.date_added else None
        }

class SearchSource(db.Model):
    __tablename__ = 'search_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(255), nullable=False)
    logo_url = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    last_search = db.Column(db.DateTime)
    watches_found = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'name': self.name,
            'url': self.url,
            'logoUrl': self.logo_url,
            'isActive': self.is_active,
            'lastSearch': self.last_search.isoformat() if self.last_search else None,
            'watchesFound': self.watches_found
        }

class SearchLog(db.Model):
    __tablename__ = 'search_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('watch_searches.id'), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    watches_found = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'searchId': self.search_id,
            'source': self.source,
            'status': self.status,
            'watchesFound': self.watches_found,
            'startedAt': self.started_at.isoformat() if self.started_at else None,
            'completedAt': self.completed_at.isoformat() if self.completed_at else None
        }

class UserPreference(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    favorite_dials = db.Column(db.ARRAY(db.String))
    acceptable_dials = db.Column(db.ARRAY(db.String))
    avoid_dials = db.Column(db.ARRAY(db.String))
    preferred_case = db.Column(db.String(100))
    preferred_size = db.Column(db.String(20))
    sigma_dial_preferred = db.Column(db.Boolean, default=False)
    target_year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'favoriteDials': self.favorite_dials,
            'acceptableDials': self.acceptable_dials,
            'avoidDials': self.avoid_dials,
            'preferredCase': self.preferred_case,
            'preferredSize': self.preferred_size,
            'sigmaDialPreferred': self.sigma_dial_preferred,
            'targetYear': self.target_year
        }
