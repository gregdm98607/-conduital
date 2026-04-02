import sqlite3

conn = sqlite3.connect(r'C:\Users\gregm\AppData\Local\Conduital\tracker.db')
cursor = conn.cursor()

tables_of_interest = ['areas', 'projects', 'project_phases', 'tasks', 'contexts', 'goals', 'visions', 'inbox', 'activity_log', 'users', 'phase_templates', 'weekly_review_completions', 'momentum_snapshots']

for t in tables_of_interest:
    print(f"\n=== {t} ===")
    cursor.execute(f"PRAGMA table_info([{t}])")
    cols = cursor.fetchall()
    for c in cols:
        print(f"  {c[1]} ({c[2]}) {'NOT NULL' if c[3] else ''} default={c[4]}")
    cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
    print(f"  -> {cursor.fetchone()[0]} rows")

# Check existing data samples
print("\n=== EXISTING USERS ===")
cursor.execute("SELECT * FROM users LIMIT 5")
for r in cursor.fetchall():
    print(r)

print("\n=== EXISTING AREAS ===")
cursor.execute("SELECT * FROM areas LIMIT 5")
for r in cursor.fetchall():
    print(r)

print("\n=== EXISTING PROJECTS ===")
cursor.execute("SELECT * FROM projects LIMIT 5")
for r in cursor.fetchall():
    print(r)

print("\n=== EXISTING TASKS ===")
cursor.execute("SELECT * FROM tasks LIMIT 5")
for r in cursor.fetchall():
    print(r)

print("\n=== EXISTING CONTEXTS ===")
cursor.execute("SELECT * FROM contexts LIMIT 5")
for r in cursor.fetchall():
    print(r)

print("\n=== PHASE TEMPLATES ===")
cursor.execute("SELECT * FROM phase_templates LIMIT 5")
for r in cursor.fetchall():
    print(r)

conn.close()
