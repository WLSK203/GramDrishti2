"""Recalculate budget_summary from actual project spent data and add category column to projects."""
from database import run_query, run_query_one

# Add category column if it doesn't exist
try:
    run_query("ALTER TABLE projects ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'other'", commit=True)
    print("Added category column to projects (or already exists)")
except Exception as e:
    print(f"Category column: {e}")

# Recalculate budget_summary from project data
row = run_query_one("""
    SELECT 
        COALESCE(SUM(spent), 0) as total_spent,
        COALESCE(SUM(CASE WHEN status = 'pending_approval' THEN sanctioned ELSE 0 END), 0) as pending
    FROM projects WHERE village_id = 1
""")
print(f"Project totals: spent={row['total_spent']}, pending={row['pending']}")

run_query("""
    UPDATE budget_summary 
    SET total_spent = %s, 
        pending_approval = %s, 
        available = total_received - %s - %s,
        last_updated = NOW()
    WHERE village_id = 1
""", (row['total_spent'], row['pending'], row['total_spent'], row['pending']), commit=True)

# Verify
updated = run_query_one("SELECT * FROM budget_summary WHERE village_id = 1")
print(f"Updated budget_summary: received={updated['total_received']}, spent={updated['total_spent']}, pending={updated['pending_approval']}, available={updated['available']}")

# Show project data
projects = run_query("SELECT name, sanctioned, released, spent, status, category FROM projects WHERE village_id = 1")
for p in projects:
    print(f"  Project: {p['name']} | sanctioned={p['sanctioned']} released={p['released']} spent={p['spent']} status={p['status']} cat={p['category']}")

print("Done!")
