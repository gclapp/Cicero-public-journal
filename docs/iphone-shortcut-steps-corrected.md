# Corrected iPhone Steps Shortcut (Option 2 - 14 Day Batch)

## Shortcut Configuration

### Trigger
- **Time of Day:** 9:00 PM
- **Repeat:** Daily

### Action 1: Find Health Samples
- **Category:** Steps
- **Start Date:** In the last 14 days
- **Group By:** Day
- **Fill Missing:** Off
- **Sort By:** Start Date
- **Order:** Oldest First

### Action 2: Repeat with Each
- **Input:** Health Samples

**Inside the loop:**

1. **Format Date**
   - **Date:** Start Date (from Repeat Item)
   - **Format:** Custom: yyyy-MM-dd
   - **Result:** DateString

2. **Get Numbers from Input**
   - **Input:** Quantity (from Repeat Item)
   - **Result:** StepCount

3. **Text**
   - **Content:** `{{DateString}}:{{StepCount}}`
   - **Result:** DayLine

4. **Add to Variable**
   - **Variable:** AllLines
   - **Content:** DayLine
   - **Separator:** New Lines

### Action 3: Send Email
- **To:** [REDACTED]
- **Subject:** Steps {{CurrentDate}}
- **Body:**
  ```
  Steps Export - {{CurrentDate}}
  
  {{AllLines}}
  ```

## Expected Email Format

```
Steps Export - Sunday, May 10, 2026

2026-04-26:11510
2026-04-27:6783
2026-04-28:6752
2026-04-29:4574
2026-04-30:7212
2026-05-01:20457
2026-05-02:32544
2026-05-03:36521
2026-05-04:18429
2026-05-05:19306
2026-05-06:7584
2026-05-07:16069
2026-05-08:18016
2026-05-09:8145
```

## Key Fixes

| Issue | Fix |
|-------|-----|
| Wrong step counts | Use explicit date:count format in email body |
| Filenames as data | Use email body text instead of attachments |
| Unclear ordering | Sort by Start Date, Oldest First |
| Fill Missing creating fake data | Turn Fill Missing OFF |
| Timezone confusion | Use yyyy-MM-dd format (no time component) |
