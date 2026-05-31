from pathlib import Path

p = Path('signup.html')
t = p.read_text(encoding='utf-8')
old = '\t<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./script.js"></script>'
new = '\t<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./assets/js/api-auth.js"></script>\n\t<script src="./script.js"></script>'

if old in t:
    p.write_text(t.replace(old, new), encoding='utf-8')
    print('✓ api-auth.js added to signup.html')
else:
    print('✗ Pattern not found, trying alternative...')
    # Try without the closing </script>
    if 'navbar-auth.js' in t and 'api-auth.js' not in t:
        old2 = '<script src="./assets/js/navbar-auth.js"></script>'
        new2 = '<script src="./assets/js/navbar-auth.js"></script>\n\t<script src="./assets/js/api-auth.js"></script>'
        if old2 in t:
            p.write_text(t.replace(old2, new2), encoding='utf-8')
            print('✓ api-auth.js added to signup.html (alternative method)')
