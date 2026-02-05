import os, sys, requests, time, re
from datetime import datetime
try: from git import Repo
except ImportError: Repo = None

# --- SDK SETUP ---
from google import genai
from google.genai import types

# --- PATH RESOLUTION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def get_path(f, sub=""): return os.path.join(BASE_DIR, sub, f)

class AegisGardener:
    def __init__(self):
        with open(get_path("api_key.txt"), 'r') as f:
            self.client = genai.Client(api_key=f.read().strip())
        self.agents = self._load_roles()
        self.current_role = "PE"
        self.role_names = {
            "PE": "Principal Engineer", "ME": "Mechanical Engineer", 
            "SW": "Software Engineer", "PM": "Project Manager", 
            "QA": "Quality Assurance", "TW": "Tech Writer"
        }
        self.models = {"fast": "gemini-2.0-flash", "pro": "gemini-2.5-pro"}
        
        # --- LOGGING INITIALIZATION (NEW) ---
        self.log_dir = get_path("logs")
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _load_roles(self):
        roles = {}
        mapping = {"PE": "pe.txt", "ME": "me.txt", "SW": "sw.txt", 
                   "PM": "pm.txt", "QA": "qa.txt", "TW": "tech_writer.txt"}
        for k, v in mapping.items():
            path = get_path(v, "prompts")
            if os.path.exists(path):
                with open(path, 'r') as f: roles[k] = f.read()
        return roles

    # --- SESSION LOGGING METHOD (NEW) ---
    def _log_session(self, user_input, response, path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"dev_log_{timestamp}.txt")
        with open(log_file, "w") as f:
            f.write(f"TIMESTAMP: {datetime.now()}\n")
            f.write(f"USER: {user_input}\n")
            f.write(f"EXPERT_PATH: {path}\n")
            f.write(f"--- RESPONSE ---\n{response}")

    def read_file(self, filename: str) -> str:
        try:
            with open(get_path(filename), 'r') as f: return f.read()
        except Exception as e: return f"Error reading {filename}: {e}"

    def write_file(self, filename: str, content: str) -> str:
        print(f"\n[SYSTEM]: AI is requesting to write to {filename}.")
        confirm = input(f"PROCEED WITH UPDATE? (y/n): ")
        if confirm.lower() == 'y':
            try:
                with open(get_path(filename), 'w') as f: f.write(content)
                return f"Successfully updated {filename}."
            except Exception as e: return f"Error writing to {filename}: {e}"
        return "Write operation rejected by user."

    def get_response(self, user_input, model_key="fast"):
        model_choice = self.models[model_key]
        breadcrumb = [self.current_role]
        decision_log = []
        visit_queue = []
        
        print(f"🔍 [DEBUG]: Persona: {self.current_role} | Model: {model_key.upper()} | Mode: [MULTI-TARGET]")
        print(f"📡 [THINKING]: {breadcrumb[0]}", end="", flush=True)

        while True:
            config = types.GenerateContentConfig(
                system_instruction=self.agents.get(self.current_role, ""),
                tools=[self.read_file, self.write_file],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
            )
            
            context = [{"role": "user", "parts": [{"text": user_input}]}]
            if decision_log:
                log_summary = "\n".join(decision_log)
                context.append({"role": "model", "parts": [{"text": f"PREVIOUS SPECIALIST DECISIONS:\n{log_summary}"}]})

            try:
                response = self.client.models.generate_content(model=model_choice, contents=context, config=config)
                response_text = str(response.text) if response.text else ""
                
                if response_text.strip():
                    decision_log.append(f"[{self.current_role}]: {response_text[:500]}")

                found_targets = re.findall(r"\[TARGET(?:\s+GEM)?:\s*([\w\s]+)\s*\]", response_text)
                for raw_target in found_targets:
                    clean_target = raw_target.strip().upper()
                    role_map = {"MECHANICAL ENGINEER": "ME", "SOFTWARE ENGINEER": "SW", "CODE MONKEY": "SW", "PROJECT MANAGER": "PM", "QUALITY ASSURANCE": "QA", "TECH WRITER": "TW"}
                    new_role = role_map.get(clean_target, clean_target)

                    if new_role in self.agents and new_role != self.current_role:
                        if new_role not in breadcrumb or new_role == "PE":
                            visit_queue.append(new_role)

                if visit_queue:
                    self.current_role = visit_queue.pop(0)
                    breadcrumb.append(self.current_role)
                    print(f" ➔ {self.current_role}", end="", flush=True)
                    continue 

                if model_key == "fast" and len(breadcrumb) < 2:
                    print("\n⚠️ [ESCALATING]: Incomplete reasoning detected. Rerunning with PRO...")
                    self.current_role = "PE"
                    return self.get_response(user_input, model_key="pro")

                print(" ✅") 
                final_trail = f" ➔ {' ➔ '.join(breadcrumb)}"
                full_output = response_text + f"\n\n[Expert Path: {final_trail}] [Model: {model_key.upper()}]"
                
                # --- AUTO-LOGGING (NEW) ---
                self._log_session(user_input, full_output, final_trail)
                
                return full_output

            except Exception as e:
                return f"\n❌ System Error: {str(e)}"

    def main_loop(self):
        print(f"--- AEGIS GARDENER: ONLINE ---")
        print(f"Version: [MIXED-MODEL-ROBUST] | Telemetry: [LOGS_ACTIVE]\n")
        while True:
            try:
                msg = input("YOU: ")
                if msg.lower() in ['exit', 'quit']: break
                print(self.get_response(msg))
                print("-" * 30)
                self.current_role = "PE"
            except Exception as e: print(f"❌ Crash: {e}")

if __name__ == "__main__":
    AegisGardener().main_loop()