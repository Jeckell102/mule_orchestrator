import os
import time
import json
import sqlite3
import re
from datetime import datetime

# --- CONFIGURATION (UPDATED FOR MODULAR STRUCTURE) ---
# Get the directory where this script lives (mule_core)
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root (one level up)
BASE_DIR = os.path.dirname(CORE_DIR)

# Define paths relative to the Project Root
INCOMING_FILE = os.path.join(BASE_DIR, "docs", os.path.join("docs", "incoming.txt"))
DB_PATH = os.path.join(BASE_DIR, "data", os.path.join("data", "aegis_master.db"))
PROJECT_ROOT = BASE_DIR

def init_db():
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ip_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            project TEXT,
            category TEXT,
            summary TEXT,
            search_string TEXT,
            confidence TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def periodic_audit():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), MAX(created_at), summary FROM ip_assets")
        row = cursor.fetchone()
        if row and row[0] > 0:
            summary = row[2][:30] if row[2] else "No Summary"
            print(f"📊 [DATABASE AUDIT]: {row[0]} Assets secured. Latest: {summary}...")
        else:
            print("📊 [DATABASE AUDIT]: Database is healthy but empty.")
        conn.close()
    except Exception as e:
        print(f"⚠️ [AUDIT FAILED]: {e}")

def process_ip_payloads(raw_content):
    pattern = r'(?:```\w*\s*)?(\{[\s\S]*?"protocol":\s*"IP_SENTRY_V1"[^}]*\})(?:\s*```)?'
    matches = re.findall(pattern, raw_content)
    if not matches:
        return raw_content, False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    processed_count = 0
    for json_str in matches:
        try:
            clean_json_str = json_str.strip()
            data = json.loads(clean_json_str)
            required = ['project', 'summary', 'search_string']
            if not all(k in data for k in required):
                print(f"❌ [VALIDATION FAILED]: Missing keys in IP block.")
                continue
            cursor.execute('''
                INSERT INTO ip_assets (timestamp, project, category, summary, search_string, confidence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data.get('timestamp'), data.get('project'), data.get('category'), data.get('summary'), data.get('search_string'), data.get('confidence'), datetime.now().isoformat()))
            print(f"📡 [IP SENTRY]: Asset Logged -> {data.get('summary')[:50]}")
            processed_count += 1
        except Exception as e:
            print(f"❌ [PARSING ERROR]: {e}")
    conn.commit()
    conn.close()
    clean_text = re.sub(pattern, '', raw_content).strip()
    return clean_text, (processed_count > 0)

def deploy_code():
    if not os.path.exists(INCOMING_FILE): return
    with open(INCOMING_FILE, "r") as f: raw_content = f.read()
    if not raw_content.strip(): return
    print(f"👀 [SCANNING]: Processing {len(raw_content)} bytes from {INCOMING_FILE}...")
    clean_content, ip_found = process_ip_payloads(raw_content)
    lines = clean_content.splitlines(keepends=True)
    current_file, buffer, code_found = None, [], False
    for line in lines:
        stripped = line.strip()
        if "START_MULE:" in stripped:
            # Handle path if it starts with "mule_core/" or "scripts/" etc.
            filename = stripped.split("START_MULE:")[1].strip()
            # If the filename provided is relative, join it with PROJECT_ROOT
            current_file = os.path.join(PROJECT_ROOT, filename)
            buffer, code_found = [], True
            print(f"   ... Recording {filename}")
            continue
        if "STOP_MULE" in stripped:
            if current_file:
                # --- NEW LOGIC: Create parent directories if they don't exist ---
                os.makedirs(os.path.dirname(current_file), exist_ok=True)
                final_code = [l for l in buffer if not l.strip().startswith("```")]
                with open(current_file, "w") as f: f.write("".join(final_code).strip())
                print(f"✅ [SAVED]: {os.path.relpath(current_file, PROJECT_ROOT)}")
                current_file = None
            continue
        if current_file: buffer.append(line)
    if ip_found or code_found:
        with open(INCOMING_FILE, "w") as f: f.write("")
        print("🧹 Buffer cleared.")
        periodic_audit()

if __name__ == "__main__":
    init_db()
    print(f"🚀 [MULE_SYNC v11]: Modular Edition Active")
    print(f"📂 Watching: {INCOMING_FILE}")
    print(f"💾 Database: {DB_PATH}")
    
    last_mtime = 0
    while True:
        try:
            if os.path.exists(INCOMING_FILE):
                mtime = os.path.getmtime(INCOMING_FILE)
                if mtime != last_mtime:
                    deploy_code()
                    last_mtime = mtime
            time.sleep(1) 
        except KeyboardInterrupt: break