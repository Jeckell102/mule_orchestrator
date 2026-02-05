import sqlite3
import os
import json
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "logs", "mule_results.db")

def view_audit():
    if not os.path.exists(DB_PATH):
        print(f"🛑 [ERROR] Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # 1. Team Performance Summary
    print("\n" + "="*50)
    print(f"📊 AEGIS GARDENER: TEAM PERFORMANCE AUDIT")
    print("="*50)
    
    df = pd.read_sql_query("SELECT status, iterations FROM mule_audit", conn)
    if df.empty:
        print("No audit records found. Run 'mule.py start' first.")
        return

    success_rate = (len(df[df['status'] == 'VALIDATED']) / len(df)) * 100
    avg_iters = df['iterations'].mean()
    
    print(f"Success Rate:    {success_rate:.1f}%")
    print(f"Avg. Iterations: {avg_iters:.2f} cycles")
    print("-" * 50)

    # 2. Detailed Task History
    query = """
    SELECT timestamp, prompt, status, iterations, specialist_feedback 
    FROM mule_audit 
    ORDER BY timestamp DESC LIMIT 10
    """
    c = conn.cursor()
    c.execute(query)
    rows = c.fetchall()

    for ts, prompt, status, iters, feedback in rows:
        color = "✅" if status == "VALIDATED" else "❌"
        print(f"{color} [{ts}] {prompt[:60]}...")
        print(f"   Status: {status} | Cycles: {iters}")
        
        # Parse Specialist Feedback
        if feedback:
            try:
                logs = json.loads(feedback)
                for log in logs:
                    print(f"   ↳ {log}")
            except:
                pass
        print("-" * 50)

    conn.close()

if __name__ == "__main__":
    view_audit()