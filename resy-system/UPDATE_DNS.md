# Update DNS for Elastic IP

## New Elastic IP: 16.59.79.163

This IP will persist through instance stops/starts.

## GoDaddy DNS Update Required

Update your A record in GoDaddy:

| Record | Old Value | New Value |
|--------|-----------|-----------|
| nyceats.openclapp.com | 18.218.34.182 | **16.59.79.163** |

## After DNS Update

Run SSL setup:
```bash
cd /home/ubuntu/.openclaw/workspace/resy-system
./setup-ssl.sh
```

## Access URLs

| URL | Status |
|-----|--------|
| http://16.59.79.163 | ✅ Working now |
| http://nyceats.openclapp.com | ⏳ After DNS update |
| https://nyceats.openclapp.com | ⏳ After SSL setup |
