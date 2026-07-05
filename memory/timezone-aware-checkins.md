# Timezone-Aware Check-In System
## Implementation: March 3, 2026

---

## DECISION: OPTION A - LOCAL TIME FOLLOWING

**Rule:** All check-ins follow Geoff's local time, wherever he is.

**How It Works:**
- Geoff sees: "7 AM morning check-in"
- System calculates: 7 AM local time → UTC time to send
- Result: Check-in arrives at 7 AM local, always

**Geoff never converts. I handle all math.**

---

## STANDARD CHECK-IN SCHEDULE

| Check-In | Local Time | Timezone Dependent |
|----------|-----------|-------------------|
| Morning | 7:00 AM | Yes - always 7 AM local |
| Midday | 12:30 PM | Yes - always 12:30 PM local |
| Afternoon | 4:30 PM | Yes - always 4:30 PM local |
| Evening | 8:30 PM | Yes - always 8:30 PM local |

---

## TIMEZONE CONVERSION TABLE

### Pacific Time (PT) - UTC - 8
| Local | UTC | Notes |
|-------|-----|-------|
| 7:00 AM PT | 3:00 PM UTC | Previous day |
| 12:30 PM PT | 8:30 PM UTC | Previous day |
| 4:30 PM PT | 12:30 AM UTC | Same day |
| 8:30 PM PT | 4:30 AM UTC | Next day |

### Eastern Time (ET) - UTC - 5
| Local | UTC | Notes |
|-------|-----|-------|
| 7:00 AM ET | 12:00 PM UTC | Same day |
| 12:30 PM ET | 5:30 PM UTC | Same day |
| 4:30 PM ET | 9:30 PM UTC | Same day |
| 8:30 PM ET | 1:30 AM UTC | Next day |

### Mountain Time (MT) - UTC - 7
| Local | UTC | Notes |
|-------|-----|-------|
| 7:00 AM MT | 2:00 PM UTC | Previous day |
| 12:30 PM MT | 7:30 PM UTC | Previous day |
| 4:30 PM MT | 11:30 PM UTC | Same day |
| 8:30 PM MT | 3:30 AM UTC | Next day |

### Central Time (CT) - UTC - 6
| Local | UTC | Notes |
|-------|-----|-------|
| 7:00 AM CT | 1:00 PM UTC | Previous day |
| 12:30 PM CT | 6:30 PM UTC | Previous day |
| 4:30 PM CT | 10:30 PM UTC | Same day |
| 8:30 PM CT | 2:30 AM UTC | Next day |

---

## ACTIVE TIMEZONE TRACKING

**Current Location:** Los Angeles, CA  
**Current Timezone:** Pacific (PT)  
**UTC Offset:** -8 hours  
**Effective Until:** March 9, 2026, 5:25 PM PT

**Next Location:** Atlanta, GA  
**Next Timezone:** Eastern (ET)  
**UTC Offset:** -5 hours  
**Effective From:** March 10, 2026, 12:30 AM ET  
**Effective Until:** March 10, 2026, evening (return flight)

**Return Location:** Los Angeles, CA  
**Return Timezone:** Pacific (PT)  
**UTC Offset:** -8 hours  
**Effective From:** March 11, 2026

---

## MARCH 9-10 ATLANTA TRIP: CHECK-IN SCHEDULE

### Monday, March 9 (Pacific Time)
- **7:00 AM PT** ← Morning check-in (3:00 PM UTC March 9)
- **12:30 PM PT** ← Midday check-in (8:30 PM UTC March 9)
- **4:30 PM PT** ← Afternoon check-in (12:30 AM UTC March 10)
- **5:25 PM PT** ← DEPART LAX
- **SKIP 8:30 PM** ← In flight

