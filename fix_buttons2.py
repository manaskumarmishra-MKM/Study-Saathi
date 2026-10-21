f = open('frontend/digital-library/active-session.html', 'r')
lines = f.readlines()
f.close()

# Line 456 (index 455): Add id="reset-btn"
lines[455] = lines[455].replace('<button>', '<button id="reset-btn">')

# Line 461 (index 460): Add id="start-btn"
lines[460] = lines[460].replace('<button>', '<button id="start-btn">')

f = open('frontend/digital-library/active-session.html', 'w')
f.writelines(lines)
f.close()

import re
c = ''.join(lines)
ids = re.findall(r'id="([^"]+)"', c)
for req_id in ['reset-btn', 'start-btn']:
    print(f"  {req_id}: {'FOUND' if req_id in ids else 'MISSING'}")