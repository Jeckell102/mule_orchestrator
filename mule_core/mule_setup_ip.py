import sqlite3
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "mule_results.db")

def setup_ip_tracker():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # IP Tracker Table
    c.execute('''CREATE TABLE IF NOT EXISTS mule_ip_tracker (
        ip_id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        innovation_title TEXT,
        problem_solved TEXT,
        technical_solution TEXT,
        boolean_search_string TEXT,
        status TEXT DEFAULT 'POTENTIAL')''')

    # Seeding discovered IP from project logs
    innovations = [
        ('Multi-Agent Consensus Engine for Hardware-Constrained Environments', 
         'AI agents generating code for physical robots often ignore mechanical stress or safety boundaries.', 
         'A three-tier handshake protocol (Gatekeeper-Specialist-Consensus) that requires tokenized validation from distinct Mechanical and Safety personas before code deployment.',
         '("multi-agent" AND "consensus" AND "robotics" AND "code generation" AND "physical constraints")'),
        
        ('Hardware-Safety-Governor (Pre-Flight Violation Check)',
         'Autonomous agents may attempt to execute commands that exceed physical hardware ratings (e.g., motor torque or chassis load).',
         'A proactive regex-based filter that cross-references user intent against a local Master Requirements Database (MRD) to kill unsafe tasks before code generation begins.',
         '("autonomous agent" AND "safety governor" AND "hardware limits" AND "proactive" AND "robotics")'),

        ('Self-Healing Logic Framework for Agentic Workflows',
         'Agentic workflows frequently fail due to context drift or instruction misalignment over time.',
         'A method for capturing execution failures in a relational database and using a second-order Analyst agent to dynamically rewrite primary instruction sets.',
         '("AI" OR "LLM") AND (orchestrat* OR agent*) AND ("closed loop") AND (audit OR log*)')
    ]

    c.executemany('''INSERT OR IGNORE INTO mule_ip_tracker 
                     (innovation_title, problem_solved, technical_solution, boolean_search_string) 
                     VALUES (?,?,?,?)''', innovations)
    
    conn.commit()
    conn.close()
    print("✅ [IP TRACKER] Discovered IP has been logged and secured.")

if __name__ == "__main__":
    setup_ip_tracker()