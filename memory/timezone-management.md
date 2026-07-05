# Timezone Change Management System
## Handling Travel Across Time Zones

**Status:** System documentation + active scenario  
**Created:** March 3, 2026  
**Scenario:** Geoff traveling next week (1 day) - timezone change

---

## THE PROBLEM

**Current Setup:**
- Default: Pacific Time (UTC - 8)
- System check-ins: 4x daily at PT times
- All scheduling based on PT

**Travel Scenario:**
- Location change → Timezone change
- Check-in times become wrong
- Scheduling becomes confusing
- "4 PM check-in" means different things in different places

**Example:**
- Monday: Geoff in LA (PT) - 7 AM check-in = 7 AM local ✓
- Tuesday: Geoff in NYC (ET) - 7 AM check-in = 10 AM local ✗
- Wednesday: Back in LA (PT) - 7 AM check-in = 7 AM local ✓

---

## SOLUTION OPTIONS

### Option 1: Anchor to Geoff's Location (RECOMMENDED)
**How it works:**
- Check-ins follow Geoff's local time wherever he is
- System detects location/timezone change
- Adjusts all times automatically
- Example: "7 AM check-in" = 7 AM local time always

**Implementation:**
```
Geoff location: LA → PT → Check-in 7 AM PT
Geoff location: NYC → ET → Check-in 7 AM ET (was 10 AM PT)
Geoff location: London → GMT → Check-in 7 AM GMT (was 11 PM PT prior day)
```

**Pros:**
- Intuitive for Geoff (7 AM = 7 AM wherever he is)
- Follows natural body clock
- No mental math required

**Cons:**
- I need to know location to calculate check-in times
- Check-ins happen at different UTC times each day
- Harder for me to schedule if I don't know location

---

### Option 2: Anchor to Home Base (Pacific)
**How it works:**
- All check-ins stay at Pacific Time regardless of Geoff's location
- Geoff converts mentally when traveling
- Example: 7 AM PT check-in = 10 AM ET when in NYC

**Implementation:**
```
Check-in: 7 AM PT (always)
Geoff in LA: 7 AM local
Geoff in NYC: 10 AM local
Geoff in London: 3 PM local
```

**Pros:**
- Simple for me (always PT)
- Consistent scheduling
- Easy to automate

**Cons:**
- Geoff has to do mental math when traveling
- 7 AM check-in might be 10 PM in some timezones (inconvenient)
- Doesn't follow natural routine

---

### Option 3: Hybrid - Ask Each Time
**How it works:**
- Before any time-sensitive message: "What timezone are you in?"
- Adjust on the fly
- Document the answer

**Implementation:**
```
Me: "Morning check-in - what timezone are you in today?"
Geoff: "NYC, Eastern"
Me: [Adjusts all times to ET]
```

**Pros:**
- Always accurate
- No assumptions
- Geoff already said he's okay with me asking

**Cons:**
- Extra friction (have to ask every day when traveling)
- Delayed responses
- More conversational overhead

---

## RECOMMENDED APPROACH: Option 1 + Location Tracking

### System Design

**1. Location Tracking**
```yaml
Current Location: [City, State/Country]
Timezone: [TZ identifier]
UTC Offset: [+/- hours]
Until: [Date/Time when location changes]

Example:
  Current Location: Los Angeles, CA
  Timezone: America/Los_Angeles
  UTC Offset: -8 (PST)
  Until: March 8, 2026 11:59 PM
```

**2. Automatic Adjustment**
- Read location from memory
- Calculate check-in times in local timezone
- Send at correct local time
- Example: 7 AM local, whatever that is in UTC

**3. Travel Day Handling**
**Problem:** What about travel days when crossing timezones?

**Solution:**
```
Travel Day Protocol:
  Morning (pre-flight): Use departure timezone
  During travel: Pause non-urgent check-ins
  Evening (post-arrival): Use arrival timezone
  Next day: Full schedule in new timezone
```

