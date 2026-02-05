import sqlite3
import csv
import os

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "logs", os.path.join("data", "mule_results.db"))
CSV_PATH = os.path.join(BASE_DIR, os.path.join("data", "requirements.csv"))

def seed_mrd():
    """Reads requirements.csv and updates the Master Requirements Database."""
    if not os.path.exists(CSV_PATH):
        print(f"🛑 [ERROR] Could not find requirements.csv at {CSV_PATH}")
        return

    try:
        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            to_db = []
            for row in reader:
                if not row['req_id']: continue
                to_db.append((
                    row['req_id'].strip(),
                    row['category'].strip(),
                    float(row['threshold']),
                    row['unit'].strip(),
                    row['logic_trigger'].lower().strip(),
                    row['description'].strip()
                ))
                
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Overwrites existing entries if the ID matches
        c.executemany("INSERT OR REPLACE INTO mule_requirements VALUES (?,?,?,?,?,?)", to_db)
        conn.commit()
        conn.close()
        
        print(f"✅ [SUCCESS] Loaded {len(to_db)} project requirements into the database.")
    except Exception as e:
        print(f"❌ [CRITICAL] Failed to parse requirements.csv: {e}")

if __name__ == "__main__":
    seed_mrd()