"""Add attachments column to issues table and fix upload path format."""
from database import run_query

# Add attachments column (JSON array of file paths)
try:
    run_query("ALTER TABLE issues ADD COLUMN IF NOT EXISTS attachments TEXT DEFAULT NULL", commit=True)
    print("Added attachments column to issues table")
except Exception as e:
    print(f"Column: {e}")

print("Done!")
