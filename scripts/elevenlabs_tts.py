#!/usr/bin/env python3
"""
ElevenLabs TTS - Direct API wrapper
Usage: python3 elevenlabs_tts.py "Your text here"
"""

import os
import sys
import requests
import json

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not API_KEY:
    print("Error: ELEVENLABS_API_KEY not set")
    sys.exit(1)

BASE_URL = "https://api.elevenlabs.io/v1"

def list_voices():
    """List available voices"""
    response = requests.get(
        f"{BASE_URL}/voices",
        headers={"xi-api-key": API_KEY}
    )
    if response.status_code == 200:
        voices = response.json()["voices"]
        print("Available voices:")
        for voice in voices[:10]:  # Show first 10
            print(f"  - {voice['name']} (ID: {voice['voice_id']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def speak(text, voice_id="21m00Tcm4TlvDq8ikWAM", output_file="output.mp3"):
    """Generate speech from text"""
    response = requests.post(
        f"{BASE_URL}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
    )
    
    if response.status_code == 200:
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"Audio saved to: {output_file}")
        return output_file
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 elevenlabs_tts.py 'Your text here'")
        print("       python3 elevenlabs_tts.py --voices")
        sys.exit(1)
    
    if sys.argv[1] == "--voices":
        list_voices()
    else:
        text = " ".join(sys.argv[1:])
        speak(text)