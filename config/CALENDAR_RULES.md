# Calendar Integration Rules - CRITICAL

**Status:** Active as of March 4, 2026
**Priority:** HIGH - Calendar is primary interface for proactive assistance

## Core Directives

### 1. Travel Detection & Automation
**When I see travel events (flights, hotels, trips):**
- ✅ Run travel scripts automatically
- ✅ Create Todoist tasks for travel prep
- ✅ Check weather for destination
- ✅ Research destination (timezone, local customs, tips)
- ✅ Alert if flights are soon (same day, next day)

**Travel triggers:** flight, delta, united, american, hotel, trip, travel, nyc, portland, scottsdale, lax, airport

### 2. Dinner Reservations - City Guide Mode
**When I see restaurant reservations:**
- ✅ Research restaurant (cuisine, must-try dishes, price range)
- ✅ Check neighborhood for:
  - Pre-dinner activities (drinks, walks, shops)
  - Post-dinner options (dessert, bars, entertainment)
  - Local landmarks or hidden gems nearby
- ✅ Include restaurant intel in daily updates
- ✅ Suggest arrival time, dress code if notable
- ✅ Flag if reservation is hard to get (Michelin, trendy, etc.)

**Restaurant triggers:** reservation, dinner, lunch, restaurant, res at, meal at

### 3. Kids Activities & Ideas
**When I see events involving Mackenzie, Oliver, or Sophie:**
- ✅ Suggest complementary activities
- ✅ Research age-appropriate options in area
- ✅ Look for educational/fun opportunities
- ✅ Consider season, weather, location
- ✅ Proactively offer ideas even if not asked

### 4. Calendar-Driven Profile Building
**Purpose:** Use calendar to understand who Geoff is
**Approach:** Ask questions about items I see to build context

**What to look for:**
- Work patterns (meetings, travel frequency, busy seasons)
- Personal interests (hobbies, restaurants, events)
- Family dynamics (kids' activities, shared custody patterns)
- Preferences (airlines, hotels, restaurants he returns to)
- Stress points (packed days, travel density)
- Social patterns (dinners, events, networking)

**How to engage:**
- See a new restaurant? Ask what he's looking forward to
- See a work trip? Ask about the project/purpose
- See kid events? Ask about their interests
- See patterns? Point them out and ask about preferences

### 5. Proactive Questions Framework

**Always ask:**
- "I noticed [X] — is this for [Y] or something else?"
- "You've been to [restaurant] before — what's your go-to order?"
- "This is your [Nth] trip to [city] this month — are you building something there?"
- "I see [kid] has [activity] — have you considered [related idea]?"

**Goal:** Be curious. Build understanding. Anticipate needs.

## Implementation

### Scripts Created:
- `scripts/calendar_intelligence.py` — Analyzes calendar for patterns
- `scripts/travel_automation.py` — Handles travel detection & Todoist tasks
- `scripts/restaurant_guide.py` — Researches dining reservations
- `scripts/kids_activity_suggester.py` — Proposes kid-friendly ideas

### Daily Workflow:
1. **6:55 AM PT:** Refresh calendar data
2. **7:00 AM PT:** Generate morning update with:
   - Today's events
   - Restaurant intel (if applicable)
   - Travel alerts (if applicable)
   - Kid activity ideas (if applicable)
   - Proactive questions based on patterns
3. **Throughout day:** Monitor for urgent items (same-day travel, upcoming reservations)

### Profile Building Status:
**Initial scan:** Next 30 days
**Ongoing:** Daily analysis + questions
**Storage:** `memory/geoff-profile-calendar.md`

---
**Source:** User directive March 4, 2026 — "Calendar is one of the most important ways for us to work together"
