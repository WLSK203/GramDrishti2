import os
from database import run_query

def clear_issues():
    print("Clearing mock issues and votes database...")
    run_query("DELETE FROM issue_votes", commit=True)
    run_query("DELETE FROM issues", commit=True)
    print("Flushed old complaints!")

if __name__ == "__main__":
    clear_issues()
