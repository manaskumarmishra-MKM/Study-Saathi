f = open('frontend/digital-library/active-session.html', 'r')
c = f.read()
f.close()

# Find and add IDs to the two remaining buttons
# Button 1: restart_alt -> reset-btn
# Button 2: play_arrow -> start-btn

import re

# Match button tags followed by restart_alt
c = re.sub(
    r'(<button\s*>\s*<span class="material-symbols-outlined">restart_alt</span>)',
    r'<button id="reset-btn">\1',
    c
)

# Match button tags followed by play_arrow  
c = re.sub(
    r'(<button\s*>\s*<span[^>]*>play_arrow</span>)',
    r'<button id="start-btn">\1',
    c
)

f = open('frontend/digital-library/active-session.html', 'w')
f.write(c)
f.close()

import re as re2
ids = re2.findall(r'id="([^"]+)"', c)
for req_id in ['reset-btn', 'start-btn']:
    print(f"  {req_id}: {'FOUND' if req_id in ids else 'MISSING'}")