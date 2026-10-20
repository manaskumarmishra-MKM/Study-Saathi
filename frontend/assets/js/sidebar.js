/* sidebar.js — StudySaathi v3 © Manas Kumar Mishra */
function injectShell(activePage){
  const links=[
    {href:"dashboard.html",icon:"📊",label:"Dashboard"},
    {href:"subjects.html",icon:"📚",label:"Subjects"},
    {href:"syllabus.html",icon:"📋",label:"Syllabus",badge:"new"},
    {href:"planner.html",icon:"📅",label:"Planner"},
    {href:"pyq.html",icon:"📝",label:"PYQ Bank"},
    {href:"mocktest.html",icon:"🧪",label:"Mock Tests"},
    {href:"analytics.html",icon:"📈",label:"Analytics"},
    {href:"resources.html",icon:"📦",label:"Resources",badge:"new"},
    {href:"chatbot.html",icon:"🤖",label:"AI Assistant"},
    {href:"digital-library/index.html",icon:"🏛️",label:"Digital Library",badge:"new"},
  ];
  const sbHTML=`
    <div class="sb-section">Main</div>
    ${links.map(l=>`<a class="sb-item ${l.href===activePage?"active":""}" href="${l.href}"><span class="si">${l.icon}</span>${l.label}${l.badge?`<span class="sb-new">${l.badge}</span>`:""}</a>`).join("")}
    <div class="sb-div"></div>
    <div class="sb-section">Account</div>
    <a class="sb-item ${activePage==="profile.html"?"active":""}" href="profile.html"><span class="si">👤</span> Profile</a>
    <a class="sb-item" onclick="logout()" style="cursor:pointer"><span class="si">🚪</span> Logout</a>
  `;
  const tbHTML=`
    <div style="display:flex;align-items:center;gap:12px">
      <button class="hamburger" id="hamburger"><span></span><span></span><span></span></button>
      <div class="topbar-brand"><div class="brand-mark">✦</div>StudySaathi <span class="brand-v3">v3</span></div>
    </div>
    <div class="topbar-search" style="position:relative">
      <span class="s-icon" style="position:absolute;left:13px;top:50%;transform:translateY(-50%);color:var(--text3);pointer-events:none">🔍</span>
      <input type="text" id="search-inp" placeholder="Search subjects, PYQs, tests…">
      <div id="search-results"></div>
    </div>
    <div class="topbar-actions">
      <div class="dropdown">
        <button class="tb-btn dd-toggle" id="notif-btn" title="Notifications">🔔<span class="tb-dot"></span></button>
        <div class="notif-panel dd-menu" id="notif-panel"></div>
      </div>
      <button class="tb-btn" id="theme-toggle" title="Toggle theme">🌙</button>
      <div class="dropdown">
        <div class="avatar dd-toggle" id="nav-avatar2">U</div>
        <div class="dd-menu">
          <div class="dd-item"><span>👤</span><span id="nav-user-name">User</span></div>
          <div class="dd-item" onclick="location.href='profile.html'"><span>⚙️</span> Profile</div>
          <div class="dd-item danger" onclick="logout()"><span>🚪</span> Logout</div>
        </div>
      </div>
    </div>
  `;
  const fabHTML=`
    <button class="chat-fab">🤖</button>
    <div class="chat-panel">
      <div class="chat-ph"><div class="bot-av">🤖</div><div><div class="bot-name">StudySaathi AI</div><div class="bot-status">● Online</div></div><button class="chat-close">✕</button></div>
      <div class="chat-msgs" id="chat-fab-msgs"><div class="msg bot"><div class="msg-av">🤖</div><div class="msg-bub">Hi! Ask me about your exam prep 📚</div></div></div>
      <div class="chat-foot"><input class="chat-inp" id="chat-fab-inp" placeholder="Ask anything…"><button class="chat-send">➤</button></div>
    </div>
    <div id="toast-container"></div>
  `;
  const tb=document.querySelector(".topbar");if(tb)tb.innerHTML=tbHTML;
  const sb=document.querySelector(".sidebar");if(sb)sb.innerHTML=sbHTML;
  document.body.insertAdjacentHTML("beforeend",fabHTML);
}
