import os
import glob

def patch_html_files():
    html_files = glob.glob('frontend/**/*.html', recursive=True)
    count = 0
    for filepath in html_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'js/env.js' in content:
            continue # Already patched
            
        # Target variations
        replacements = [
            ('<script src="js/auth.js"></script>', '<script src="js/env.js"></script>\n    <script src="js/auth.js"></script>'),
            ('<script src="../js/auth.js"></script>', '<script src="../js/env.js"></script>\n    <script src="../js/auth.js"></script>'),
            ('<script src="./js/auth.js"></script>', '<script src="./js/env.js"></script>\n    <script src="./js/auth.js"></script>'),
        ]
        
        made_replacement = False
        for original, new_text in replacements:
            if original in content:
                content = content.replace(original, new_text)
                made_replacement = True
                break
                
        if made_replacement:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            count += 1
            print(f"Patched {filepath}")
            
    print(f"✅ Patched {count} HTML files to include env.js")

if __name__ == "__main__":
    patch_html_files()