### Tuesday, March 10 (Eastern Time)
- **12:30 AM ET** ← Arrive ATL (9:30 PM PT March 9)
- **7:00 AM ET** ← Morning check-in (12:00 PM UTC March 10) ⭐ TIMEZONE SWITCH
- **12:30 PM ET** ← Midday check-in (5:30 PM UTC March 10)
- **4:30 PM ET** ← Afternoon check-in (9:30 PM UTC March 10)
- **8:30 PM ET** ← Evening check-in (1:30 AM UTC March 11)
- **Evening** ← Return flight to LA

### Wednesday, March 11 (Pacific Time)
- Resume normal PT schedule
- 7:00 AM PT check-in (3:00 PM UTC March 11)

---

## IMPLEMENTATION NOTES

### For System (Cicero)

**Before each check-in:**
1. Read current location from memory
2. Determine timezone from location
3. Calculate UTC time for local check-in time
4. Send at correct UTC time
5. Reference local time in message ("Good morning - 7 AM PT")

**Example Code Logic:**
```python
location = get_geoff_location()  # "Los Angeles, CA"
timezone = get_timezone(location)  # "America/Los_Angeles" (PT)
local_time = "7:00 AM"
utc_time = convert_to_utc(local_time, timezone)  # Calculate

schedule_check_in(utc_time, message="Good morning! 7 AM PT check-in")
```

### For User (Geoff)

**You see:**
- "7 AM morning check-in"
- "12:30 PM midday check-in"
- "4:30 PM afternoon check-in"
- "8:30 PM evening check-in"

**Always in your local time. No math required.**

---

## EDGE CASES

### Travel Days
**Problem:** What about days when crossing timezones?

**Solution:**
- Pre-travel check-ins: Use departure timezone
- Post-arrival check-ins: Use arrival timezone
- In-flight: Skip non-urgent check-ins

**March 9 Example:**
- Morning/Midday/Afternoon: PT (LA)
- Evening: SKIP (in flight)

**March 10 Example:**
- Morning/Midday/Afternoon/Evening: ET (Atlanta)

### Very Short Trips
**Problem:** Same-day trips (2-3 hours)

**Solution:**
- Keep home timezone (don't switch for short trips)
- Or skip check-ins during travel

### International Travel
**Problem:** Larger timezone differences (Europe, Asia)

**Solution:**
- Same system applies (local time following)
- Just larger UTC offset
- May require overnight scheduling (I send at 2 AM UTC = 10 AM local)

---

## TESTING THE SYSTEM

### Test 1: March 10 (Atlanta - ET)
**Expected:**
- Morning check-in arrives at 7:00 AM ET
- Geoff sees: "7 AM ET - Good morning!"
- System sent at: 12:00 PM UTC

### Test 2: March 11 (Back in LA - PT)
**Expected:**
- Morning check-in arrives at 7:00 AM PT
- Geoff sees: "7 AM PT - Good morning!"
- System sent at: 3:00 PM UTC (previous day)

### Success Criteria
- ✅ Check-ins arrive at correct local time
- ✅ Timezone referenced in message ("7 AM ET")
- ✅ No confusion about timing
- ✅ Seamless experience for Geoff

---

## MAINTENANCE

**Weekly:**
- Review upcoming travel in calendar
- Update location/timezone tracking
- Adjust check-in UTC times as needed

**Daily:**
- Before first check-in: Confirm location
- If uncertain: Ask Geoff "What timezone are you in?"
- Document any changes

---

## BACKUP PLAN

**If system fails:**
- Default to Pacific Time (home base)
- Tell Geoff: "Check-ins in PT - convert as needed"
- Fix system before next timezone change

**If uncertain:**
- Ask: "What timezone are you in today?"
- Geoff already approved asking when needed

---

## STATUS

**System:** ACTIVE  
**Current Timezone:** Pacific (PT)  
**Next Timezone Change:** March 10, 2026 (Eastern)  
**Test Case:** Atlanta trip (1 day in ET)  
**Decision:** Option A - Local time following ✓

---

**Goal:** Geoff never thinks about timezones. Check-ins just arrive at the right local time, always.

**Implementation Date:** March 3, 2026  
**First Test:** March 10, 2026 (Atlanta - ET)
