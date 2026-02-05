import os
import sys
import sqlite3
import argparse
import datetime
import time
import warnings
import re

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
DB_PATH = os.path.join(LOG_DIR, os.path.join("data", "mule_results.db"))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

warnings.filterwarnings("ignore")

try:
    import google.generativeai as genai
    from google.api_core import exceptions
except ImportError:
    print("🛑 [ERROR] Missing library: google-generativeai")
    sys.exit(1)

os.makedirs(LOG_DIR, exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''CREATE TABLE IF NOT EXISTS mule_audit
                    (timestamp TEXT, prompt TEXT, status TEXT, iterations INTEGER, 
                     specialist_feedback TEXT, proposal TEXT, model_used TEXT)''')
    return conn

def configure_genai():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("🛑 [AUTH ERROR] GOOGLE_API_KEY missing. Run 'source mule_init.sh'")
        sys.exit(1)
    genai.configure(api_key=api_key)

def get_valid_model(complexity_high=False):
    print("📡 [CONNECTING] Auto-negotiating Model ID...")
    try:
        all_models = [m for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        found_names = [m.name for m in all_models]
        if not found_names: sys.exit(1)

        if complexity_high:
            preferences = ["gemini-1.5-pro", "gemini-pro"]
        else:
            preferences = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]

        for pref in preferences:
            for model_name in found_names:
                if pref in model_name: return model_name
        return found_names[0]
    except:
        return "models/gemini-1.5-flash"

def inject_file_context(prompt):
    """Scans prompt for filenames and injects content."""
    files_found = []
    words = prompt.split()
    context_buffer = "\n\n=== AUTOMATIC CONTEXT INJECTION ===\n"
    
    for word in words:
        clean_word = word.strip("',.\":")
        if os.path.isfile(os.path.join(BASE_DIR, clean_word)):
            if clean_word in ["mule.py", os.path.join("data", "mule_results.db")] or clean_word.endswith(".db"):
                continue
                
            try:
                with open(clean_word, 'r') as f:
                    content = f.read()
                    if len(content) > 20000:
                        content = content[:20000] + "\n...[TRUNCATED]..."
                    
                    context_buffer += f"FILE: {clean_word}\n```\n{content}\n```\n"
                    files_found.append(clean_word)
            except:
                pass
    
    if files_found:
        print(f"📖 [CONTEXT SNIFFER] Read files: {files_found}")
        return context_buffer
    return ""

def apply_code_changes(proposal):
    pattern = r"START_MULE: (.*?)\n(.*?)\nSTOP_MULE: \1"
    matches = re.findall(pattern, proposal, re.DOTALL)
    
    if not matches:
        print("⚠️ [FILE SYSTEM] No 'START_MULE' tags found.")
        return False

    for filename, content in matches:
        filepath = os.path.join(BASE_DIR, filename.strip())
        try:
            with open(filepath, "w") as f:
                f.write(content.strip())
            print(f"💾 [SAVED] {filename}")
        except Exception as e:
            print(f"❌ [ERROR] Writing {filename}: {e}")
            return False
    return True

def run_orchestrator(prompt):
    configure_genai()
    print(f"✅ [SETUP] DB: {DB_PATH}")
    
    # 0. Context Injection
    file_context = inject_file_context(prompt)
    
    # 1. Setup
    is_override = "OVERRIDE" in prompt.upper() or "SKIP" in prompt.upper()
    is_complex = any(k in prompt.lower() for k in ["red team", "architect"])
    
    model_name = get_valid_model(is_complex)
    print(f"🔹 Locked Target: {model_name}")
    model = genai.GenerativeModel(model_name)
    
    iterations = 0
    max_iterations = 3
    status = "PROCESSING"
    feedback_history = []
    final_proposal = ""
    
    try:
        pe_persona = open(os.path.join(PROMPTS_DIR, "pe.txt")).read()
    except:
        pe_persona = "You are the Principal Engineer."

    chat = model.start_chat(history=[])
    chat.history.append({"role": "user", "parts": [pe_persona]})
    chat.history.append({"role": "model", "parts": ["Understood."]})
    
    # Mission Logic
    flow = "Me -> SW -> PE -> Me (Direct)" if is_override else "Me -> SW -> PE -> Team -> PE -> Me"
    
    current_input = f"TASK: {prompt}\nFLOW: {flow}\n{file_context}"
    current_input += """
    INSTRUCTION: 
    1. READ the injected file context.
    2. If editing, output the FULL FILE content with your changes.
    3. Use START_MULE: filename / STOP_MULE: filename tags.
    """

    # 3. Execution Loop
    while iterations < max_iterations:
        iterations += 1
        print(f"🔄 [CONSENSUS] Cycle {iterations}/{max_iterations}...")
        
        try:
            response = chat.send_message(current_input).text
        except Exception as e:
            print(f"❌ [API ERROR] {e}")
            break

        # --- USER GATE ---
        if "DO YOU WISH TO APPLY" in response.upper() or "(y/n)" in response.lower():
            print("\n" + "═"*40)
            print("⚠️  AEGIS USER GATE")
            print("═"*40)
            print(response.strip()) 
            print("═"*40)
            
            user_decision = input(">> DECISION (y/n or feedback): ").strip()
            
            if user_decision.lower() == 'y':
                if apply_code_changes(response):
                    status = "VALIDATED"
                    final_proposal = response
                    print("✅ [COMMIT SUCCESS]")
                else:
                    status = "WRITE_FAILURE"
                break
            else:
                print("❌ [REJECTED] Re-routing...")
                feedback_history.append(f"Rejected: {user_decision}")
                current_input = f"User feedback: {user_decision}. Refine proposal."
                continue

        if "[FINAL STATE]: VALIDATED" in response:
            status = "VALIDATED"
            final_proposal = response
            print(f"\n🚀 [FINAL STATE]: VALIDATED")
            break
            
        current_input = f"Refine plan: {response}"

    conn = get_db_connection()
    try:
        conn.execute("INSERT INTO mule_audit VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (str(datetime.datetime.now()), prompt, status, iterations, str(feedback_history), final_proposal, model_name))
        conn.commit()
    except:
        conn.execute("DROP TABLE mule_audit")
        get_db_connection().execute("INSERT INTO mule_audit VALUES (?, ?, ?, ?, ?, ?, ?)", 
                     (str(datetime.datetime.now()), prompt, status, iterations, str(feedback_history), final_proposal, model_name)).commit()
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("start")
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()
    run_orchestrator(args.prompt)