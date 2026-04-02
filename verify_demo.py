import sqlite3

conn = sqlite3.connect(r'C:\Users\gregm\AppData\Local\Conduital\tracker.db')
c = conn.cursor()

print("=== DATA SUMMARY ===\n")

# Counts
for table in ['areas', 'projects', 'tasks', 'contexts', 'goals', 'visions', 'inbox', 'activity_log', 'weekly_review_completions', 'momentum_snapshots']:
    c.execute(f"SELECT COUNT(*) FROM [{table}]")
    print(f"  {table}: {c.fetchone()[0]} rows")

print("\n=== AREAS ===")
c.execute("SELECT id, title, health_score, review_frequency FROM areas ORDER BY id")
for r in c.fetchall():
    print(f"  [{r[0]}] {r[1]} (health: {r[2]}, review: {r[3]})")

print("\n=== PROJECTS ===")
c.execute("SELECT id, title, status, momentum_score, area_id FROM projects ORDER BY id")
for r in c.fetchall():
    print(f"  [{r[0]}] {r[1]} ({r[2]}, momentum: {r[3]}, area: {r[4]})")

print("\n=== TASK STATUS BREAKDOWN ===")
c.execute("SELECT status, COUNT(*) FROM tasks GROUP BY status ORDER BY status")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== TASKS BY PROJECT (active projects) ===")
c.execute("""
    SELECT p.title, t.status, COUNT(*) 
    FROM tasks t JOIN projects p ON t.project_id = p.id 
    WHERE p.status = 'active'
    GROUP BY p.title, t.status
    ORDER BY p.title, t.status
""")
for r in c.fetchall():
    print(f"  {r[0]} - {r[1]}: {r[2]}")

print("\n=== INBOX ===")
c.execute("SELECT content, CASE WHEN processed_at IS NULL THEN 'UNPROCESSED' ELSE 'processed' END FROM inbox ORDER BY captured_at DESC")
for r in c.fetchall():
    print(f"  [{r[1]}] {r[0][:60]}")

print("\n=== GOALS ===")
c.execute("SELECT title, status, target_date FROM goals")
for r in c.fetchall():
    print(f"  {r[0]} ({r[1]}, target: {r[2]})")

print("\n=== VISIONS ===")
c.execute("SELECT title, timeframe FROM visions")
for r in c.fetchall():
    print(f"  {r[0]} ({r[1]})")

print("\n=== WEEKLY REVIEWS ===")
c.execute("SELECT completed_at, notes[:80] FROM weekly_review_completions ORDER BY completed_at DESC")
for r in c.fetchall():
    print(f"  {r[0]}: {r[1]}")

print("\n=== NEXT ACTIONS (is_next_action=1, not completed) ===")
c.execute("""
    SELECT t.title, t.status, t.context, p.title 
    FROM tasks t JOIN projects p ON t.project_id = p.id 
    WHERE t.is_next_action = 1 AND t.status != 'completed'
    ORDER BY t.priority
""")
for r in c.fetchall():
    print(f"  {r[0]} [{r[1]}] @{r[2]} -- {r[3]}")

conn.close()
print("\n✓ Verification complete!")
