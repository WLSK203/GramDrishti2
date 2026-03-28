import os, re

folder = 'frontend'

def process_file(fp):
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Apply Rebranding
    content = content.replace('GramSabha', 'GramDrishti')
    content = content.replace('gram_sabha', 'gram_drishti')
    content = content.replace('gram-sabha', 'gram-drishti')
    content = content.replace('GRAM_SABHA', 'GRAM_DRISHTI')
    content = content.replace('GRAM-SABHA', 'GRAM-DRISHTI')

    # Apply Supabase CDN injection
    cdn = '<script src=\"https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2\"></script>\n<script src=\"js/auth.js\"'
    content = re.sub(r'<script\s+src=[\"\']js/auth\.js[\"\']', cdn, content, count=1)

    if content != original_content:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(content)
        print('Updated:', fp)

for fn in os.listdir(folder):
    if fn.endswith('.html'):
        process_file(os.path.join(folder, fn))

for sub_path in ['js/app.js', 'js/mobile.js', 'css/styles.css', 'css/mobile.css']:
    fp = os.path.join(folder, sub_path)
    if os.path.exists(fp):
        process_file(fp)

print('Done')
