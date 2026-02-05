import os
import sqlite3

def run_diagnostics():
    print("🔍 [DIAGNOSTIC] Starting MuleLab System Check...")
    
    # 1. Check Directory Structure
    dirs = ['logs', 'prompts', 'tests']
    for d in dirs:
        status = "✅" if os.path.exists(d) else "❌"
        print(f"{status} Directory: {d}")

    # 2. Check Database Connectivity
    db_path = 'logs/mule_results.db'
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            print("✅ Database: Connection Successful.")
            conn.close()
        except Exception as e:
            print(f"❌ Database: Connection Failed. Error: {e}")
    else:
        print("⚠️ Database: Not found. Run 'python3 mule.py setup' first.")

    # 3. Check API Key
    if os.path.exists('api_key.txt'):
        print("✅ API Key: api_key.txt detected.")
    else:
        print("❌ API Key: api_key.txt MISSING.")

if __name__ == "__main__":
    run_diagnostics()