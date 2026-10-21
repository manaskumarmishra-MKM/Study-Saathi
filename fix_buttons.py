f = open('frontend/digital-library/active-session.html', 'r')
lines = f.readlines()
f.close()

# Line 456 (index 455): Add id="reset-btn" to first button
lines[455] = lines[455].replace('<button>', '<button id="reset-btn">')

# Line 461 (index 460): Add id="start-btn" to second button
lines[460] = lines[460].replace('<button>', '<button id="start-btn">')

# Line 467 (index 466): Change pause to play_arrow
lines[466] = lines[466].replace('>pause</span', '>play_arrow</span')

# Line 470 (index 469): Replace entire line with pause-btn including hidden class
lines[469] = '<button id="pause-btn" class="w-12 h-12 rounded-full flex items-center justify-center bg-surface-variant/50 text-on-surface-variant hover:bg-surface-variant transition-colors hidden">\n'

# Line 473 (index 472): Change skip_next to pause
lines[472] = lines[472].replace('skip_next', 'pause')

f = open('frontend/digital-library/active-session.html', 'w')
f.writelines(lines)
f.close()

import re
c = ''.join(lines)
ids = re.findall(r'id="([^"]+)"', c)
print("HTML IDs:", sorted(set(ids)))
for req_id in ['end-btn', 'session-subject', 'pomodoro-count', 'session-time', 'status-badge', 'status-dot', 'reset-btn', 'start-btn', 'pause-btn']:
    print(f"  {req_id}: {'FOUND' if req_id in ids else 'MISSING'}")