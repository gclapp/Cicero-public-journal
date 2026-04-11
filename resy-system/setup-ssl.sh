#!/bin/bash
# SSL Setup Script for nyceats.openclapp.com
# Run this after DNS is configured

echo "Setting up SSL for nyceats.openclapp.com..."

# Check if DNS is configured
echo "Checking DNS..."
if ! nslookup nyceats.openclapp.com > /dev/null 2>&1; then
    echo "❌ DNS not found for nyceats.openclapp.com"
    echo ""
    echo "Please add this DNS record first:"
    echo "  Type: A"
    echo "  Name: nyceats"
    echo "  Value: 3.141.39.228"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ DNS found"

# Get SSL certificate
echo "Obtaining SSL certificate..."
sudo certbot --nginx -d nyceats.openclapp.com --non-interactive --agree-tos --email [REDACTED]

# Test renewal
echo "Testing certificate renewal..."
sudo certbot renew --dry-run

echo ""
echo "✅ SSL setup complete!"
echo "Your site is now available at: https://nyceats.openclapp.com"
