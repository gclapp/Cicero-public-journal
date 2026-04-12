#!/bin/bash

# Spawn 6 sub-agents for the NYCeats Resy system improvements

WORKSPACE="/home/ubuntu/.openclaw/workspace/resy-system"

# Task 1: Add more space around the "add a restaurant" div
openclaw sessions spawn --runtime=subagent --label="task-1-spacing" --prompt="""
You are a sub-agent working on Task 1 for the NYCeats Resy reservation system.

TASK: Add more space around the 'add a restaurant' div (too close to '4 restaurants' indicator)

FILE TO EDIT: templates/index.html

DETAILS:
- In the header-actions section, there's a span showing the restaurant count (e.g., '4 restaurants')
- The 'Add Restaurant' button is too close to this indicator
- Add appropriate margin/padding to create more visual separation

The relevant HTML is in the header-actions div near the top of the content block.

STEPS:
1. Read templates/index.html
2. Find the header-actions div
3. Add CSS styling to create more space between the restaurant count and the Add Restaurant button
4. Save the file
5. Update TASK_STATUS.json to mark task 1 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

# Task 2: Filter out existing restaurants from search results
openclaw sessions spawn --runtime=subagent --label="task-2-filter-existing" --prompt="""
You are a sub-agent working on Task 2 for the NYCeats Resy reservation system.

TASK: When searching by food type like 'Greek', don't show items already in the list

FILE TO EDIT: app.py

DETAILS:
- The /api/resy/search endpoint searches for restaurants
- Currently it returns all matching results, even if they're already in the user's list
- Need to filter out restaurants that are already added to the user's list
- The user's restaurants are stored and accessible

STEPS:
1. Read app.py and find the /api/resy/search route
2. Understand how restaurant data is stored and accessed
3. Modify the search function to filter out venue_ids that already exist in the user's restaurant list
4. Save the file
5. Update TASK_STATUS.json to mark task 2 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

# Task 3: Increase search results from 10 to 20
openclaw sessions spawn --runtime=subagent --label="task-3-search-limit" --prompt="""
You are a sub-agent working on Task 3 for the NYCeats Resy reservation system.

TASK: When searching by food type, show up to 20 options (not 10)

FILE TO EDIT: app.py

DETAILS:
- The /api/resy/search endpoint currently limits results to 10
- Need to increase this limit to 20 options
- This is likely a per_page or limit parameter in the API call or result slicing

STEPS:
1. Read app.py and find the /api/resy/search route
2. Find where the limit of 10 is set (look for per_page, limit, or array slicing [:10])
3. Change the limit from 10 to 20
4. Save the file
5. Update TASK_STATUS.json to mark task 3 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

# Task 4: Change 'Logs' to 'Processing' in header
openclaw sessions spawn --runtime=subagent --label="task-4-rename-logs" --prompt="""
You are a sub-agent working on Task 4 for the NYCeats Resy reservation system.

TASK: Change 'Logs' to 'Processing' in the header

FILE TO EDIT: templates/base.html

DETAILS:
- The navigation header has a link labeled 'Logs'
- This should be renamed to 'Processing'
- The link points to the logs_page endpoint

STEPS:
1. Read templates/base.html
2. Find the navigation link that says 'Logs'
3. Change the text from 'Logs' to 'Processing'
4. Save the file
5. Update TASK_STATUS.json to mark task 4 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

# Task 5: Add calendar/trip processing logs
openclaw sessions spawn --runtime=subagent --label="task-5-processing-logs" --prompt="""
You are a sub-agent working on Task 5 for the NYCeats Resy reservation system.

TASK: Add calendar/trip processing logs showing wake-up, check, and completion (even when no action needed)

FILE TO EDIT: calendar_scanner.py

DETAILS:
- The calendar scanner wakes up and checks for trips
- Currently it only logs when actions are taken
- Need to add logging for:
  1. When the scanner wakes up
  2. When it checks for trips (with result - found or not found)
  3. When processing completes (even if no action was needed)
- Use the existing log_scan function from monitoring module

STEPS:
1. Read calendar_scanner.py to understand the scan flow
2. Find where the main scan/process function starts
3. Add log_scan calls at key points:
   - At the start (wake-up)
   - After checking for trips (with count of trips found)
   - At completion (with summary of what was done)
4. Save the file
5. Update TASK_STATUS.json to mark task 5 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

# Task 6: Add random delay between reservation attempts
openclaw sessions spawn --runtime=subagent --label="task-6-random-delay" --prompt="""
You are a sub-agent working on Task 6 for the NYCeats Resy reservation system.

TASK: Add random delay (33-105 seconds) between reservation attempts to avoid API spam detection

FILE TO EDIT: calendar_scanner.py

DETAILS:
- The scanner attempts to book reservations for multiple restaurants
- Currently it may make requests too quickly in succession
- Need to add a random delay between attempts
- Delay should be between 33 and 105 seconds
- Use Python's random module and time.sleep()

STEPS:
1. Read calendar_scanner.py to understand the reservation attempt flow
2. Find where reservation attempts are made (likely in a loop)
3. Import random module if not already imported
4. Add time.sleep(random.randint(33, 105)) between attempts
5. Save the file
6. Update TASK_STATUS.json to mark task 6 as COMPLETE

WORKSPACE: /home/ubuntu/.openclaw/workspace/resy-system
""" &

echo "All 6 sub-agents spawned!"
