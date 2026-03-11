# Email Authorization System

## Overview
Dynamic authorization system for [REDACTED] inbox. Only authorized senders receive replies; unauthorized senders trigger security alerts to Geoff.

## Current Authorized Senders
- [REDACTED]
- geoffrey.clapp@progyny.com
- keers003@gmail.com (Grace — highest priority)

## How Authorization Works

### For Unauthorized Senders
1. Email arrives from unauthorized address
2. Email is logged but NOT replied to
3. 🚨 **Security alert sent to Geoff** (both personal + work email)
4. Alert includes instructions to authorize the sender

### To Authorize a New Sender
1. Geoff receives security alert with unauthorized email details
2. Geoff replies with: `Authorize email@example.com`
3. System automatically adds sender to authorized list
4. Confirmation sent to Geoff
5. New sender can now email and receive replies

## Security Features
- Only Geoff ([REDACTED] or geoffrey.clapp@progyny.com) can authorize senders
- Authorization commands are logged with timestamp and who authorized
- All unauthorized emails are logged for weekly security reports
- Grace emails trigger immediate high-priority alerts

## Files
- `scripts/imap_email_reader.py` — Main email processing script
- `config/authorized-senders.json` — Dynamic authorized senders list
- `data/processed-emails.json` — Tracks processed email IDs
- `logs/imap-cron.log` — Execution logs

## Schedule
- Runs every 15 minutes via cron
- Polls [REDACTED] inbox via IMAP
- Processes new unread emails only

## Email Types Handled
1. **Watch alerts** — Forwards from Chrono24, Bob's Watches, etc.
2. **Flight confirmations/cancellations** — Delta emails
3. **Calendar event requests** — Create events from email
4. **Authorization commands** — Add new authorized senders
5. **General replies** — Contextual responses to authorized senders

## Alert Recipients
All security alerts and notifications go to:
- [REDACTED]
- geoffrey.clapp@progyny.com
