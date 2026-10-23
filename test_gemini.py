"""
Quick test script to verify Gemini API is working
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kaaf.settings')
django.setup()

from django.conf import settings
import urllib.request
import urllib.error
import json

def test_gemini():
    api_key = settings.GEMINI_API_KEY
    print(f"API Key: {api_key[:20]}..." if api_key else "No API key found!")
    
    if not api_key:
        print("❌ GEMINI_API_KEY not set in settings")
        return False
    
    # Simple test message
    payload = json.dumps({
        'contents': [{'role': 'user', 'parts': [{'text': 'Say hello'}]}],
        'generationConfig': {'maxOutputTokens': 50}
    }).encode('utf-8')
    
    models = ['gemini-flash-lite-latest', 'gemini-flash-latest', 'gemini-2.5-flash-lite']
    
    for model in models:
        print(f"\n🧪 Testing {model}...")
        url = f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}'
        req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'}, method='POST')
        
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                candidates = data.get('candidates', [])
                if candidates:
                    response = candidates[0]['content']['parts'][0]['text'].strip()
                    print(f"✅ {model} works!")
                    print(f"Response: {response}")
                    return True
                else:
                    print(f"⚠️ {model} returned no candidates")
                    print(f"Response: {data}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            print(f"Details: {error_body}")
        except urllib.error.URLError as e:
            print(f"❌ URL Error: {e.reason}")
        except Exception as e:
            print(f"❌ Exception: {type(e).__name__}: {e}")
    
    return False

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Gemini API Connection")
    print("=" * 60)
    
    success = test_gemini()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Gemini API is working!")
    else:
        print("❌ Gemini API test failed")
        print("\nPossible issues:")
        print("1. Invalid API key")
        print("2. No internet connection")
        print("3. API quota exceeded")
        print("4. Model not available")
    print("=" * 60)
