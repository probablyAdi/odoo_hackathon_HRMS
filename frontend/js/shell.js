// ============================================================
// Renders the shared top navigation bar into #topbar-mount on
// every authenticated page, and wires up the avatar dropdown.
// ============================================================
function renderShell(activePage) {
  const session = Auth.requireLogin();
  const mount = document.getElementById("topbar-mount");
  if (!mount || !session) return session;

  const navItems = [
    { href: "dashboard.html", label: "Employees", key: "dashboard" },
    { href: "attendance.html", label: "Attendance", key: "attendance" },
    { href: "timeoff.html", label: "Time Off", key: "timeoff" },
  ];

  mount.innerHTML = `
    <div class="topbar">
      <div class="brand-row">
        ${session.company_logo_url 
          ? `<img src="${session.company_logo_url}" alt="Logo" style="height: 24px; width: auto; object-fit: contain; border-radius: 4px; background: var(--bg-surface);">` 
          : `<div class="brand-mark">HR</div>`}
        <span class="brand-name">${session.company_name || 'HRMS'}</span>
      </div>
      <nav>
        ${navItems.map(item => `
          <a href="${item.href}" class="${activePage === item.key ? 'active' : ''}">${item.label}</a>
        `).join("")}
      </nav>
      <div class="avatar-menu">
        <button class="avatar-btn" id="avatarBtn" title="${session.full_name}">
          ${initials(session.full_name)}
          <span class="status-dot absent" id="statusDot"></span>
        </button>
        <div class="dropdown" id="avatarDropdown">
          <a href="profile.html">My Profile</a>
          <button id="logoutBtn">Log Out</button>
        </div>
      </div>
    </div>
  `;

  const avatarBtn = document.getElementById("avatarBtn");
  const dropdown = document.getElementById("avatarDropdown");
  avatarBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.classList.toggle("show");
  });
  document.addEventListener("click", () => dropdown.classList.remove("show"));
  document.getElementById("logoutBtn").addEventListener("click", () => Auth.logout());

  refreshStatusDot();
  return session;
}

async function refreshStatusDot() {
  const dot = document.getElementById("statusDot");
  if (!dot) return;
  try {
    const rows = await api.get("/api/attendance/me");
    const today = new Date().toISOString().slice(0, 10);
    const todayRow = rows.find(r => r.work_date === today);
    if (todayRow && todayRow.status === "leave") dot.className = "status-dot leave";
    else if (todayRow && todayRow.check_in) dot.className = "status-dot present";
    else dot.className = "status-dot absent";
  } catch {
    /* non-critical, leave default */
  }
}
