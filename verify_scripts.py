from pathlib import Path

pages = ['index.html', 'learn.html', 'words.html', 'quiz.html', 'translate.html', 'progress.html', 'signup.html']

for page in pages:
    p = Path(page)
    if not p.exists():
        print(f'✗ {page} not found')
        continue
    
    t = p.read_text(encoding='utf-8')
    has_navbar = 'navbar-auth.js' in t
    has_api = 'api-auth.js' in t
    
    print(f'{page}: navbar-auth={"✓" if has_navbar else "✗"}, api-auth={"✓" if has_api else "✗"}')
