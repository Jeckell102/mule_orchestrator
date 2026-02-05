import os
import time
import json
import sqlite3
import re
from datetime import datetime

# --- CONFIGURATION ---
INCOMING_FILE = "incoming.txt"
DB_NAME = "aegis_master.db"
PROJECT_ROOT = os.getcwd()

def init_db():
    conn = sqlite3.connect(DB_NAME)
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
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*), MAX(created_at), summary FROM ip_assets")
        row = cursor.fetchone()
        if row and row[0] > 0:
            print(f"📊 [DATABASE AUDIT]: {row[0]} Assets secured. Latest: {row[2][:30]}...")
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
    conn = sqlite3.connect(DB_NAME)
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
    print(f"👀 [SCANNING]: Processing {len(raw_content)} bytes...")
    clean_content, ip_found = process_ip_payloads(raw_content)
    lines = clean_content.splitlines(keepends=True)
    current_file, buffer, code_found = None, [], False
    for line in lines:
        stripped = line.strip()
        if "START_MULE:" in stripped:
            current_file = stripped.split("START_MULE:")[1].strip()
            buffer, code_found = [], True
            print(f"   ... Recording {current_file}")
            continue
        if "STOP_MULE" in stripped:
            if current_file:
                file_path = os.path.join(PROJECT_ROOT, current_file)
                # --- NEW LOGIC: Create parent directories if they don't exist ---
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                final_code = [l for l in buffer if not l.strip().startswith("```")]
                with open(file_path, "w") as f: f.write("".join(final_code).strip())
                print(f"✅ [SAVED]: {current_file}")
                current_file = None
            continue
        if current_file: buffer.append(line)
    if ip_found or code_found:
        with open(INCOMING_FILE, "w") as f: f.write("")
        print("扫 Buffer cleared.")
        periodic_audit()

if __name__ == "__main__":
    init_db()
    print(f"🚀 [MULE_SYNC v10]: Ready (Directory Auto-Create Enabled)...")
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