# FlightAware AeroAPI Setup Guide

This guide explains how to obtain and configure your FlightAware AeroAPI key for use with the Aero flight tracking system.

## Overview

FlightAware AeroAPI v4 is a RESTful API that provides:
- Real-time flight tracking
- Airport arrivals and departures
- Flight status and position data
- Historical flight information
- Airport delays and disruptions

## Getting an API Key

### Step 1: Create a FlightAware Account

1. Visit [FlightAware](https://flightaware.com/)
2. Click "Sign Up" in the top right corner
3. Complete the registration form
4. Verify your email address

### Step 2: Request AeroAPI Access

1. Log in to your FlightAware account
2. Navigate to [AeroAPI Commercial Services](https://www.flightaware.com/commercial/aeroapi)
3. Click "Get Started" or "Contact Sales"
4. Complete the API access request form with:
   - Your use case
   - Expected request volume
   - Application details

### Step 3: Generate API Key

Once approved:

1. Go to [AeroAPI Portal](https://www.flightaware.com/aeroapi/portal)
2. Navigate to "API Keys" or "Credentials"
3. Click "Generate New Key"
4. Copy your API key (store it securely!)

**Important:** Keep your API key confidential. Treat it like a password.

## Configuration

### Option 1: Environment Variable (Recommended)

Set the `AEROAPI_KEY` environment variable:

```bash
# Linux/macOS
export AEROAPI_KEY="your_api_key_here"

# Windows (Command Prompt)
set AEROAPI_KEY=your_api_key_here

# Windows (PowerShell)
$env:AEROAPI_KEY="your_api_key_here"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export AEROAPI_KEY="your_api_key_here"' >> ~/.bashrc
```

### Option 2: Config File

Create a config file at `~/.aero/config.json`:

```bash
mkdir -p ~/.aero
cat > ~/.aero/config.json << 'EOF'
{
  "api_key": "your_api_key_here"
}
EOF
chmod 600 ~/.aero/config.json
```

### Option 3: Direct Parameter

Pass the API key directly when creating the tracker:

```python
from aero import AeroTracker

tracker = AeroTracker(api_key="your_api_key_here")
```

### Option 4: Custom Config Path

Use a custom config file location:

```python
from aero import AeroTracker

tracker = AeroTracker(config_path="/path/to/config.json")
```

## API Key Security Best Practices

1. **Never commit API keys to version control**
   - Add config files to `.gitignore`
   - Use environment variables in production

2. **Restrict API key usage**
   - Use separate keys for development and production
   - Monitor API usage in the FlightAware portal

3. **Rotate keys regularly**
   - Generate new keys periodically
   - Revoke old keys when no longer needed

4. **Use appropriate permissions**
   - Only request the endpoints you need
   - Follow principle of least privilege

## Rate Limits

FlightAware AeroAPI has rate limits based on your plan:

| Plan | Requests/Minute | Requests/Hour | Requests/Day |
|------|----------------|---------------|--------------|
| Free Trial | 10 | 100 | 500 |
| Basic | 60 | 1,000 | 10,000 |
| Professional | 300 | 5,000 | 50,000 |
| Enterprise | Custom | Custom | Custom |

The Aero client includes built-in rate limiting to help stay within these limits.

## Pricing

FlightAware offers several pricing tiers:

- **Free Trial**: Limited access for testing
- **Basic**: Starting at ~$100/month
- **Professional**: Starting at ~$500/month
- **Enterprise**: Custom pricing

Visit [FlightAware Pricing](https://www.flightaware.com/commercial/aeroapi/pricing) for current rates.

## Testing Your API Key

Verify your API key is working:

```python
from aero import AeroTracker

try:
    with AeroTracker() as tracker:
        # Try to get airport info
        info = tracker.client.get_airport_info("KJFK")
        print(f"✓ API key is valid!")
        print(f"Airport: {info.get('name')}")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Troubleshooting

### Authentication Error (401)

- Verify your API key is correct
- Check that the key is active in the FlightAware portal
- Ensure the key has access to AeroAPI v4

### Rate Limit Error (429)

- You've exceeded your plan's rate limits
- Wait before making more requests
- Consider upgrading your plan

### Not Found Error (404)

- Flight or airport code doesn't exist
- Check the spelling of flight numbers and airport codes
- Use ICAO codes (4 letters) for best results

### Connection Errors

- Check your internet connection
- Verify FlightAware API is operational
- Check [FlightAware Status](https://status.flightaware.com/)

## API Endpoints Reference

### Flight Tracking
- `GET /flights` - Search flights
- `GET /flights/{id}` - Get flight details
- `GET /flights/{id}/position` - Get flight position

### Airport Operations
- `GET /airports/{code}` - Get airport info
- `GET /airports/{code}/flights/arrivals` - Get arrivals
- `GET /airports/{code}/flights/departures` - Get departures
- `GET /airports/{code}/delays` - Get airport delays

### Alerts (if enabled)
- `POST /alerts` - Create flight alert
- `GET /alerts` - List alerts
- `DELETE /alerts/{id}` - Delete alert

## Support

- [AeroAPI Documentation](https://www.flightaware.com/aeroapi/portal/documentation)
- [FlightAware Support](https://www.flightaware.com/commercial/support/)
- [FlightAware Discussions](https://discussions.flightaware.com/)

## Next Steps

Once your API key is configured, see `USAGE.md` for examples of how to use the Aero tracking system.
