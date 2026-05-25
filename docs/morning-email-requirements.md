# Morning Email Requirements

**Last Updated:** May 25, 2026

## Email Structure (in order)

1. **Location Bar** (compact, single row)
   - 📍 Location | 🕐 Time | 🌡️ Temp | 💧 Humidity | 💨 Wind
   - Smart detection: Uses flight times to determine actual location
   - If flight hasn't departed → at origin
   - If flight has departed → at destination

2. **Today's Schedule**
   - Calendar events for today
   - Travel events highlighted
   - Restaurant events highlighted

3. **Today's Priorities (Todoist)**
   - Tasks due TODAY only
   - Tasks due TOMORROW only
   - Sorted by: Day first, then by priority (P1, P2, P3, P4)
   - Show ALL tasks (not limited to 10-15)
   - Each task is clickable link to Todoist
   - Format: https://app.todoist.com/app/task/{task_id}
   - Group by: Today section, Tomorrow section
   - No project grouping

4. **7-Day Calendar View**
   - Table format: Day | Events
   - Today highlighted
   - Travel events marked with ✈️
   - Show times for events

5. **Upcoming Travel**
   - Next 3 travel events
   - Flight details with dates

## Removed Sections
- ❌ Weight loss focus
- ❌ Questions for today
- ❌ Whoop health data (moved to Vitus emails)
- ❌ Large gradient location boxes

## Technical Requirements

### Location Detection Logic
- Check calendar for today's flights
- Parse flight time from event
- Compare to current time
- Flight TO LAX/LA: If not departed → at origin, else → LA
- Flight FROM LAX/LA: If not departed → LA, else → destination

### Todoist Integration
- Use existing `fetch_todoist_tasks.py` module
- Filter: (today | tomorrow)
- Sort: Priority descending (P1 first)
- Links: Use task IDs from Todoist

### Weather
- Current temp, humidity, wind
- No forecast section
- Compact inline display

## Testing Checklist
Before claiming done:
- [ ] Email sends successfully
- [ ] Location shows correctly based on flight times
- [ ] Todoist tasks appear (today + tomorrow)
- [ ] Tasks are sorted by priority
- [ ] All tasks shown (not truncated)
- [ ] Task links work
- [ ] 7-day calendar displays
- [ ] No duplicate sections
