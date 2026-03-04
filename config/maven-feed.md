# Maven Competitive Intelligence Feed

## Feed Configuration
- **Source:** Google Alerts
- **Feed URL:** https://www.google.com/alerts/feeds/13519883000496020413/8201260240037632355
- **Target:** Maven (competitor monitoring)
- **Added:** March 3, 2026
- **Status:** Pending blogwatcher setup

## Setup Required
Blogwatcher needs Go installed to build the binary for ARM64 architecture.

### Option 1: Install Go + Blogwatcher
```bash
# Install Go for ARM64
wget https://go.dev/dl/go1.21.0.linux-arm64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-arm64.tar.gz
export PATH=$PATH:/usr/local/go/bin

# Install blogwatcher
go install github.com/Hyaxia/blogwatcher/cmd/blogwatcher@latest
```

### Option 2: Python RSS Monitor (Alternative)
Create a simple Python script to poll the feed and notify on new items.

## Next Steps
- [ ] Install Go or set up Python RSS monitor
- [ ] Add feed to blogwatcher
- [ ] Set up scan schedule (daily)
- [ ] Integrate with competitive intel email reports