**4. Calendar Integration (Future)**
- Read travel from calendar automatically
- Detect timezone changes
- Adjust without asking
- Alert Geoff: "I see you're in NYC - adjusting to ET"

---

## ACTIVE SCENARIO: Next Week's Trip

**Current Understanding:**
- **When:** Next week (Week of March 9)
- **Duration:** 1 day
- **Destination:** Unknown
- **Timezone change:** Yes (from PT to ???)

**Questions to Resolve:**
1. What day exactly? (March 9? March 10?)
2. Where are you going?
3. What timezone is that in?
4. Do you want check-ins to follow local time?

**Test Scenario Options:**

### Test A: March 9 Trip (Same Day Return)
```
March 9 Morning: LA (PT) - Morning check-in 7 AM PT
March 9 Travel: To ??? (timezone change)
March 9 Evening: Back in LA (PT) - Evening check-in 8 PM PT

Action: No timezone change needed (same day return)
```

### Test B: March 9-10 (Overnight)
```
March 9 Morning: LA (PT) - 7 AM check-in PT
March 9 Travel: To NYC (ET)
March 9 Evening: NYC (ET) - 8 PM check-in ET
March 10 Morning: NYC (ET) - 7 AM check-in ET
March 10 Travel: Back to LA

Action: Switch to ET for March 9 evening + March 10 morning
```

---

## IMPLEMENTATION PLAN

### Immediate (This Week)
1. **Geoff tells me:** Exact dates and destination
2. **I document:** Location and timezone
3. **We test:** Option 1 (local time following)
4. **I adjust:** Check-in schedule for travel days

### Short Term (Next Month)
1. **Build:** Location tracking in memory
2. **Automate:** Check-in time calculation based on location
3. **Document:** Travel day protocol

### Long Term (Future)
1. **Integrate:** Calendar API for automatic detection
2. **Smart defaults:** Common destinations (NYC = ET, SF = PT)
3. **Proactive alerts:** "I see you're traveling to ET - adjusting"

---

## DECISION NEEDED

**From Geoff:**
1. **Which option do you prefer?**
   - A: Check-ins follow local time (7 AM = 7 AM wherever you are)
   - B: Check-ins stay Pacific Time (you convert mentally)
   - C: I ask each time

2. **Next week's trip details:**
   - Exact dates?
   - Destination?
   - Overnight or same-day return?

3. **How do you want to communicate location changes?**
   - Tell me explicitly ("I'm in NYC now")
   - I'll read from calendar
   - I'll ask each morning

---

## EXAMPLE WORKFLOW (Option 1 - Local Time)

**Normal Week in LA:**
```
Monday 7 AM PT: Morning check-in
Monday 12:30 PM PT: Midday check-in
Monday 4:30 PM PT: Afternoon check-in
Monday 8:30 PM PT: Evening check-in
```

**Travel Week (LA → NYC):**
```
Sunday: Geoff tells me "Traveling to NYC Monday"
Monday 7 AM PT: Morning check-in (LA)
Monday 12 PM: Travel to NYC
Monday 8:30 PM ET: Evening check-in (NYC - was 5:30 PM PT)
Tuesday 7 AM ET: Morning check-in (NYC - was 4 AM PT)
Tuesday 12:30 PM ET: Midday check-in (NYC - was 9:30 AM PT)
Tuesday travel: Back to LA
Tuesday 8:30 PM PT: Evening check-in (LA)
```

**I handle all the math. Geoff just sees 7 AM local time.**

---

## DOCUMENTATION

**Files Updated:**
- `memory/timezone-management.md` (this file)
- `SOUL.md` - Added timezone handling as core truth
- `MEMORY.md` - Logged timezone fix

**Next Action:** Geoff confirms preference and provides trip details

---

**The Goal:** Seamless timezone management that follows Geoff, not the other way around.

**Status:** System designed, awaiting Geoff's preference and trip details.
