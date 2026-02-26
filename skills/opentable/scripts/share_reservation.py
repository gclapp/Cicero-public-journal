#!/usr/bin/env python3
"""
Share an OpenTable reservation via OpenTable, WhatsApp, SMS, or Email
Generates shareable content and sends via specified channel
"""

import argparse
import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from opentable_client import OpenTableClient


def generate_share_message(reservation, restaurant, include_link=True):
    """Generate a shareable message for a reservation"""
    message = f"🍽️ Dinner Reservation\n\n"
    message += f"📍 {reservation.get('restaurant_name', restaurant.get('name', 'Unknown'))}\n"
    message += f"📅 {reservation.get('date')}\n"
    message += f"🕒 {reservation.get('time')}\n"
    message += f"👥 Party of {reservation.get('party_size')}\n"
    
    if restaurant.get('address'):
        message += f"📮 {restaurant.get('address')}, {restaurant.get('city', '')}\n"
    
    if reservation.get('confirmation_number'):
        message += f"🎫 Confirmation: {reservation.get('confirmation_number')}\n"
    
    if include_link and reservation.get('share_url'):
        message += f"\n🔗 {reservation.get('share_url')}"
    elif include_link and restaurant.get('reserve_url'):
        message += f"\n🔗 {restaurant.get('reserve_url')}"
    
    return message


def generate_opentable_share_url(confirmation_number):
    """Generate OpenTable share URL"""
    return f"https://www.opentable.com/reservation-details?confirmation={confirmation_number}"


def generate_whatsapp_url(phone, message):
    """Generate WhatsApp click-to-chat URL"""
    encoded_message = urllib.parse.quote(message)
    return f"https://wa.me/{phone}?text={encoded_message}"


def generate_sms_url(phone, message):
    """Generate SMS URL scheme"""
    encoded_message = urllib.parse.quote(message)
    return f"sms:{phone}?body={encoded_message}"


def generate_email_url(email, subject, body):
    """Generate email mailto URL"""
    encoded_subject = urllib.parse.quote(subject)
    encoded_body = urllib.parse.quote(body)
    return f"mailto:{email}?subject={encoded_subject}&body={encoded_body}"


def main():
    parser = argparse.ArgumentParser(description="Share OpenTable reservation")
    parser.add_argument("--confirmation-number", required=True, help="Reservation confirmation number")
    parser.add_argument("--email", help="Your email (for lookup)")
    parser.add_argument("--to", help="Recipient phone/email (for WhatsApp/SMS/Email)")
    parser.add_argument("--channel", required=True, 
                       choices=["opentable", "whatsapp", "sms", "email", "copy"],
                       help="Sharing channel")
    parser.add_argument("--message", help="Custom message to include")
    parser.add_argument("--api-key", help="OpenTable API key")
    
    args = parser.parse_args()
    
    try:
        client = OpenTableClient(api_key=args.api_key)
        
        # Get reservation details
        reservation = client.get_reservation(args.confirmation_number)
        
        # Get restaurant details if available
        restaurant = {}
        if reservation.get('restaurant_id'):
            try:
                restaurant = client.get_restaurant(reservation['restaurant_id'])
            except:
                pass
        
        # Generate share content
        share_message = generate_share_message(reservation, restaurant)
        
        if args.message:
            share_message = f"{args.message}\n\n{share_message}"
        
        output = {
            "success": True,
            "channel": args.channel,
            "confirmation_number": args.confirmation_number,
            "share_text": share_message
        }
        
        # Generate channel-specific share method
        if args.channel == "opentable":
            output["share_url"] = generate_opentable_share_url(args.confirmation_number)
            output["method"] = "OpenTable app share"
            
        elif args.channel == "whatsapp":
            if not args.to:
                print(json.dumps({
                    "success": False,
                    "error": "WhatsApp sharing requires --to with phone number (international format, e.g., +1234567890)"
                }))
                sys.exit(1)
            output["share_url"] = generate_whatsapp_url(args.to, share_message)
            output["method"] = "WhatsApp"
            output["instructions"] = "Click the share_url or use OpenClaw's message tool"
            
        elif args.channel == "sms":
            if not args.to:
                print(json.dumps({
                    "success": False,
                    "error": "SMS sharing requires --to with phone number"
                }))
                sys.exit(1)
            output["share_url"] = generate_sms_url(args.to, share_message)
            output["method"] = "SMS"
            output["instructions"] = "Click the share_url or use OpenClaw's message tool"
            
        elif args.channel == "email":
            if not args.to:
                print(json.dumps({
                    "success": False,
                    "error": "Email sharing requires --to with email address"
                }))
                sys.exit(1)
            subject = f"Dinner Reservation: {reservation.get('restaurant_name', 'Restaurant')}"
            output["share_url"] = generate_email_url(args.to, subject, share_message)
            output["method"] = "Email"
            output["instructions"] = "Click the share_url or use OpenClaw's message tool"
            
        elif args.channel == "copy":
            output["method"] = "Copy to clipboard"
            output["instructions"] = "Share text is ready to copy"
        
        print(json.dumps(output, indent=2))
        
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
