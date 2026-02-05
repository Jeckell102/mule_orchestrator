import sqlite3, pandas as pd, os
def show():
    db = 'logs/mule_results.db'
    if not os.path.exists(db):
        print("❌ [ERROR] Database not found.")
        return
    conn = sqlite3.connect(db)
    try:
        df = pd.read_sql('SELECT specialist_consulted, COUNT(*) as count FROM mule_audit GROUP BY specialist_consulted', conn)
        print('\n📊 TEAM UTILIZATION CHART\n' + '-'*30)
        for _, r in df.iterrows():
            spec = str(r['specialist_consulted'])
            count = int(r['count'])
            print(f"{spec:<15} | {'█' * count} ({count})")
    except Exception as e:
        print(f"❌ [ERROR] {e}")
    finally:
        conn.close()
if __name__ == '__main__': show()
