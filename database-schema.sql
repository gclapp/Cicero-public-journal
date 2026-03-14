-- Database Schema for Cicero Private Server
-- Run: psql -U cicero -d cicero_db -f schema.sql

-- Users table (for authentication)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'America/Los_Angeles',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watch Searches
CREATE TABLE watch_searches (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    model_numbers TEXT[], -- Array of model numbers
    year_min INTEGER,
    year_max INTEGER,
    dial_colors TEXT[], -- Array of preferred dial colors
    case_materials TEXT[], -- Array of case materials
    sources TEXT[], -- Array of sources to search
    status VARCHAR(50) DEFAULT 'active', -- active, paused, completed
    schedule VARCHAR(50) DEFAULT 'daily', -- daily, twice_daily, weekly
    last_run TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Watches (listings found)
CREATE TABLE watches (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES watch_searches(id) ON DELETE CASCADE,
    reference VARCHAR(50) NOT NULL,
    year INTEGER,
    dial_color VARCHAR(50),
    dial_type VARCHAR(100),
    case_type VARCHAR(100),
    size VARCHAR(20),
    bracelet VARCHAR(50),
    price DECIMAL(10, 2),
    currency VARCHAR(3) DEFAULT 'USD',
    source VARCHAR(100) NOT NULL,
    source_url TEXT NOT NULL,
    image_url TEXT,
    local_image_path TEXT,
    status VARCHAR(50) DEFAULT 'pending_review', -- pending_review, liked, passed, sold
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_notes TEXT,
    date_added DATE DEFAULT CURRENT_DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, source_url) -- Prevent duplicates
);

-- Search Sources (for footer display)
CREATE TABLE search_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    url VARCHAR(255) NOT NULL,
    logo_url VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    last_search TIMESTAMP,
    watches_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search Logs (track when searches run)
CREATE TABLE search_logs (
    id SERIAL PRIMARY KEY,
    search_id INTEGER REFERENCES watch_searches(id) ON DELETE CASCADE,
    source VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL, -- success, error, partial
    watches_found INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- User Preferences
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    favorite_dials TEXT[],
    acceptable_dials TEXT[],
    avoid_dials TEXT[],
    preferred_case VARCHAR(100),
    preferred_size VARCHAR(20),
    sigma_dial_preferred BOOLEAN DEFAULT false,
    target_year INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Indexes for performance
CREATE INDEX idx_watches_search_id ON watches(search_id);
CREATE INDEX idx_watches_status ON watches(status);
CREATE INDEX idx_watches_source ON watches(source);
CREATE INDEX idx_watches_date_added ON watches(date_added);
CREATE INDEX idx_watches_user_rating ON watches(user_rating);
CREATE INDEX idx_search_logs_search_id ON search_logs(search_id);
CREATE INDEX idx_search_logs_completed_at ON search_logs(completed_at);

-- Insert default search sources
INSERT INTO search_sources (name, url, logo_url, is_active) VALUES
    ('Chrono24', 'https://www.chrono24.com', 'https://www.chrono24.com/favicon.ico', true),
    ('eBay', 'https://www.ebay.com', 'https://www.ebay.com/favicon.ico', true),
    ('Bob''s Watches', 'https://www.bobswatches.com', 'https://www.bobswatches.com/favicon.ico', true),
    ('Bulang & Sons', 'https://bulangandsons.com', 'https://bulangandsons.com/favicon.ico', true),
    ('Bezel', 'https://www.getbezel.com', 'https://www.getbezel.com/favicon.ico', true),
    ('Crown & Caliber', 'https://www.crownandcaliber.com', 'https://www.crownandcaliber.com/favicon.ico', true),
    ('Watches of Espionage', 'https://watchesofespionage.com', 'https://watchesofespionage.com/favicon.ico', true),
    ('WatchRecon', 'https://www.watchrecon.com', 'https://www.watchrecon.com/favicon.ico', true);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watch_searches_updated_at BEFORE UPDATE ON watch_searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_watches_updated_at BEFORE UPDATE ON watches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
