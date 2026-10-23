"""
List available Gemini models
"""
import os
import sys
import django

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')
django.setup()

from django.conf import settings
import urllib.request
import json

api_key = settings.GEMINI_API_KEY
url = f'https://generativelanguage.googleapis.com/v1beta/models?key={api_key}'

try:
    with urllib.request.urlopen(url, timeout=10) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        models = data.get('models', [])
        
        print("=" * 60)
        print("Available Gemini Models:")
        print("=" * 60)
        
        for model in models:
            name = model.get('name', '')
            if 'generateContent' in model.get('supportedGenerationMethods', []):
                print(f"✅ {name}")
        
        print("=" * 60)
except Exception as e:
    print(f"Error: {e}")
