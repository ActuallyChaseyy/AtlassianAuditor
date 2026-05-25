import json
from datetime import datetime, timezone, timedelta


def _safe_json(data):
    """Serialize to JSON safe for embedding inside a <script> tag."""
    return json.dumps(data, ensure_ascii=False).replace("</script>", "<\\/script>")


REPORT_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Atlassian Audit Report</title>
    <style>
        :root {{
            --bg:         #0D1117;
            --surface:    #161B22;
            --surface-2:  #21262D;
            --border:     #30363D;
            --text:       #E6EDF3;
            --text-muted: #8B949E;
            --accent:     #388BFD;
            --accent-dim: #1F6FEB;
        }}

        * {{ box-sizing: border-box; }}

        body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
               background: var(--bg); color: var(--text); }}

        h1 {{ margin: 0; font-size: 20px; }}

        header {{ background: var(--surface); border-bottom: 1px solid var(--border);
                 padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }}
        header .meta {{ font-size: 12px; color: var(--text-muted); }}

        nav {{ background: var(--surface); border-bottom: 1px solid var(--border);
              padding: 0 16px; display: flex; gap: 4px; }}
        nav button {{ background: none; border: none; color: var(--text-muted);
                     padding: 12px 16px; cursor: pointer; font-size: 14px;
                     border-bottom: 2px solid transparent; transition: color 0.15s; }}
        nav button:hover {{ color: var(--text); }}
        nav button.active {{ color: var(--accent); border-bottom-color: var(--accent); }}

        .tab {{ display: none; padding: 24px; }}
        .tab.active {{ display: block; }}

        details {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
                  margin-bottom: 6px; padding: 12px 16px; transition: border-color 0.15s; }}
        details:hover {{ border-color: var(--accent-dim); }}
        details[open] {{ border-color: var(--accent); }}
        summary {{ cursor: pointer; font-weight: 600; list-style: none;
                  display: flex; justify-content: space-between; align-items: center; }}
        summary::-webkit-details-marker {{ display: none; }}
        .summary-left {{ display: flex; gap: 8px; align-items: baseline; }}
        .summary-left span {{ color: var(--text-muted); font-weight: normal; font-size: 14px; }}
        .summary-right {{ font-size: 12px; font-weight: normal; color: var(--text-muted);
                         white-space: nowrap;
                         background: var(--surface-2); border: 1px solid var(--border);
                         border-radius: 12px; padding: 2px 10px; }}

        .members-table {{ width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }}
        .members-table th {{ text-align: left; padding: 6px 12px; color: var(--text-muted);
                            border-bottom: 1px solid var(--border); font-weight: 600; }}
        .members-table td {{ padding: 6px 12px; border-bottom: 1px solid var(--border); }}
        .members-table tr:last-child td {{ border-bottom: none; }}
        .members-table tr:hover td {{ background: var(--surface-2); }}
        .member-count {{ font-size: 12px; color: var(--text-muted); font-weight: normal;
                        margin-left: 8px; }}

        .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }}
        .stat-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
                     padding: 24px; text-align: center; }}
        .stat-card .number {{ font-size: 40px; font-weight: 700; color: var(--accent); }}
        .stat-card .label {{ font-size: 13px; color: var(--text-muted); margin-top: 6px; }}

        input[type=search] {{ width: 100%; max-width: 400px; padding: 8px 12px; margin-bottom: 16px;
                             background: var(--surface); border: 1px solid var(--border);
                             border-radius: 6px; font-size: 14px; color: var(--text);
                             outline: none; transition: border-color 0.15s; }}
        input[type=search]:focus {{ border-color: var(--accent); }}
        input[type=search]::placeholder {{ color: var(--text-muted); }}

        .empty-state {{ color: var(--text-muted); font-style: italic; padding: 32px 0; }}

        .suggestions-section {{ margin-top: 32px; }}
        .suggestions-section h2 {{
            font-size: 15px; font-weight: 600; color: var(--text-muted);
            text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 12px 0;
        }}
        .suggestion-badge {{
            display: inline-block; border-radius: 4px;
            padding: 1px 7px; font-size: 11px; font-weight: 700;
            text-transform: uppercase; letter-spacing: 0.04em;
            margin-right: 6px; vertical-align: middle;
        }}
        .badge-warning {{ background: #3D2B00; color: #F0A500; border: 1px solid #6B4A00; }}
        .badge-info    {{ background: #0D2137; color: #388BFD; border: 1px solid #1F6FEB; }}
        .suggestion-item-row {{
            padding: 4px 0; font-size: 13px; border-bottom: 1px solid var(--border);
            display: flex; justify-content: space-between; align-items: baseline;
        }}
        .suggestion-item-row:last-child {{ border-bottom: none; }}
        .suggestion-item-secondary {{ font-size: 12px; color: var(--text-muted); }}

        .group-tabs, .space-tabs, .group-sub-tabs {{
            display: flex; gap: 0; margin-top: 12px; border-bottom: 1px solid var(--border);
        }}
        .group-tab, .space-tab, .group-sub-tab {{
            background: none; border: none; color: var(--text-muted); cursor: pointer;
            border-bottom: 2px solid transparent; transition: color 0.15s;
        }}
        .group-tab, .space-tab {{ padding: 8px 12px; font-size: 13px; }}
        .group-sub-tab {{ padding: 6px 10px; font-size: 12px; }}
        .group-tab:hover, .space-tab:hover, .group-sub-tab:hover {{ color: var(--text); }}
        .group-tab.active, .space-tab.active, .group-sub-tab.active {{
            color: var(--accent); border-bottom-color: var(--accent);
        }}
        .group-tab-panel, .space-tab-panel, .group-sub-panel {{ display: none; }}
        .group-tab-panel.active, .space-tab-panel.active, .group-sub-panel.active {{ display: block; }}

        .member-card {{ background: var(--surface-2); border: 1px solid var(--border); border-radius: 4px;
                       margin-top: 8px; padding: 8px 12px; }}
        .member-card summary {{ cursor: pointer; font-weight: 500; font-size: 13px; list-style: none;
                               display: flex; justify-content: space-between; align-items: center; }}
        .member-card summary::-webkit-details-marker {{ display: none; }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: var(--bg); }}
        ::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: var(--text-muted); }}
    </style>
</head>
<body>
    <header>
        <h1>Atlassian Audit Report</h1>
        <div class="meta">Generated {generated_at}</div>
    </header>
    <nav>
        <button data-tab="summary" class="active">Summary</button>
        <button data-tab="groups">Groups</button>
        <button data-tab="users">Users</button>
        <button data-tab="permissions">Permissions</button>
        <button data-tab="jira-spaces">Jira Spaces</button>
    </nav>
    <main>
        <section id="summary" class="tab active"></section>
        <section id="groups" class="tab"></section>
        <section id="users" class="tab"></section>
        <section id="permissions" class="tab"></section>
        <section id="jira-spaces" class="tab"></section>
    </main>

    <script>
    const DATA = {data_json};

    // ── HTML escaping ──────────────────────────────────────────────────────────
    function esc(s) {{
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }}

    // ── Tab navigation ─────────────────────────────────────────────────────────
    const rendered = new Set();

    function activateTab(name) {{
        document.querySelectorAll('.tab').forEach(s => s.classList.remove('active'));
        document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
        document.getElementById(name).classList.add('active');
        document.querySelector(`[data-tab="${{name}}"]`).classList.add('active');
        if (!rendered.has(name)) {{
            RENDERERS[name]();
            rendered.add(name);
        }}
    }}

    document.querySelectorAll('nav button').forEach(btn =>
        btn.addEventListener('click', () => activateTab(btn.dataset.tab))
    );

    // ── Summary ────────────────────────────────────────────────────────────────
    function renderSummary() {{
        const stats = [
            {{ n: DATA.groups.length,      label: 'Groups' }},
            {{ n: DATA.users.length,       label: 'Users' }},
            {{ n: 'N/A',                   label: 'Confluence Spaces' }},
            {{ n: DATA.jira_spaces.length, label: 'Jira Projects' }},
        ];
        let html = '<div class="stat-grid">' +
            stats.map(s => `<div class="stat-card"><div class="number">${{s.n}}</div><div class="label">${{s.label}}</div></div>`).join('') +
            '</div>';

        const suggestions = (DATA.suggestions || []).slice().sort((a, b) => {{
            if (a.severity === b.severity) return 0;
            return a.severity === 'warning' ? -1 : 1;
        }});

        if (suggestions.length) {{
            html += '<div class="suggestions-section"><h2>Suggested Changes</h2>';
            html += suggestions.map(s => {{
                const badgeClass = s.severity === 'warning' ? 'badge-warning' : 'badge-info';
                const itemsHtml = (s.items || []).map(item => {{
                    const secondary = Object.entries(item)
                        .filter(([k]) => k !== 'label')
                        .map(([k, v]) => `${{esc(k.replace(/_/g, ' '))}}: ${{esc(String(v))}}`)
                        .join('  ·  ');
                    return `<div class="suggestion-item-row">
                        <span>${{esc(item.label)}}</span>
                        ${{secondary ? `<span class="suggestion-item-secondary">${{secondary}}</span>` : ''}}
                    </div>`;
                }}).join('');
                return `<details>
                    <summary>
                        <div class="summary-left">
                            <span class="suggestion-badge ${{badgeClass}}">${{esc(s.severity)}}</span>
                            ${{esc(s.title)}}
                            <span>${{esc(s.category)}}</span>
                        </div>
                        <div class="summary-right">${{s.count}} item${{s.count !== 1 ? 's' : ''}}</div>
                    </summary>
                    <p style="font-size:13px;color:var(--text-muted);margin:8px 0 12px">${{esc(s.detail)}}</p>
                    <div>${{itemsHtml}}</div>
                </details>`;
            }}).join('');
            html += '</div>';
        }}

        document.getElementById('summary').innerHTML = html;
    }}

    // ── Groups ─────────────────────────────────────────────────────────────────
    function buildGroupCard(group) {{
        const tenantName = DATA.tenant_map[group.directoryId] || group.directoryId;
        const det = document.createElement('details');
        det.className = 'group-card';
        det.dataset.name = (group.name || '').toLowerCase();
        det.innerHTML = `
            <summary>
                <div class="summary-left">${{esc(group.name)}}
                    <span style="color:#6B778C;font-weight:normal"> - ${{esc(group.description || 'No description')}}</span>
                </div>
                <div class="summary-right">${{esc(tenantName)}}</div>
            </summary>`;

        let innerDone = false;
        det.addEventListener('toggle', () => {{
            if (!det.open || innerDone) return;
            innerDone = true;
            const users = group.users || [];
            const rows = users.map(u =>
                `<tr><td>${{esc(u.name)}}</td><td>${{esc(u.email)}}</td><td>${{esc(u.status)}}</td></tr>`
            ).join('');
            const usersTable = rows
                ? `<table class="members-table"><thead><tr>
                       <th>Name <span class="member-count">(${{users.length}})</span></th>
                       <th>Email</th><th>Account Status</th>
                   </tr></thead><tbody>${{rows}}</tbody></table>`
                : '<p class="empty-state">No members.</p>';

            const assignedSpaces = (DATA.jira_spaces || []).filter(s =>
                (s.groups_with_access || []).some(g => g.name === group.name)
            );
            const spaceRows = assignedSpaces.map(s => {{
                const ga = s.groups_with_access.find(g => g.name === group.name);
                const roles = (ga.roles || []).join(', ') || '—';
                return `<tr><td>${{esc(s.name)}}</td><td>${{esc(s.key)}}</td><td>${{esc(roles)}}</td></tr>`;
            }}).join('');
            const spacesTable = spaceRows
                ? `<table class="members-table"><thead><tr>
                       <th>Project <span class="member-count">(${{assignedSpaces.length}})</span></th>
                       <th>Key</th><th>Roles</th>
                   </tr></thead><tbody>${{spaceRows}}</tbody></table>`
                : '<p class="empty-state">Not assigned to any Jira project.</p>';

            det.insertAdjacentHTML('beforeend', `
                <div class="group-tabs">
                    <button class="group-tab active" data-target="users">Users (${{users.length}})</button>
                    <button class="group-tab" data-target="spaces">Spaces (${{assignedSpaces.length}})</button>
                    <button class="group-tab" data-target="permissions">Permissions</button>
                </div>
                <div class="group-tab-panel active" data-panel="users">${{usersTable}}</div>
                <div class="group-tab-panel" data-panel="spaces">${{spacesTable}}</div>
                <div class="group-tab-panel" data-panel="permissions"><p class="empty-state">Permissions data not yet collected.</p></div>`);
            det.querySelectorAll('.group-tab').forEach(tab =>
                tab.addEventListener('click', e => {{
                    e.preventDefault();
                    const target = e.target.dataset.target;
                    det.querySelectorAll('.group-tab').forEach(t => t.classList.remove('active'));
                    det.querySelectorAll('.group-tab-panel').forEach(p => p.classList.remove('active'));
                    e.target.classList.add('active');
                    det.querySelector(`.group-tab-panel[data-panel="${{target}}"]`).classList.add('active');
                }})
            );
        }});
        return det;
    }}

    let groupCards = [];

    function renderGroups() {{
        const sec = document.getElementById('groups');
        sec.innerHTML = `<input type="search" id="group-search" placeholder="Search groups..."><div id="group-list"></div>`;
        const list = document.getElementById('group-list');
        groupCards = (DATA.groups || []).map(buildGroupCard);
        groupCards.forEach(c => list.appendChild(c));
        document.querySelector('[data-tab="groups"]').textContent = `Groups (${{DATA.groups.length}})`;
        document.getElementById('group-search').addEventListener('input', e => {{
            const q = e.target.value.toLowerCase();
            groupCards.forEach(c => {{ c.style.display = c.dataset.name.includes(q) ? '' : 'none'; }});
        }});
    }}

    // ── Users ──────────────────────────────────────────────────────────────────
    let userRows = [];

    function renderUsers() {{
        const sec = document.getElementById('users');
        if (!DATA.users || !DATA.users.length) {{
            sec.innerHTML = '<p class="empty-state">No users found.</p>';
            return;
        }}
        sec.innerHTML = `
            <input type="search" id="user-search" placeholder="Search users...">
            <table class="members-table">
                <thead><tr><th>Name</th><th>Email</th><th>Account Status</th></tr></thead>
                <tbody id="users-tbody"></tbody>
            </table>`;
        const tbody = document.getElementById('users-tbody');
        userRows = DATA.users.map(u => {{
            const tr = document.createElement('tr');
            tr.dataset.name  = (u.name  || '').toLowerCase();
            tr.dataset.email = (u.email || '').toLowerCase();
            tr.innerHTML = `<td>${{esc(u.name)}}</td><td>${{esc(u.email)}}</td><td>${{esc(u.status)}}</td>`;
            return tr;
        }});
        userRows.forEach(r => tbody.appendChild(r));
        document.querySelector('[data-tab="users"]').textContent = `Users (${{DATA.users.length}})`;
        document.getElementById('user-search').addEventListener('input', e => {{
            const q = e.target.value.toLowerCase();
            userRows.forEach(r => {{
                r.style.display = (r.dataset.name.includes(q) || r.dataset.email.includes(q)) ? '' : 'none';
            }});
        }});
    }}

    // ── Permissions ────────────────────────────────────────────────────────────
    function renderPermissions() {{
        document.getElementById('permissions').innerHTML = '<p class="empty-state">No data collected yet.</p>';
    }}

    // ── Jira Spaces ────────────────────────────────────────────────────────────
    function buildJiraCard(space) {{
        const det = document.createElement('details');
        det.className = 'jira-card';
        det.dataset.name = (space.name || '').toLowerCase();
        const lead = space.lead ? ` · ${{esc(space.lead)}}` : '';
        det.innerHTML = `
            <summary>
                <div class="summary-left">${{esc(space.name)}}
                    <span style="color:#6B778C;font-weight:normal"> · ${{esc(space.key)}}</span>
                </div>
                <div class="summary-right">${{esc(space.type)}}${{lead}}</div>
            </summary>`;

        let innerDone = false;
        det.addEventListener('toggle', () => {{
            if (!det.open || innerDone) return;
            innerDone = true;

            const usersWithAccess  = space.users_with_access  || [];
            const groupsWithAccess = space.groups_with_access || [];

            const usersHtml = usersWithAccess.map(user => {{
                const roles = (user.roles || []).map(r => `<tr><td>${{esc(r)}}</td></tr>`).join('');
                return `<details class="member-card">
                    <summary>
                        <div class="summary-left">${{esc(user.displayName)}}</div>
                        <div class="summary-right">${{esc((user.roles || []).join(', '))}}</div>
                    </summary>
                    <table class="members-table"><thead><tr><th>Permission Role</th></tr></thead>
                    <tbody>${{roles}}</tbody></table>
                </details>`;
            }}).join('') || '<p class="empty-state">No users with direct access.</p>';

            const groupsHtml = groupsWithAccess.map(group => {{
                const gd = DATA.groups.find(g => g.name === group.name);
                const memberRows = (gd && gd.users || []).map(u =>
                    `<tr><td>${{esc(u.name)}}</td><td>${{esc(u.email)}}</td><td>${{esc(u.status)}}</td></tr>`
                ).join('');
                const usersTable = memberRows
                    ? `<table class="members-table"><thead><tr><th>Name</th><th>Email</th><th>Status</th></tr></thead><tbody>${{memberRows}}</tbody></table>`
                    : '<p class="empty-state">No members.</p>';
                const permRows = (group.roles || []).map(r => `<tr><td>${{esc(r)}}</td></tr>`).join('');
                const memberCount = gd ? (gd.users || []).length : 0;
                return `<details class="member-card">
                    <summary>
                        <div class="summary-left">${{esc(group.name)}}</div>
                        <div class="summary-right">${{esc((group.roles || []).join(', '))}}</div>
                    </summary>
                    <div class="group-sub-tabs">
                        <button class="group-sub-tab active" data-target="users">Users (${{memberCount}})</button>
                        <button class="group-sub-tab" data-target="permissions">Permissions</button>
                    </div>
                    <div class="group-sub-panel active" data-panel="users">${{usersTable}}</div>
                    <div class="group-sub-panel" data-panel="permissions">
                        <table class="members-table"><thead><tr><th>Permission Role</th></tr></thead>
                        <tbody>${{permRows}}</tbody></table>
                    </div>
                </details>`;
            }}).join('') || '<p class="empty-state">No groups with access.</p>';

            det.insertAdjacentHTML('beforeend', `
                <div class="space-tabs">
                    <button class="space-tab active" data-target="users">Users (${{usersWithAccess.length}})</button>
                    <button class="space-tab" data-target="groups">Groups (${{groupsWithAccess.length}})</button>
                </div>
                <div class="space-tab-panel active" data-panel="users">${{usersHtml}}</div>
                <div class="space-tab-panel" data-panel="groups">${{groupsHtml}}</div>`);

            det.querySelectorAll('.space-tab').forEach(tab =>
                tab.addEventListener('click', e => {{
                    e.preventDefault();
                    const target = e.target.dataset.target;
                    det.querySelectorAll('.space-tab').forEach(t => t.classList.remove('active'));
                    det.querySelectorAll('.space-tab-panel').forEach(p => p.classList.remove('active'));
                    e.target.classList.add('active');
                    det.querySelector(`.space-tab-panel[data-panel="${{target}}"]`).classList.add('active');
                }})
            );
            det.querySelectorAll('.group-sub-tab').forEach(tab =>
                tab.addEventListener('click', e => {{
                    e.preventDefault();
                    const card = e.target.closest('.member-card');
                    const target = e.target.dataset.target;
                    card.querySelectorAll('.group-sub-tab').forEach(t => t.classList.remove('active'));
                    card.querySelectorAll('.group-sub-panel').forEach(p => p.classList.remove('active'));
                    e.target.classList.add('active');
                    card.querySelector(`.group-sub-panel[data-panel="${{target}}"]`).classList.add('active');
                }})
            );
        }});
        return det;
    }}

    let jiraCards = [];

    function renderJiraSpaces() {{
        const sec = document.getElementById('jira-spaces');
        if (!DATA.jira_spaces || !DATA.jira_spaces.length) {{
            sec.innerHTML = '<p class="empty-state">No Jira spaces found.</p>';
            return;
        }}
        sec.innerHTML = `<input type="search" id="jira-search" placeholder="Search spaces..."><div id="jira-list"></div>`;
        const list = document.getElementById('jira-list');
        jiraCards = DATA.jira_spaces.map(buildJiraCard);
        jiraCards.forEach(c => list.appendChild(c));
        document.querySelector('[data-tab="jira-spaces"]').textContent = `Jira Spaces (${{DATA.jira_spaces.length}})`;
        document.getElementById('jira-search').addEventListener('input', e => {{
            const q = e.target.value.toLowerCase();
            jiraCards.forEach(c => {{ c.style.display = c.dataset.name.includes(q) ? '' : 'none'; }});
        }});
    }}

    // ── Bootstrap ──────────────────────────────────────────────────────────────
    const RENDERERS = {{
        summary:     renderSummary,
        groups:      renderGroups,
        users:       renderUsers,
        permissions: renderPermissions,
        'jira-spaces': renderJiraSpaces,
    }};

    renderSummary();
    rendered.add('summary');
    </script>
</body>
</html>
"""


def generate_report(audit_data, output_path="report.html"):
    html = REPORT_TEMPLATE.format(
        generated_at=datetime.now(timezone(timedelta(hours=10))).strftime("%Y-%m-%d %H:%M AEST"),
        data_json=_safe_json(audit_data),
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
