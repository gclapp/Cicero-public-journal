#!/usr/bin/env python3
"""
Generate voice samples for comparison
Usage: python3 voice_samples.py
"""

import os
import requests

API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
if not API_KEY:
    print("Error: ELEVENLABS_API_KEY not set")
    exit(1)

BASE_URL = "https://api.elevenlabs.io/v1"

# Voice IDs and descriptions
VOICES = {
    "Roger": {"id": "CwhRBWXzGAHq8TQ4Fs17", "desc": "Laid-Back, Casual, Resonant"},
    "George": {"id": "JBFqnCBsd6RMkjVDRZzb", "desc": "Warm, Captivating Storyteller"},
    "Callum": {"id": "N2lVS1w4EtoT3dr4eOWO", "desc": "Husky"},
    "Liam": {"id": "TX3LPaxmHKxFdv7VOQHJ", "desc": "Energetic, Social Media Creator"},
    "Charlie": {"id": "IKne3meq5aSn9XLyUdCD", "desc": "Deep, Confident, Energetic"},
}

SAMPLE_TEXT = "Hello Geoff. This is Cicero, your digital familiar. I'm here to help with competitive intelligence, travel planning, and anything else you need."

def generate_sample(voice_name, voice_id, desc):
    output_file = f"voice_sample_{voice_name.lower()}.mp3"
    
    response = requests.post(
        f"{BASE_URL}/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": API_KEY,
            "Content-Type": "application/json"
        },
        json={
            "text": SAMPLE_TEXT,
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
        print(f"✅ {voice_name}: {desc}")
        print(f"   Saved: {output_file}")
        return True
    else:
        print(f"❌ {voice_name}: Error {response.status_code}")
        return False

print("Generating voice samples...\n")
for name, info in VOICES.items():
    generate_sample(name, info["id"], info["desc"])
    
print("\n📁 All samples saved. Listen and pick your favorite!")
print("\nTo use a specific voice, note the name and I'll set it as default.")