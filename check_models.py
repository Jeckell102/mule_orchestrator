import google.generativeai as genai
import os

# --- PATH SETUP ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(SCRIPT_DIR, "api_key.txt")

# --- LOAD KEY ---
if not os.path.exists(KEY_FILE):
    print("❌ Error: api_key.txt not found.")
    exit()

with open(KEY_FILE, "r") as f:
    api_key = f.read().strip()

genai.configure(api_key=api_key)

# --- THE DIAGNOSTIC ---
print("🔍 Scanning available AI models for this API key...")
try:
    available_models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"  ✅ FOUND: {m.name}")
            available_models.append(m.name)
    
    if not available_models:
        print("\n⚠️ No content generation models found. Check your API key permissions.")
    else:
        print(f"\n🎉 SUCCESS: Found {len(available_models)} usable models.")
        print(f"👉 Recommended Model ID: {available_models[0]}")

except Exception as e:
    print(f"\n❌ CONNECTION FAILED: {e}")