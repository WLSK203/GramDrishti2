import os, re

folder = '.'
cdn_tag = '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>\n    '

for fn in os.listdir(folder):
    if not fn.endswith('.html'):
        continue
    fp = os.path.join(folder, fn)
    txt = open(fp, encoding='utf-8').read()
    if 'js/auth.js' in txt and 'supabase-js' not in txt:
        txt2 = re.sub(r'(<script src="js/auth\.js")', cdn_tag + r'\1', txt, count=1)
        open(fp, 'w', encoding='utf-8').write(txt2)
        print('Updated:', fn)

print('Done')
