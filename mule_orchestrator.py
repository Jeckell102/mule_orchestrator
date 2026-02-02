import os, sys, subprocess, re, requests, time
from datetime import datetime

# --- GPS & GIT LIBRARIES ---
try: import gps
except ImportError: gps = None

# --- PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
def get_path(f, sub=""): return os.path.join(BASE_DIR, sub, f)

# --- SDK SETUP ---
from google import genai
from google.genai import types

class MuleTeam:
    def __init__(self):
        with open(get_path("api_key.txt"), 'r') as f:
            self.client = genai.Client(api_key=f.read().strip())
        self.agents = self._load_roles()
        self.current_role = "Principal Engineer"

    def _load_roles(self):
        roles = {}
        mapping = {"PE": "pe.txt", "ME": "me.txt", "SW": "code_monkey.txt", 
                   "PM": "pm.txt", "QA": "qa.txt", "TW": "tech_writer.txt"}
        for k, v in mapping.items():
            path = get_path(v, "prompts")
            if os.path.exists(path):
                with open(path, 'r') as f: roles[k] = f.read()
        return roles

    def get_location_context(self):
        """Tiered Location Fetch: GPS -> IP -> Elyria."""
        # Layer 1: GPS Fix
        if gps:
            try:
                session = gps.gps(mode=gps.WATCH_ENABLE)
                start = time.time()
                while time.time() - start < 1.5: # 1.5s timeout for lock
                    report = session.next()
                    if report['class'] == 'TPV' and getattr(report, 'mode', 0) >= 2:
                        return f"{report.lat},{report.lon}", "GPS Satellite Fix"
            except: pass

        # Layer 2: IP Address Fallback
        try:
            res = requests.get("http://ip-api.com/json/", timeout=2).json()
            if res['status'] == 'success':
                return f"{res['lat']},{res['lon']}", f"IP Geolocation ({res['city']})"
        except: pass

        # Layer 3: Default to Elyria
        return "Elyria,OH", "Default (Elyria Base)"

    def get_weather(self):
        loc_query, source = self.get_location_context()
        try:
            # wttr.in handles both coordinates and city names
            res = requests.get(f"https://wttr.in/{loc_query}?format=%t+%w+%h").text
            return f"{res.strip()} | Source: {source}"
        except: return f"Weather offline | Location: {source}"

    def get_response(self, user_input, override_role=None):
        role_key = override_role or self.current_role
        config = types.GenerateContentConfig(
            system_instruction=self.agents.get(role_key, ""),
            thinking_config=types.ThinkingConfig(include_thoughts=True),
            thinking_budget=-1 # Pro-logic active
        )
        return self.client.models.generate_content(
            model="gemini-2.5-pro", contents=user_input, config=config
        ).text

# --- RUN LOOP ---
def main():
    mule = MuleTeam()
    env = mule.get_weather()
    print(f"--- MuleLab Online | {env} ---")
    
    # Startup Environmental Briefing
    brief = mule.get_response(f"Environment: {env}. Give me a 2-sentence startup brief regarding hardware constraints.")
    print(f"\n[PE]: {brief}\n")

    while True:
        try:
            msg = input("YOU: ")
            if msg.lower() in ['exit', 'quit']: break
            print(f"\n[{mule.current_role}]:\n{mule.get_response(msg)}\n")
        except Exception as e: print(f"❌ Error: {e}")

if __name__ == "__main__": main()