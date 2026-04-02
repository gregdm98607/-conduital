"""
Populate Conduital with fresh, realistic demo data for screenshots.
Uses April 2026 dates to look current.
"""
import sqlite3
import json
import random
from datetime import datetime, timedelta, date

DB_PATH = r'C:\Users\gregm\AppData\Local\Conduital\tracker.db'

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ============================================================
# STEP 1: Clear existing data (order matters for FK constraints)
# ============================================================
tables_to_clear = [
    'momentum_snapshots',
    'activity_log',
    'weekly_review_completions',
    'inbox',
    'tasks',
    'project_phases',
    'projects',
    'areas',
    'goals',
    'visions',
    'contexts',
    'phase_templates',
    'memory_objects',
    'memory_namespaces',
    'memory_index',
    'prefetch_rules',
    'sync_state',
]

for t in tables_to_clear:
    try:
        cursor.execute(f"DELETE FROM [{t}]")
        print(f"Cleared {t}")
    except Exception as e:
        print(f"Could not clear {t}: {e}")

# Reset autoincrement counters
try:
    cursor.execute("DELETE FROM sqlite_sequence WHERE 1=1")
except:
    pass

# ============================================================
# STEP 2: Contexts (GTD-style)
# ============================================================
contexts = [
    (1, 'work', 'location', 'Tasks for the office or professional context', 'briefcase'),
    (2, 'home', 'location', 'Tasks to do at home', 'home'),
    (3, 'computer', 'tool', 'Tasks requiring a computer', 'monitor'),
    (4, 'phone', 'tool', 'Calls and phone-based tasks', 'phone'),
    (5, 'errands', 'location', 'Tasks requiring going out', 'shopping-cart'),
    (6, 'focus', 'energy', 'Deep work requiring concentration', 'target'),
]
now_str = '2026-04-01 09:00:00'
for c in contexts:
    cursor.execute("""
        INSERT INTO contexts (id, name, context_type, description, icon, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (c[0], c[1], c[2], c[3], c[4], now_str, now_str))
print("Inserted contexts")

# ============================================================
# STEP 3: Areas of Responsibility
# ============================================================
areas = [
    (1, 'Product Development', 'Oversee product strategy, roadmap, and feature delivery for the Conduital app.',
     None, 'Ship high-quality features on time with minimal bugs. Maintain a clear roadmap that aligns with user needs and business goals.',
     'weekly', 0.82, False),
    (2, 'Marketing & Growth', 'Drive user acquisition, content marketing, and brand awareness.',
     None, 'Consistently grow MRR by 15% month-over-month. Produce content that ranks and converts.',
     'weekly', 0.65, False),
    (3, 'Finance & Operations', 'Manage budgets, invoicing, subscriptions, and operational processes.',
     None, 'Keep burn rate sustainable. Ensure all invoices paid within 30 days. Monthly financial review completed on time.',
     'monthly', 0.71, False),
    (4, 'Health & Fitness', 'Maintain physical health through exercise, nutrition, and sleep habits.',
     None, 'Exercise 4x per week. Maintain consistent sleep schedule. Annual physical completed.',
     'weekly', 0.58, False),
    (5, 'Learning & Development', 'Continuous improvement through reading, courses, and skill-building.',
     None, 'Complete one book per month. Finish at least one professional development course per quarter.',
     'monthly', 0.45, False),
    (6, 'Relationships', 'Nurture personal and professional relationships.',
     None, 'Weekly check-ins with close friends/family. Attend at least 2 networking events per month.',
     'weekly', 0.60, False),
]

base_date = datetime(2026, 1, 15, 10, 0, 0)
for a in areas:
    created = (base_date + timedelta(days=random.randint(0, 10))).strftime('%Y-%m-%d %H:%M:%S')
    updated = '2026-03-31 14:30:00'
    reviewed = '2026-03-28 09:00:00'
    cursor.execute("""
        INSERT INTO areas (id, title, description, folder_path, standard_of_excellence, 
                          review_frequency, created_at, updated_at, last_reviewed_at,
                          user_id, health_score, is_archived, archived_at, deleted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, NULL, NULL)
    """, (a[0], a[1], a[2], a[3], a[4], a[5], created, updated, reviewed, a[6], a[7]))
print("Inserted areas")

# ============================================================
# STEP 4: Goals & Visions
# ============================================================
goals = [
    (1, 'Launch Conduital v2.0', 'Ship the major v2.0 release with AI-powered weekly reviews, momentum tracking, and calendar integration.', 
     '1-3_years', '2026-06-30', 'active', None),
    (2, 'Reach 1,000 paying users', 'Grow the subscriber base to 1,000 active paying users through organic marketing and product-led growth.',
     '1-3_years', '2026-12-31', 'active', None),
    (3, 'Complete half-marathon', 'Train for and complete a half-marathon by fall 2026.',
     '1-3_years', '2026-10-15', 'active', None),
    (4, 'Read 12 books this year', 'One book per month across business, fiction, and personal development.',
     '1-3_years', '2026-12-31', 'active', None),
]

for g in goals:
    created = '2026-01-05 10:00:00'
    cursor.execute("""
        INSERT INTO goals (id, title, description, timeframe, target_date, status, completed_at, created_at, updated_at, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
    """, (g[0], g[1], g[2], g[3], g[4], g[5], g[6], created, '2026-03-31 10:00:00'))
print("Inserted goals")

visions = [
    (1, 'Build the best GTD app', 'Conduital becomes the go-to productivity system for knowledge workers who want structure without rigidity. A profitable, sustainable SaaS business.', '3-5_years'),
    (2, 'Financial independence', 'Achieve enough passive and business income to have full autonomy over how I spend my time.', '5+_years'),
]
for v in visions:
    cursor.execute("""
        INSERT INTO visions (id, title, description, timeframe, created_at, updated_at, user_id)
        VALUES (?, ?, ?, ?, ?, ?, NULL)
    """, (v[0], v[1], v[2], v[3], '2026-01-05 10:00:00', '2026-03-31 10:00:00'))
print("Inserted visions")

# ============================================================
# STEP 5: Projects (mix of active, someday/maybe, completed)
# ============================================================
projects = [
    # Active projects
    (1, 'Conduital v2.0 Release', 'Major release with AI weekly reviews, momentum dashboard, and calendar sync. Target: June 2026.', 
     'active', 1, None, 1, None, 1, 0.87, '2026-03-31 22:15:00', None, None, '2026-06-30',
     'A polished v2.0 release that delights users and drives upgrades.', 'weekly'),
    
    (2, 'Content Marketing Campaign', 'Create a series of blog posts, comparison guides, and YouTube videos about GTD methodology and how Conduital implements it.',
     'active', 2, None, 2, None, 2, 0.72, '2026-03-30 16:00:00', None, None, '2026-05-15',
     'Published content that drives organic traffic and positions Conduital as a thought leader.', 'weekly'),
    
    (3, 'User Onboarding Redesign', 'Redesign the first-run experience with guided setup, sample data, and interactive tutorials.',
     'active', 1, None, 2, None, 1, 0.65, '2026-03-29 11:00:00', None, None, '2026-04-30',
     'New users reach their aha moment within 5 minutes of signing up.', 'weekly'),
    
    (4, 'Q2 Financial Review', 'Prepare Q1 financials, update projections, review subscription metrics and churn.',
     'active', 3, None, None, None, 2, 0.54, '2026-03-28 09:30:00', None, None, '2026-04-15',
     'Clear financial picture with actionable insights for Q2 planning.', 'weekly'),
    
    (5, 'Half-Marathon Training Plan', 'Follow a 16-week training plan for the October half-marathon. Currently in week 6.',
     'active', 4, None, 3, None, 3, 0.78, '2026-03-31 06:30:00', None, None, '2026-10-15',
     'Complete the half-marathon in under 2 hours.', 'weekly'),
    
    (6, 'API Integration Layer', 'Build REST API endpoints for third-party integrations (Todoist import, Notion sync, Google Calendar).',
     'active', 1, None, 1, None, 2, 0.61, '2026-03-27 14:00:00', None, None, '2026-05-31',
     'Working API that enables key integrations and opens the platform.', 'weekly'),
    
    (7, 'Networking & Community Building', 'Attend local tech meetups, engage in online communities, build relationships with potential partners.',
     'active', 6, None, None, None, 3, 0.43, '2026-03-25 19:00:00', None, None, None,
     'A growing network of allies, users, and collaborators.', 'weekly'),
    
    # Someday/Maybe
    (8, 'Mobile App (iOS)', 'Native iOS companion app for capture and quick review on the go.',
     'someday_maybe', 1, None, 1, None, 4, 0.20, '2026-02-15 10:00:00', None, None, None,
     'A polished iOS app that syncs seamlessly with the desktop version.', 'monthly'),
    
    (9, 'Podcast Launch', 'Start a podcast about personal productivity, GTD, and building in public.',
     'someday_maybe', 2, None, None, None, 5, 0.15, '2026-02-01 10:00:00', None, None, None,
     'A weekly podcast with growing listenership.', 'monthly'),
    
    (10, 'Home Office Renovation', 'Redesign the home office for better ergonomics and video recording setup.',
     'someday_maybe', 4, None, None, None, 4, 0.10, '2026-01-20 10:00:00', None, None, None,
     'An inspiring, functional workspace.', 'monthly'),
    
    # Completed projects
    (11, 'Conduital v1.5 Launch', 'Shipped momentum tracking, area health scores, and inbox processing.',
     'completed', 1, None, 1, None, 1, 0.95, '2026-02-28 18:00:00', '2026-02-28 18:00:00', None, '2026-02-28',
     'Successful release with positive user feedback.', 'weekly'),
    
    (12, 'Tax Preparation 2025', 'Gather documents, meet with accountant, file federal and state returns.',
     'completed', 3, None, None, None, 2, 0.92, '2026-03-15 14:00:00', '2026-03-15 14:00:00', None, '2026-03-15',
     'Taxes filed accurately and on time.', 'monthly'),
    
    (13, 'Reading: "Four Thousand Weeks"', 'Read and take notes on Oliver Burkeman\'s book about time management philosophy.',
     'completed', 5, None, 4, None, 3, 0.88, '2026-03-10 21:00:00', '2026-03-10 21:00:00', None, '2026-03-10',
     'Finished with key takeaways documented.', 'monthly'),
]

for p in projects:
    created_offset = random.randint(0, 30)
    created = (datetime(2026, 1, 10) + timedelta(days=created_offset)).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO projects (id, title, description, status, area_id, phase_template_id, goal_id, vision_id,
                             priority, momentum_score, last_activity_at, completed_at, stalled_since,
                             target_completion_date, file_path, file_hash, created_at, updated_at,
                             outcome_statement, user_id, next_review_date, last_reviewed_at,
                             purpose, vision_statement, brainstorm_notes, organizing_notes,
                             previous_momentum_score, review_frequency, deleted_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?, ?, NULL, ?, ?, NULL, NULL, NULL, NULL, ?, ?, NULL)
    """, (p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8], p[9], p[10], p[11], p[12], p[13],
          created, '2026-03-31 20:00:00', p[14], '2026-04-04', '2026-03-28 09:00:00',
          round(p[9] - random.uniform(0.05, 0.15), 2), p[15]))
