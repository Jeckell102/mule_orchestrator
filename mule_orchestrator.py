import os, sys, subprocess, re, requests, time
from datetime import datetime
try: from git import Repo
except ImportError: Repo = None

# --- PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")
def get_path(f, sub=""): return os.path.join(BASE_DIR, sub, f)

# --- SDK SETUP ---
from google import genai
from google.genai import types

class AegisGardener:
    def __init__(self):
        with open(get_path("api_key.txt"), 'r') as f:
            self.client = genai.Client(api_key=f.read().strip())
        self.agents = self._load_roles()
        self.current_role = "Principal Engineer"
        self.log_file = get_path(f"mule_log_{datetime.now().strftime('%Y-%m-%d')}.md")

    def _load_roles(self):
        roles = {}
        mapping = {"PE": "pe.txt", "ME": "me.txt", "SW": "code_monkey.txt", 
                   "PM": "pm.txt", "QA": "qa.txt", "TW": "tech_writer.txt"}
        for k, v in mapping.items():
            path = get_path(v, "prompts")
            if os.path.exists(path):
                with open(path, 'r') as f: roles[k] = f.read()
        return roles

    def auto_backup(self):
        """Final session sync to GitHub."""
        if Repo is None: return
        try:
            repo = Repo(BASE_DIR)
            if repo.is_dirty(untracked_files=True):
                print("\n📡 [AEGIS]: Syncing R&D logs to GitHub...")
                repo.git.add(all=True)
                repo.index.commit(f"Session Close: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
                repo.remote(name='origin').push()
                print("✅ Sync Complete.")
        except Exception as e: print(f"⚠️ Sync failed: {e}")

    def get_response(self, user_input, override_role=None):
        role_key = override_role or self.current_role
        config = types.GenerateContentConfig(
            system_instruction=self.agents.get(role_key, ""),
            thinking_config=types.ThinkingConfig(include_thoughts=True),
            thinking_budget=-1 # Dynamic Pro Reasoning enabled
        )
        return self.client.models.generate_content(
            model="gemini-2.5-pro", contents=user_input, config=config
        ).text

# --- STARTUP ---
def main():
    aegis = AegisGardener()
    print(f"--- AEGIS GARDENER: ONLINE ---")
    print(f"Ready for Principal Engineer input.\n")

    while True:
        try:
            msg = input("YOU: ")
            if msg.lower() in ['exit', 'quit']:
                aegis.auto_backup()
                break
            
            response = aegis.get_response(msg)
            print(f"\n[{aegis.current_role}]:\n{response}\n")
            
        except Exception as e: 
            print(f"❌ Error: {e}")

if __name__ == "__main__": 
    main()