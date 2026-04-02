import sqlite3

conn = sqlite3.connect(r'C:\Users\gregm\AppData\Local\Conduital\tracker.db')
cursor = conn.cursor()

# Get all table schemas
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL")
for row in cursor.fetchall():
    print(row[0])
    print()

# Get row counts
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("=== ROW COUNTS ===")
for t in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
        count = cursor.fetchone()[0]
        print(f"{t}: {count} rows")
    except:
        pass

conn.close()
