import sqlite3
import sys
import os

db_path = r'C:\Users\gregm\AppData\Local\Conduital\tracker.db'
print(f"DB exists: {os.path.exists(db_path)}")
print(f"DB size: {os.path.getsize(db_path)} bytes")

# Check WAL and SHM
for ext in ['-wal', '-shm']:
    p = db_path + ext
    if os.path.exists(p):
        print(f"{ext} size: {os.path.getsize(p)} bytes")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List all tables
    cursor.execute("SELECT name, type, sql FROM sqlite_master")
    rows = cursor.fetchall()
    print(f"\nsqlite_master has {len(rows)} entries")
    for row in rows:
        print(f"  {row[1]}: {row[0]}")
        if row[2]:
            print(f"    {row[2][:200]}")
    
    conn.close()
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
