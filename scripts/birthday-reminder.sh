#!/bin/bash
# Birthday reminder script - triggers notifications via OpenClaw

PERSON="$1"
REMINDER_TYPE="$2"  # "gift" or "halfbirthday"
BIRTHDAY="$3"

if [ "$REMINDER_TYPE" == "gift" ]; then
    MESSAGE="🎁 Birthday gift reminder: $PERSON's birthday is on $BIRTHDAY (2 weeks away). Have you gotten a gift yet? Reply with what you got and I'll stop reminding you."
else
    MESSAGE="🎂 Half-birthday reminder: $PERSON's half-birthday is in 2 days ($BIRTHDAY). Time to plan something fun!"
fi

# Send via OpenClaw message tool
echo "$MESSAGE"
