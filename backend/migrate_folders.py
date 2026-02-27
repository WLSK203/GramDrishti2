import os
import shutil
import json
import re
import sys

sys.path.append('c:/Users/1wlsk/OneDrive/Desktop/Innovit2/innovit/backend')
from database import run_query

UPLOAD_DIR = "c:/Users/1wlsk/OneDrive/Desktop/Innovit2/innovit/backend/Uploaded data"
OLD_UPLOAD_DIR = "c:/Users/1wlsk/OneDrive/Desktop/Innovit2/innovit/backend/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

projects = run_query("SELECT id, name, verification_images FROM projects")

if not projects:
    print("No projects to migrate.")

for p in projects:
    pid = p['id']
    name = p['name']
    safe_name = re.sub(r'[^A-Za-z0-9]', '_', name)
    folder_name = f"Project_{pid}_{safe_name}"
    folder_path = os.path.join(UPLOAD_DIR, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    
    images = p.get('verification_images')
    if images:
        if isinstance(images, str):
            try: images = json.loads(images)
            except: images = []
            
        new_images = []
        changed = False
        for img_path in images:
            if img_path.startswith('/api/uploads/'):
                filename = img_path.replace('/api/uploads/', '')
                
                if '/' in filename:
                    new_images.append(img_path)
                    continue
                
                old_file = os.path.join(OLD_UPLOAD_DIR, filename)
                new_file = os.path.join(folder_path, filename)
                
                if os.path.exists(old_file):
                    shutil.move(old_file, new_file)
                    
                new_url = f"/api/uploads/{folder_name}/{filename}"
                new_images.append(new_url)
                changed = True
            else:
                new_images.append(img_path)
                
        if changed:
            run_query("UPDATE projects SET verification_images = %s::jsonb WHERE id = %s", (json.dumps(new_images), pid), commit=True)
            print(f"Updated images for Project {pid}")

print("Migration complete. Check Uploaded data folder.")
