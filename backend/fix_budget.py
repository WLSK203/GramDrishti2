import os
import sys

# Add the parent directory to the path so we can import the database code
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection

def fix_budget():
    """Recalculates the budget summary based on actual projects."""
    print("Fixing budget math...")
    conn = get_connection()
    if not conn:
        print("Could not connect to database")
        return
        
    try:
        with conn.cursor() as cur:
            # First, check if there are any completed projects and sum their spent amount
            cur.execute("SELECT SUM(spent) as s FROM projects WHERE status = 'completed'")
            row = cur.fetchone()
            actual_spent = row['s'] if row and row['s'] is not None else 0
            
            # Now sum pending approval
            cur.execute("SELECT SUM(sanctioned) as p FROM projects WHERE status IN ('pending', 'in_progress', 'pending_approval')")
            row = cur.fetchone()
            actual_pending = row['p'] if row and row['p'] is not None else 0
            
            # Get the total received from the budget_summary table
            cur.execute("SELECT total_received FROM budget_summary LIMIT 1")
            row = cur.fetchone()
            if row:
                total_received = row['total_received']
                
                # Recalculate available base on received - spent - pending
                actual_available = total_received - actual_spent - actual_pending
                
                print(f"Total Received: {total_received}")
                print(f"Recalculated Total Spent: {actual_spent}")
                print(f"Recalculated Pending: {actual_pending}")
                print(f"Recalculated Available: {actual_available}")
                
                # Update the budget_summary table
                cur.execute(
                    "UPDATE budget_summary SET total_spent = %s, pending_approval = %s, available = %s "
                    "WHERE id IN (SELECT id FROM budget_summary LIMIT 1)",
                    (actual_spent, actual_pending, actual_available)
                )
                conn.commit()
                print("Budget mathematically corrected successfully!")
            else:
                print("No budget summary found to update.")

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    fix_budget()
