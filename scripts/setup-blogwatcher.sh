#!/bin/bash
# setup-blogwatcher.sh - Configure blogwatcher for competitor monitoring

# Competitors to monitor:
# - Maven (CEO: Kate Ryder)
# - Carrot
# - KindBody
# - WIN Fertility
# - Pomelo Health

echo "Setting up blogwatcher for competitive intelligence..."

# Note: Most companies don't have public RSS feeds for news
# We'll need to use alternative sources:
# 1. Company blogs (if they have RSS)
# 2. Google Alerts (via RSS)
# 3. News site searches
# 4. LinkedIn (if API available)

# For now, let's create a list of sources to monitor

cat << 'EOF'

## COMPETITOR RSS SOURCES TO MONITOR

### Maven
- URL: https://www.mavenclinic.com/blog (check for RSS)
- CEO: Kate Ryder (LinkedIn, Twitter)
- News: Google Alert "Maven Clinic funding"

### Carrot
- URL: https://www.carrotfertility.com/blog (check for RSS)
- News: Google Alert "Carrot Fertility"

### KindBody
- URL: https://www.kindbody.com/blog (check for RSS)
- News: Google Alert "KindBody fertility"

### WIN Fertility
- URL: https://www.winfertility.com/ (check for news section)
- News: Google Alert "WIN Fertility"

### Pomelo Health
- URL: https://www.pomelohealth.com/ (check for blog)
- News: Google Alert "Pomelo Health"

### General Healthcare/Fertility News
- Fierce Healthcare: https://www.fiercehealthcare.com/rss.xml
- Healthcare Dive: https://www.healthcaredive.com/feeds/news/
- MedCity News: https://medcitynews.com/feed/

EOF

echo ""
echo "To add RSS feeds:"
echo "  openclaw blogwatcher subscribe <rss-url>"
echo ""
echo "To check all feeds:"
echo "  openclaw blogwatcher watch"
echo ""
echo "Next steps:"
echo "1. Find RSS feeds for each competitor's blog"
echo "2. Set up Google Alerts with RSS output"
echo "3. Add feeds to blogwatcher"
echo "4. Schedule daily checks"
