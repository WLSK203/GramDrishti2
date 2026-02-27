import os
import re

files = [
    'sarpanch-portal.html',
    'pending-approvals.html',
    'contractors.html',
    'community-issues.html',
    'active-projects.html'
]

for f in files:
    if os.path.exists(f):
        print(f"Modifying {f}")
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Remove all badge spans
        content = re.sub(r'\s*<span class=\"(?:sp-)?nav-badge[^\"]*\"[^>]*>.*?</span>', '', content)
        
        with open(f, 'w', encoding='utf-8') as file:
            file.write(content)
print("Removed sidebar badges from html files.")
