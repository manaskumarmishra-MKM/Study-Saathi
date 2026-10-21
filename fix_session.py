f = open('frontend/digital-library/active-session.html', 'r')
c = f.read()
f.close()

# 1. Add id="end-btn" to the End Session button
c = c.replace(
    'class="w-full py-3 px-4 rounded-xl font-label-sm text-label-sm bg-surface-variant text-error hover:bg-error-container hover:text-on-error-container transition-colors duration-200 border border-error/20 flex items-center justify-center gap-2"',
    'id="end-btn" class="w-full py-3 px-4 rounded-xl font-label-sm text-label-sm bg-surface-variant text-error hover:bg-error-container hover:text-on-error-container transition-colors duration-200 border border-error/20 flex items-center justify-center gap-2"'
)

# 2. Add id to pomodoro count
c = c.replace(
    '>2 Pomodoros</span',
    'id="pomodoro-count" class="font-body-md text-on-background font-medium">0 Pomodoros</span'
)

# 3. Add id to session time
c = c.replace(
    '>1h 40m</span',
    'id="session-time" class="font-body-md text-on-background font-medium">0m 0s</span'
)

# 4. Add subject select before the CTA comment
c = c.replace(
    '<!-- CTA -->',
    '<select id="session-subject" class="w-full bg-surface-container-lowest text-on-surface border border-outline-variant/30 rounded-lg px-4 py-3 mb-4 focus:border-primary focus:outline-none"><option value="">Select Subject</option></select>\n        <!-- CTA -->'
)

# 5. Add status badge and dot after timer display
c = c.replace(
    'id="timer-display"',
    'id="timer-display"\n                <div class="flex items-center gap-2 mt-2">\n                    <span id="status-badge" class="text-xs font-semibold px-2 py-1 rounded bg-surface-variant text-on-surface-variant">IDLE</span>\n                    <span id="status-dot" class="w-2 h-2 rounded-full bg-text2"></span>\n                </div>'
)

# 6. Add IDs to control buttons
c = c.replace(
    'class="w-12 h-12 rounded-full flex items-center justify-center bg-surface-variant/50 text-on-surface-variant hover:bg-surface-variant transition-colors"\n              >\n              <span class="material-symbols-outlined">restart_alt</span>',
    'id="reset-btn" class="w-12 h-12 rounded-full flex items-center justify-center bg-surface-variant/50 text-on-surface-variant hover:bg-surface-variant transition-colors"\n              >\n              <span class="material-symbols-outlined">restart_alt</span>'
)
c = c.replace(
    'class="w-16 h-16 rounded-full flex items-center justify-center bg-primary-container text-on-primary-container shadow-lg hover:scale-105 transition-transform border border-primary/20"\n              >\n              <span\n                class="material-symbols-outlined text-3xl"\n                style="font-variation-settings: &quot;FILL&quot; 1"\n                >pause</span',
    'id="start-btn" class="w-16 h-16 rounded-full flex items-center justify-center bg-primary-container text-on-primary-container shadow-lg hover:scale-105 transition-transform border border-primary/20"\n              >\n              <span\n                class="material-symbols-outlined text-3xl"\n                style="font-variation-settings: &quot;FILL&quot; 1"\n                >play_arrow</span'
)
c = c.replace(
    'class="w-12 h-12 rounded-full flex items-center justify-center bg-surface-variant/50 text-on-surface-variant hover:bg-surface-variant transition-colors"\n              >\n              <span class="material-symbols-outlined">skip_next</span>',
    'id="pause-btn" class="w-12 h-12 rounded-full flex items-center justify-center bg-surface-variant/50 text-on-surface-variant hover:bg-surface-variant transition-colors hidden"\n              >\n              <span class="material-symbols-outlined">pause</span>'
)

f = open('frontend/digital-library/active-session.html', 'w')
f.write(c)
f.close()

import re
ids = re.findall(r'id="([^"]+)"', c)
print("HTML IDs:", sorted(set(ids)))
for req_id in ['end-btn', 'session-subject', 'pomodoro-count', 'session-time', 'status-badge', 'status-dot', 'reset-btn', 'start-btn', 'pause-btn']:
    print(f"  {req_id}: {'FOUND' if req_id in ids else 'MISSING'}")