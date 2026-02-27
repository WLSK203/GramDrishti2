import os
from database import run_query

def seed_db():
    print("Seeding database...")
    
    # 1. Clear existing for village 1 (optional, for idempotency on test DB)
    run_query("DELETE FROM projects WHERE village_id = 1", commit=True)
    run_query("DELETE FROM budget_summary WHERE village_id = 1", commit=True)
    
    # 2. Add budget summary
    run_query(
        """
        INSERT INTO budget_summary (village_id, total_received, total_spent, pending_approval, available, fiscal_year)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (1, 4280000, 3000000, 825000, 455000, "FY 2024-25"),
        commit=True
    )
    print("Inserted budget summary")
    
    # 3. Add active projects
    projects = [
        (
            "PRJ-2024-1089", 1, "Water Pipeline — Ward 4", 350000, 252000, 252000,
            72, "in-progress", "Sharma Constructions", "2024-01-15", None, None,
            False, False, False, False
        ),
        (
            "PRJ-2024-0956", 1, "School Road Repair", 225000, 101250, 101250,
            45, "in-progress", "Gupta Contractors", "2024-02-01", None, None,
            False, False, False, False
        ),
        (
            "PRJ-2024-0892", 1, "School Boundary Wall", 185000, 185000, 185000,
            100, "pending_verification", "Devi Construction", "2023-11-10", "2024-02-20", "2024-02-18",
            True, True, False, False  # Partial verification
        ),
        # A new pending approval project that ties to the 825k committed
        (
            "PRJ-2024-1100", 1, "Water Pipeline — Phase 2 Payment", 85000, 0, 0,
            0, "pending_approval", "Sharma Constructions", "2024-02-25", None, None,
            False, False, False, False
        )
    ]
    
    for p in projects:
        run_query(
            """
            INSERT INTO projects (
                external_id, village_id, name, sanctioned, released, spent,
                progress, status, contractor, start_date, deadline, completed_date,
                verifications_photos, verifications_gps, verifications_community, verifications_audit
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            p,
            commit=True
        )
    print("Inserted projects")
    print("Seeding complete.")

if __name__ == "__main__":
    seed_db()