print("Inserted projects")

# ============================================================
# STEP 6: Tasks â€” lots of variety
# ============================================================
task_id = 0

def add_task(title, desc, status, task_type, project_id, due_date=None, context=None, 
             energy=None, priority=3, is_next=False, is_two_min=False, estimated_min=None,
             waiting_for=None, urgency='opportunity_now', started_at=None, completed_at=None):
    global task_id
    task_id += 1
    created = (datetime(2026, 3, 1) + timedelta(days=random.randint(0, 25), hours=random.randint(8, 20))).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO tasks (id, title, description, status, task_type, project_id, parent_task_id, phase_id,
                          sequence_order, due_date, defer_until, estimated_minutes, actual_minutes,
                          context, energy_level, location, priority, is_next_action, is_two_minute_task,
                          is_unstuck_task, started_at, completed_at, waiting_for, resource_requirements,
                          file_line_number, file_marker, created_at, updated_at, urgency_zone, deleted_at)
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, NULL, ?, NULL, ?, NULL, ?, ?, NULL, ?, ?, ?, 0, ?, ?, ?, NULL, NULL, NULL, ?, ?, ?, NULL)
    """, (task_id, title, desc, status, task_type, project_id, due_date, estimated_min,
          context, energy, priority, 1 if is_next else 0, 1 if is_two_min else 0,
          started_at, completed_at, waiting_for, created, '2026-03-31 20:00:00', urgency))

# === Project 1: Conduital v2.0 Release ===
add_task('Finalize AI weekly review prompt engineering', 'Test and refine the prompts used for AI-generated weekly review summaries.', 
         'in_progress', 'action', 1, '2026-04-05', 'computer', 'high', 1, True, False, 120,
         started_at='2026-03-31 10:00:00')
add_task('Build momentum trend chart component', 'React component showing 30-day momentum trend with sparkline.',
         'todo', 'action', 1, '2026-04-08', 'computer', 'high', 2, True, False, 180)
add_task('Write migration script for v2.0 schema changes', None,
         'completed', 'action', 1, '2026-03-28', 'computer', 'high', 1, False, False, 60,
         completed_at='2026-03-28 16:30:00')
add_task('Design calendar sync settings UI', 'Mockup the settings panel for Google Calendar integration.',
         'todo', 'action', 1, '2026-04-10', 'computer', 'medium', 2, False, False, 90)
add_task('Set up beta testing group', 'Recruit 20 beta testers from existing users and set up feedback channel.',
         'in_progress', 'action', 1, '2026-04-07', 'computer', 'medium', 2, True, False, 45,
         started_at='2026-03-30 14:00:00')
add_task('Update API documentation for v2.0 endpoints', None,
         'todo', 'action', 1, '2026-04-15', 'computer', 'medium', 3, False, False, 120)
add_task('Fix timezone handling in recurring task scheduler', 'Bug: tasks created in PST show wrong time in UTC display.',
         'completed', 'action', 1, '2026-03-25', 'computer', 'high', 1, False, False, 90,
         completed_at='2026-03-25 17:45:00')
add_task('Performance audit on dashboard load time', 'Profile and optimize the main dashboard â€” target < 500ms.',
         'todo', 'action', 1, '2026-04-12', 'computer', 'high', 2, False, False, 180)

# === Project 2: Content Marketing Campaign ===
add_task('Write blog post: "GTD in 2026: What Still Works"', 'Long-form post comparing traditional GTD with modern adaptations.',
         'in_progress', 'action', 2, '2026-04-04', 'computer', 'high', 1, True, False, 180,
         started_at='2026-03-30 09:00:00')
add_task('Create comparison chart: Conduital vs Todoist vs Things 3', None,
         'todo', 'action', 2, '2026-04-08', 'computer', 'medium', 2, True, False, 120)
add_task('Film intro video for YouTube channel', 'Script, film, and edit a 3-minute intro video.',
         'todo', 'action', 2, '2026-04-12', 'home', 'high', 3, False, False, 240)
add_task('Set up ConvertKit email sequence', '5-email welcome sequence for new subscribers.',
         'completed', 'action', 2, '2026-03-20', 'computer', 'medium', 2, False, False, 120,
         completed_at='2026-03-20 15:00:00')
add_task('Research SEO keywords for productivity niche', None,
         'completed', 'action', 2, '2026-03-15', 'computer', 'low', 3, False, False, 60,
         completed_at='2026-03-16 11:00:00')
add_task('Draft Twitter thread on weekly review benefits', None,
         'todo', 'action', 2, '2026-04-06', 'phone', 'low', 3, False, True, 15)

# === Project 3: User Onboarding Redesign ===
add_task('Map current onboarding funnel with drop-off points', 'Analyze analytics to find where new users abandon setup.',
         'completed', 'action', 3, '2026-03-22', 'computer', 'high', 1, False, False, 90,
         completed_at='2026-03-22 14:00:00')
add_task('Design interactive tutorial wireframes', 'Figma mockups for the step-by-step guided setup.',
         'in_progress', 'action', 3, '2026-04-03', 'computer', 'high', 1, True, False, 180,
         started_at='2026-03-29 10:00:00')
add_task('Build sample project template for new users', 'Pre-populated "Getting Started" project with example tasks.',
         'todo', 'action', 3, '2026-04-08', 'computer', 'medium', 2, True, False, 60)
add_task('Write onboarding tooltip copy', '12 contextual tooltips explaining key features.',
         'todo', 'action', 3, '2026-04-10', 'computer', 'low', 3, False, False, 45)
add_task('A/B test new vs old onboarding flow', None,
         'todo', 'action', 3, '2026-04-20', 'computer', 'medium', 2, False, False, 120)

# === Project 4: Q2 Financial Review ===
add_task('Export Q1 revenue data from Stripe', None,
         'completed', 'action', 4, '2026-03-31', 'computer', 'low', 2, False, True, 10,
         completed_at='2026-03-31 10:15:00')
add_task('Compile monthly expense report', 'Gather receipts and categorize Q1 expenses.',
         'in_progress', 'action', 4, '2026-04-05', 'computer', 'medium', 1, True, False, 90,
         started_at='2026-03-31 11:00:00')
add_task('Calculate churn rate and LTV metrics', None,
         'todo', 'action', 4, '2026-04-08', 'computer', 'high', 2, True, False, 60)
add_task('Update Q2 budget projections', None,
         'todo', 'action', 4, '2026-04-12', 'computer', 'medium', 2, False, False, 45)
add_task('Schedule meeting with accountant', None,
         'todo', 'action', 4, '2026-04-10', 'phone', 'low', 3, False, True, 10)

# === Project 5: Half-Marathon Training ===
add_task('Complete Week 7 long run (8 miles)', None,
         'todo', 'action', 5, '2026-04-05', None, 'high', 1, True, False, 90)
add_task('3-mile recovery run', None,
         'completed', 'action', 5, '2026-03-31', None, 'medium', 2, False, False, 30,
         completed_at='2026-03-31 07:00:00')
add_task('Buy new running shoes', 'Current pair at 400 miles â€” time to replace.',
         'todo', 'action', 5, '2026-04-06', 'errands', 'low', 2, True, False, 45)
add_task('Research race-day nutrition strategy', None,
         'todo', 'action', 5, '2026-04-15', 'computer', 'low', 4, False, False, 30)
add_task('Register for October half-marathon', 'Early bird registration closes April 20.',
         'todo', 'action', 5, '2026-04-18', 'computer', 'low', 2, False, True, 10,
         urgency='critical_now')

# === Project 6: API Integration Layer ===
add_task('Define OpenAPI spec for task endpoints', None,
         'completed', 'action', 6, '2026-03-20', 'computer', 'high', 1, False, False, 120,
         completed_at='2026-03-20 16:00:00')
add_task('Implement Todoist CSV import parser', 'Parse Todoist export format and map to Conduital schema.',
         'in_progress', 'action', 6, '2026-04-05', 'computer', 'high', 1, True, False, 180,
         started_at='2026-03-28 10:00:00')
add_task('Build Google Calendar OAuth flow', None,
         'todo', 'action', 6, '2026-04-12', 'computer', 'high', 2, True, False, 240)
add_task('Write API rate limiting middleware', None,
         'todo', 'action', 6, '2026-04-15', 'computer', 'medium', 3, False, False, 90)
add_task('Create webhook endpoint for external notifications', None,
         'todo', 'action', 6, '2026-04-20', 'computer', 'medium', 3, False, False, 120)

# === Project 7: Networking ===
add_task('Attend April Tech Meetup', 'Local startup meetup on April 10th.',
         'todo', 'action', 7, '2026-04-10', 'errands', 'medium', 2, True, False, 180)
add_task('Follow up with contacts from March meetup', 'Send LinkedIn messages to 5 people met at the event.',
         'todo', 'action', 7, '2026-04-03', 'computer', 'low', 3, True, False, 30)
add_task('Reply to community forum questions', 'Check and respond to Conduital community posts.',
         'todo', 'action', 7, '2026-04-02', 'computer', 'low', 3, False, True, 15)
add_task('Coffee chat with Sarah from ProductHunt', None,
         'waiting', 'action', 7, '2026-04-08', 'errands', 'low', 3, False, False, 60,
         waiting_for='Waiting for Sarah to confirm time')

# === Completed Project 11: v1.5 (a few done tasks) ===
add_task('Ship momentum tracking feature', None,
         'completed', 'action', 11, '2026-02-25', 'computer', 'high', 1, False, False, 480,
         completed_at='2026-02-25 18:00:00')
add_task('Write v1.5 release notes', None,
         'completed', 'action', 11, '2026-02-28', 'computer', 'medium', 2, False, False, 45,
         completed_at='2026-02-28 12:00:00')
add_task('Deploy v1.5 to production', None,
         'completed', 'action', 11, '2026-02-28', 'computer', 'high', 1, False, False, 30,
         completed_at='2026-02-28 17:30:00')

# === Completed Project 12: Tax Prep ===
add_task('Gather W-2 and 1099 forms', None,
         'completed', 'action', 12, '2026-02-15', 'home', 'low', 2, False, False, 30,
         completed_at='2026-02-14 10:00:00')
add_task('Meet with accountant', None,
         'completed', 'action', 12, '2026-03-10', 'errands', 'medium', 1, False, False, 60,
         completed_at='2026-03-10 11:00:00')
add_task('Review and sign returns', None,
         'completed', 'action', 12, '2026-03-15', 'computer', 'medium', 1, False, False, 20,
         completed_at='2026-03-15 14:00:00')

print(f"Inserted {task_id} tasks")

# ============================================================
# STEP 7: Inbox items (mix of processed and unprocessed)
# ============================================================
inbox_items = [
    # Unprocessed (recent captures)
    ('Look into Resend for transactional emails â€” recommended by Jake', '2026-04-01 08:30:00', None, 'manual', None, None),
    ('Idea: add keyboard shortcuts cheat sheet to onboarding', '2026-04-01 07:15:00', None, 'manual', None, None),
    ('Check if annual domain renewal went through', '2026-03-31 22:00:00', None, 'manual', None, None),
    ('Book dentist appointment', '2026-03-31 18:30:00', None, 'manual', None, None),
    ('Article to read: "The Unreasonable Effectiveness of Checklists"', '2026-03-31 12:00:00', None, 'manual', None, None),
    # Processed
    ('Review pull request from contractor', '2026-03-28 09:00:00', '2026-03-28 10:30:00', 'manual', 'task', 1),
    ('Update privacy policy for GDPR compliance', '2026-03-27 14:00:00', '2026-03-28 09:00:00', 'manual', 'task', 6),
    ('Respond to feature request email from beta user', '2026-03-26 11:00:00', '2026-03-26 14:00:00', 'manual', 'task', 1),
    ('Buy birthday gift for Mom', '2026-03-25 08:00:00', '2026-03-25 08:15:00', 'manual', 'task', None),
    ('Schedule car maintenance', '2026-03-24 17:00:00', '2026-03-25 09:00:00', 'manual', 'task', None),
]

for i, item in enumerate(inbox_items, 1):
    cursor.execute("""
        INSERT INTO inbox (id, content, captured_at, processed_at, source, result_type, result_id, user_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
    """, (i, item[0], item[1], item[2], item[3], item[4], item[5], item[1], item[1]))
print("Inserted inbox items")

# ============================================================
# STEP 8: Activity Log (recent activity for the dashboard)
# ============================================================
activities = []
act_id = 0

def add_activity(entity_type, entity_id, action, details, timestamp, source='app'):
    global act_id
    act_id += 1
    activities.append((act_id, entity_type, entity_id, action, details, timestamp, source))

# Recent task completions
add_activity('task', 3, 'status_changed', '{"from": "in_progress", "to": "completed"}', '2026-03-28 16:30:00')
add_activity('task', 7, 'status_changed', '{"from": "in_progress", "to": "completed"}', '2026-03-25 17:45:00')
add_activity('task', 12, 'status_changed', '{"from": "todo", "to": "completed"}', '2026-03-20 15:00:00')
add_activity('task', 13, 'status_changed', '{"from": "todo", "to": "completed"}', '2026-03-16 11:00:00')
add_activity('task', 22, 'status_changed', '{"from": "in_progress", "to": "completed"}', '2026-03-31 10:15:00')
add_activity('task', 28, 'status_changed', '{"from": "todo", "to": "completed"}', '2026-03-31 07:00:00')
add_activity('task', 33, 'status_changed', '{"from": "in_progress", "to": "completed"}', '2026-03-20 16:00:00')

# Task starts
add_activity('task', 1, 'status_changed', '{"from": "todo", "to": "in_progress"}', '2026-03-31 10:00:00')
add_activity('task', 9, 'status_changed', '{"from": "todo", "to": "in_progress"}', '2026-03-30 09:00:00')
add_activity('task', 17, 'status_changed', '{"from": "todo", "to": "in_progress"}', '2026-03-29 10:00:00')
add_activity('task', 23, 'status_changed', '{"from": "todo", "to": "in_progress"}', '2026-03-31 11:00:00')
add_activity('task', 34, 'status_changed', '{"from": "todo", "to": "in_progress"}', '2026-03-28 10:00:00')

# Project updates
add_activity('project', 11, 'status_changed', '{"from": "active", "to": "completed"}', '2026-02-28 18:00:00')
add_activity('project', 12, 'status_changed', '{"from": "active", "to": "completed"}', '2026-03-15 14:00:00')
add_activity('project', 13, 'status_changed', '{"from": "active", "to": "completed"}', '2026-03-10 21:00:00')

# Inbox processing
add_activity('inbox', 6, 'processed', '{"result_type": "task"}', '2026-03-28 10:30:00')
add_activity('inbox', 7, 'processed', '{"result_type": "task"}', '2026-03-28 09:00:00')
add_activity('inbox', 8, 'processed', '{"result_type": "task"}', '2026-03-26 14:00:00')

# Weekly review
add_activity('weekly_review', 1, 'completed', '{"duration_minutes": 35}', '2026-03-28 10:00:00')

# Area reviews
add_activity('area', 1, 'reviewed', '{"health_score": 0.82}', '2026-03-28 09:15:00')
add_activity('area', 2, 'reviewed', '{"health_score": 0.65}', '2026-03-28 09:20:00')

# More recent daily activity
for day_offset in range(7):
    dt = datetime(2026, 3, 25) + timedelta(days=day_offset)
    # A few random task creations per day
    for _ in range(random.randint(1, 3)):
        hour = random.randint(8, 20)
        ts = dt.replace(hour=hour, minute=random.randint(0, 59)).strftime('%Y-%m-%d %H:%M:%S')
        add_activity('task', random.randint(1, task_id), 'created', None, ts)

for a in activities:
    cursor.execute("""
        INSERT INTO activity_log (id, entity_type, entity_id, action_type, details, timestamp, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, a)
print(f"Inserted {act_id} activity log entries")

# ============================================================
# STEP 9: Weekly Review Completions
# ============================================================
reviews = [
    (1, None, '2026-03-28 10:00:00', 'Reviewed all areas, processed 8 inbox items, updated 3 project statuses. Momentum is strong on v2.0 and content campaign.',
     'All 6 areas reviewed. 3 projects show improving momentum. Key focus for next week: finalize AI review prompts and complete onboarding wireframes. 5 unprocessed inbox items remain.'),
    (2, None, '2026-03-21 09:30:00', 'Good week. Shipped timezone fix. Marketing content pipeline building up. Need to focus more on financial review.',
     'Completed 7 tasks across 4 projects. Momentum up on 2 projects, flat on 2. Financial review needs attention â€” moved to priority for next week.'),
    (3, None, '2026-03-14 10:15:00', 'Tax prep dominating this week. v2.0 work slowed but still on track. Started training plan.',
     'Tax preparation completed. 5 tasks done, 3 new tasks created. Half-marathon training started strong. Need to re-engage with content marketing.'),
]
for r in reviews:
    cursor.execute("""
        INSERT INTO weekly_review_completions (id, user_id, completed_at, notes, ai_summary)
        VALUES (?, ?, ?, ?, ?)
    """, r)
print("Inserted weekly reviews")

# ============================================================
# STEP 10: Momentum Snapshots (30 days of history for charts)
# ============================================================
active_project_ids = [1, 2, 3, 4, 5, 6, 7]
base_scores = {1: 0.70, 2: 0.55, 3: 0.50, 4: 0.40, 5: 0.65, 6: 0.45, 7: 0.35}

snap_id = 0
for day_offset in range(30):
    dt = datetime(2026, 3, 2) + timedelta(days=day_offset)
    for pid in active_project_ids:
        snap_id += 1
        # Gradual upward trend with some noise
        progress = day_offset / 30.0 * 0.25  # up to +0.25 over 30 days
        noise = random.uniform(-0.08, 0.08)
        score = min(0.95, max(0.05, base_scores[pid] + progress + noise))
        factors = json.dumps({
            "task_completion_rate": round(random.uniform(0.3, 0.9), 2),
            "days_since_activity": random.randint(0, 3),
            "next_action_defined": random.choice([True, True, True, False]),
            "review_current": random.choice([True, True, False])
        })
        cursor.execute("""
            INSERT INTO momentum_snapshots (id, project_id, score, factors_json, snapshot_at)
            VALUES (?, ?, ?, ?, ?)
        """, (snap_id, pid, round(score, 2), factors, dt.strftime('%Y-%m-%d 04:00:00')))

print(f"Inserted {snap_id} momentum snapshots")

# ============================================================
# Commit everything
# ============================================================
conn.commit()
conn.close()
print("\nâœ“ Demo data population complete!")

