from pathlib import Path

# Update signup.html
p = Path('signup.html')
t = p.read_text(encoding='utf-8')
old = '\t<script src="./script.js"></script>\n</body>'
new = '\t<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./script.js"></script>\n</body>'
if old in t:
    p.write_text(t.replace(old, new), encoding='utf-8')
    print('✓ Navbar script added to signup.html')
else:
    print('✗ Pattern not found in signup.html')

# Update all other main pages
pages = ['index.html', 'learn.html', 'words.html', 'quiz.html', 'translate.html', 'progress.html']
for page in pages:
    if not Path(page).exists():
        print(f'✗ {page} not found')
        continue
    p = Path(page)
    t = p.read_text(encoding='utf-8')
    # Try to add before closing body tag
    if '</body>' in t and 'navbar-auth.js' not in t:
        old_body = '</body>'
        new_body = '\t<script src="./assets/js/navbar-auth.js"></script>\n</body>'
        t = t.replace(old_body, new_body)
        p.write_text(t, encoding='utf-8')
        print(f'✓ Navbar script added to {page}')
    else:
        print(f'✗ Skipped {page} (already has script or no body tag)')
