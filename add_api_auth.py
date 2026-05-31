from pathlib import Path

pages = ['index.html', 'learn.html', 'words.html', 'quiz.html', 'translate.html', 'progress.html']

for page in pages:
    p = Path(page)
    if not p.exists():
        print(f'✗ {page} not found')
        continue
    
    t = p.read_text(encoding='utf-8')
    
    # Add api-auth.js if not already present
    if 'api-auth.js' not in t:
        # Find navbar-auth.js line and add api-auth.js after it
        if 'navbar-auth.js' in t:
            old = '<script src="./assets/js/navbar-auth.js"></script>'
            new = '<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./assets/js/api-auth.js"></script>'
            t = t.replace(old, new)
        else:
            # Add before closing body tag
            old = '</body>'
            new = '\t<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./assets/js/api-auth.js"></script>\n</body>'
            t = t.replace(old, new)
        
        p.write_text(t, encoding='utf-8')
        print(f'✓ API auth script added to {page}')
    else:
        print(f'✓ {page} already has API auth script')
