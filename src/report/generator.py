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

        .toolbar {{ display: flex; gap: 12px; align-items: center; margin-bottom: 16px; flex-wrap: wrap; }}
        .toolbar input[type=search] {{ margin-bottom: 0; }}
        .toggle-btn {{
            background: var(--surface-2); border: 1px solid var(--border); border-radius: 6px;
            color: var(--text-muted); cursor: pointer; font-size: 13px; padding: 7px 14px;
            white-space: nowrap; transition: color 0.15s, border-color 0.15s;
        }}
        .toggle-btn.active {{ color: var(--accent); border-color: var(--accent); }}

        .combo {{ position: relative; }}
        .combo input[type=text] {{
            padding: 8px 12px; background: var(--surface); border: 1px solid var(--border);
            border-radius: 6px; font-size: 14px; color: var(--text); outline: none;
            min-width: 260px; transition: border-color 0.15s;
        }}
        .combo input[type=text]:focus {{ border-color: var(--accent); }}
        .combo input[type=text]::placeholder {{ color: var(--text-muted); }}
        .combo-results {{
            display: none; position: absolute; top: calc(100% + 4px); left: 0; z-index: 20;
            width: 340px; max-height: 280px; overflow-y: auto;
            background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
        }}
        .combo-item {{ padding: 8px 12px; cursor: pointer; font-size: 13px;
                      border-bottom: 1px solid var(--border); }}
        .combo-item:last-child {{ border-bottom: none; }}
        .combo-item:hover {{ background: var(--surface-2); }}
        .combo-tenant {{ color: var(--text-muted); font-size: 12px; }}
        .combo-empty {{ padding: 8px 12px; color: var(--text-muted); font-style: italic; font-size: 13px; }}
        .filter-chip {{
            display: inline-flex; align-items: center; gap: 6px;
            background: var(--surface-2); border: 1px solid var(--accent); color: var(--accent);
            border-radius: 12px; padding: 4px 10px; font-size: 13px; white-space: nowrap;
        }}
        .filter-chip button {{
            background: none; border: none; color: var(--accent); cursor: pointer;
            font-size: 14px; line-height: 1; padding: 0;
        }}
        .filter-count {{ font-size: 13px; color: var(--text-muted); margin-bottom: 16px; }}
        .role-select {{
            padding: 8px 12px; background: var(--surface); border: 1px solid var(--border);
            border-radius: 6px; font-size: 14px; color: var(--text); outline: none; cursor: pointer;
            transition: border-color 0.15s;
        }}
        .role-select:focus {{ border-color: var(--accent); }}

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
        <button data-tab="jira-spaces">Jira Spaces</button>
    </nav>
    <main>
        <section id="summary" class="tab active"></section>
        <section id="groups" class="tab"></section>
        <section id="users" class="tab"></section>
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

            const spacesHtml = assignedSpaces.map(space => {{
                const ga = space.groups_with_access.find(g => g.name === group.name);
                const groupRoles = ga ? (ga.roles || []) : [];
                const scheme = (DATA.permission_schemes || []).find(s => s.id == space.permission_scheme_id);
                let permsHtml;
                if (scheme) {{
                    const allPerms = [...new Set(scheme.permissions.map(p => p.permission))].sort();
                    const permRows = allPerms.map(permKey => {{
                        let granted = false;
                        for (const perm of scheme.permissions) {{
                            if (perm.permission !== permKey) continue;
                            for (const holder of perm.holders) {{
                                if (holder.type === 'group' && holder.name === group.name) {{ granted = true; break; }}
                                if (holder.type === 'projectRole' && groupRoles.includes(holder.name)) {{ granted = true; break; }}
                            }}
                            if (granted) break;
                        }}
                        return `<tr>
                            <td>${{esc(formatPermissionName(permKey))}}</td>
                            <td style="text-align:right">${{granted ? '✅' : '❌'}}</td>
                        </tr>`;
                    }}).join('');
                    permsHtml = `<table class="members-table"><thead><tr>
                        <th>Permission</th><th style="text-align:right">Granted</th>
                    </tr></thead><tbody>${{permRows}}</tbody></table>`;
                }} else {{
                    permsHtml = '<p class="empty-state">No permission scheme linked to this space.</p>';
                }}
                return `<details class="member-card">
                    <summary>
                        <div class="summary-left">${{esc(space.name)}}
                            <span style="color:#6B778C;font-weight:normal"> · ${{esc(space.key)}}</span>
                        </div>
                        <div class="summary-right">${{esc(groupRoles.join(', ') || '')}}</div>
                    </summary>
                    ${{permsHtml}}
                </details>`;
            }}).join('') || '<p class="empty-state">Not assigned to any Jira project.</p>';

            det.insertAdjacentHTML('beforeend', `
                <div class="group-tabs">
                    <button class="group-tab active" data-target="users">Users (${{users.length}})</button>
                    <button class="group-tab" data-target="spaces">Spaces (${{assignedSpaces.length}})</button>
                </div>
                <div class="group-tab-panel active" data-panel="users">${{usersTable}}</div>
                <div class="group-tab-panel" data-panel="spaces">${{spacesHtml}}</div>`);
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
    let userCards = [];

    function renderUsers() {{
        const sec = document.getElementById('users');
        if (!DATA.users || !DATA.users.length) {{
            sec.innerHTML = '<p class="empty-state">No users found.</p>';
            return;
        }}
        sec.innerHTML = `
            <div class="toolbar">
                <input type="search" id="user-search" placeholder="Search users...">
                <button id="user-active-toggle" class="toggle-btn">Active Only</button>
                <div class="combo">
                    <input type="text" id="user-group-search" autocomplete="off"
                           placeholder="Filter by group (type 2+ chars)...">
                    <div id="user-group-results" class="combo-results"></div>
                </div>
                <select id="user-role-filter" class="role-select">
                    <option value="">All roles</option>
                </select>
                <span id="user-group-chip"></span>
            </div>
            <div id="user-count" class="filter-count"></div>
            <div id="user-list"></div>`;
        const list = document.getElementById('user-list');

        const groupsByAccount = {{}};
        for (const group of (DATA.groups || [])) {{
            for (const u of (group.users || [])) {{
                if (!groupsByAccount[u.accountId]) groupsByAccount[u.accountId] = [];
                groupsByAccount[u.accountId].push(group);
            }}
        }}

        // Precompute the set of space roles each user holds (direct + via group membership),
        // plus the universe of roles for the filter dropdown. Only roles actually held by a
        // user are offered, so every option filters to at least one user.
        const groupById = {{}};
        for (const g of (DATA.groups || [])) groupById[g.id] = g;
        const rolesByAccount = {{}};
        const allRoles = new Set();
        function addUserRole(accountId, role) {{
            allRoles.add(role);
            (rolesByAccount[accountId] || (rolesByAccount[accountId] = new Set())).add(role);
        }}
        for (const space of (DATA.jira_spaces || [])) {{
            for (const u of (space.users_with_access || []))
                for (const r of (u.roles || [])) addUserRole(u.accountId, r);
            for (const ga of (space.groups_with_access || [])) {{
                const grp = groupById[ga.groupId];
                if (!grp) continue;
                for (const m of (grp.users || []))
                    for (const r of (ga.roles || [])) addUserRole(m.accountId, r);
            }}
        }}
        const roleSelect = document.getElementById('user-role-filter');
        roleSelect.innerHTML = '<option value="">All roles</option>' +
            [...allRoles].sort((a, b) => a.localeCompare(b))
                .map(r => `<option value="${{esc(r)}}">${{esc(r)}}</option>`).join('');

        userCards = (DATA.users || []).map(user => {{
            const det = document.createElement('details');
            det.className = 'user-card';
            det.dataset.name    = (user.name   || '').toLowerCase();
            det.dataset.email   = (user.email  || '').toLowerCase();
            det.dataset.status  = (user.status || '').toLowerCase();
            det.dataset.account = user.accountId || '';
            det.innerHTML = `
                <summary>
                    <div class="summary-left">${{esc(user.name)}}
                        <span style="color:#6B778C;font-weight:normal"> - ${{esc(user.email)}}</span>
                    </div>
                    <div class="summary-right">${{esc(user.status)}}</div>
                </summary>`;

            let innerDone = false;
            det.addEventListener('toggle', () => {{
                if (!det.open || innerDone) return;
                innerDone = true;
                const memberGroups = groupsByAccount[user.accountId] || [];

                // ── Groups panel: groups the user is a member of ──
                const groupRows = memberGroups.map(g =>
                    `<tr><td>${{esc(g.name)}}</td><td>${{esc(g.description || '')}}</td></tr>`
                ).join('');
                const groupsTable = groupRows
                    ? `<table class="members-table"><thead><tr>
                           <th>Group <span class="member-count">(${{memberGroups.length}})</span></th>
                           <th>Description</th>
                       </tr></thead><tbody>${{groupRows}}</tbody></table>`
                    : '<p class="empty-state">Not a member of any group.</p>';

                // ── Spaces panel: spaces the user can access directly or via a group ──
                const memberGroupIds = new Set(memberGroups.map(g => g.id));
                const spaceEntries = [];
                for (const space of (DATA.jira_spaces || [])) {{
                    const direct = (space.users_with_access || []).find(u => u.accountId === user.accountId);
                    const viaGroups = (space.groups_with_access || []).filter(g => memberGroupIds.has(g.groupId));
                    if (!direct && !viaGroups.length) continue;
                    const sources = [];
                    if (direct) sources.push('Direct');
                    viaGroups.forEach(g => sources.push(g.name));
                    const roles = new Set();
                    if (direct) (direct.roles || []).forEach(r => roles.add(r));
                    viaGroups.forEach(g => (g.roles || []).forEach(r => roles.add(r)));
                    spaceEntries.push({{
                        name: space.name, key: space.key, tenant: space.tenant || '',
                        sources, roles: [...roles],
                    }});
                }}

                det.insertAdjacentHTML('beforeend', `
                    <div class="group-tabs">
                        <button class="group-tab active" data-target="groups">Groups (${{memberGroups.length}})</button>
                        <button class="group-tab" data-target="spaces">Spaces</button>
                    </div>
                    <div class="group-tab-panel active" data-panel="groups">${{groupsTable}}</div>
                    <div class="group-tab-panel" data-panel="spaces"></div>`);

                // Render (and re-render on role-filter change) the spaces panel. When a role is
                // selected, only spaces granting that role are shown.
                const spacesPanel  = det.querySelector('.group-tab-panel[data-panel="spaces"]');
                const spacesTabBtn = det.querySelector('.group-tab[data-target="spaces"]');
                function renderSpacesPanel() {{
                    const filtered = selectedRole
                        ? spaceEntries.filter(e => e.roles.includes(selectedRole))
                        : spaceEntries;
                    spacesTabBtn.textContent = `Spaces (${{filtered.length}})`;
                    if (!filtered.length) {{
                        spacesPanel.innerHTML = selectedRole
                            ? '<p class="empty-state">No accessible spaces with the selected role.</p>'
                            : '<p class="empty-state">No Jira space access.</p>';
                        return;
                    }}
                    const rows = filtered.map(e => `<tr>
                        <td>${{esc(e.name)}}</td>
                        <td>${{esc(e.key)}}</td>
                        <td>${{esc(e.tenant)}}</td>
                        <td>${{esc(e.sources.join(', '))}}</td>
                        <td>${{esc(e.roles.join(', '))}}</td>
                    </tr>`).join('');
                    spacesPanel.innerHTML = `<table class="members-table"><thead><tr>
                        <th>Space <span class="member-count">(${{filtered.length}})</span></th>
                        <th>Key</th><th>Tenant</th><th>Access Via</th><th>Roles</th>
                    </tr></thead><tbody>${{rows}}</tbody></table>`;
                }}
                det._refreshSpaces = renderSpacesPanel;
                renderSpacesPanel();

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
        }});

        userCards.forEach(c => list.appendChild(c));
        document.querySelector('[data-tab="users"]').textContent = `Users (${{DATA.users.length}})`;

        let activeOnly = false;
        let selectedGroup = null;   // {{ name, tenant, accountIds: Set }}
        let selectedRole = '';      // space role name, or '' for all
        function applyUserFilter() {{
            const q = document.getElementById('user-search').value.toLowerCase();
            let shown = 0;
            userCards.forEach(c => {{
                const matchSearch = c.dataset.name.includes(q) || c.dataset.email.includes(q);
                const matchActive = !activeOnly || c.dataset.status === 'active';
                const matchGroup  = !selectedGroup || selectedGroup.accountIds.has(c.dataset.account);
                const userRoles   = rolesByAccount[c.dataset.account];
                const matchRole   = !selectedRole || (userRoles && userRoles.has(selectedRole));
                const visible = matchSearch && matchActive && matchGroup && matchRole;
                c.style.display = visible ? '' : 'none';
                if (visible) shown++;
                // Re-filter the spaces panel of any card already expanded.
                if (c._refreshSpaces) c._refreshSpaces();
            }});
            document.getElementById('user-count').textContent =
                `${{shown}} of ${{userCards.length}} user${{userCards.length !== 1 ? 's' : ''}} match the current filter`;
        }}
        applyUserFilter();

        roleSelect.addEventListener('change', e => {{
            selectedRole = e.target.value;
            applyUserFilter();
        }});
        document.getElementById('user-search').addEventListener('input', applyUserFilter);
        document.getElementById('user-active-toggle').addEventListener('click', e => {{
            activeOnly = !activeOnly;
            e.target.classList.toggle('active', activeOnly);
            applyUserFilter();
        }});

        // ── Group type-ahead filter ──────────────────────────────────────────
        const groupIndex = (DATA.groups || []).map(g => ({{
            name:       g.name || '',
            tenant:     DATA.tenant_map[g.directoryId] || g.directoryId || '',
            accountIds: new Set((g.users || []).map(u => u.accountId)),
        }}));

        const groupSearch  = document.getElementById('user-group-search');
        const groupResults = document.getElementById('user-group-results');
        const groupChip    = document.getElementById('user-group-chip');
        let currentMatches = [];

        function renderGroupChip() {{
            if (!selectedGroup) {{ groupChip.innerHTML = ''; return; }}
            groupChip.innerHTML = `<span class="filter-chip">Group: ${{esc(selectedGroup.name)}}` +
                `<button title="Clear group filter">&times;</button></span>`;
            groupChip.querySelector('button').addEventListener('click', () => {{
                selectedGroup = null;
                renderGroupChip();
                applyUserFilter();
            }});
        }}

        function hideGroupResults() {{
            groupResults.style.display = 'none';
            groupResults.innerHTML = '';
        }}

        groupSearch.addEventListener('input', () => {{
            const q = groupSearch.value.trim().toLowerCase();
            if (q.length < 2) {{ hideGroupResults(); return; }}
            currentMatches = groupIndex
                .filter(g => g.name.toLowerCase().includes(q))
                .sort((a, b) => a.name.localeCompare(b.name))
                .slice(0, 50);
            if (!currentMatches.length) {{
                groupResults.innerHTML = '<div class="combo-empty">No matching groups</div>';
            }} else {{
                groupResults.innerHTML = currentMatches.map((g, i) => {{
                    const n = g.accountIds.size;
                    return `<div class="combo-item" data-idx="${{i}}">${{esc(g.name)}}` +
                        ` <span class="combo-tenant">${{esc(g.tenant)}} · ${{n}} member${{n !== 1 ? 's' : ''}}</span></div>`;
                }}).join('');
            }}
            groupResults.style.display = 'block';
        }});

        groupResults.addEventListener('click', e => {{
            const item = e.target.closest('.combo-item');
            if (!item) return;
            selectedGroup = currentMatches[+item.dataset.idx];
            groupSearch.value = '';
            hideGroupResults();
            renderGroupChip();
            applyUserFilter();
        }});

        // Close the dropdown when clicking outside the combo box.
        document.addEventListener('click', e => {{
            if (!e.target.closest('.combo')) hideGroupResults();
        }});
    }}

    // ── Permissions (helpers used by Jira Spaces) ──────────────────────────────
    function formatPermissionName(key) {{
        return key.replace(/_/g, ' ').replace(/\\b\\w/g, c => c.toUpperCase());
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
                const scheme = (DATA.permission_schemes || []).find(s => s.id == space.permission_scheme_id);
                const groupRoles = group.roles || [];
                let permsHtml;
                if (scheme) {{
                    const rows = [];
                    for (const perm of scheme.permissions) {{
                        for (const holder of perm.holders) {{
                            if (holder.type === 'group' && holder.name === group.name) {{
                                rows.push(`<tr><td>${{esc(formatPermissionName(perm.permission))}}</td><td>Direct</td></tr>`);
                            }} else if (holder.type === 'projectRole' && groupRoles.includes(holder.name)) {{
                                rows.push(`<tr><td>${{esc(formatPermissionName(perm.permission))}}</td><td>Role: ${{esc(holder.name)}}</td></tr>`);
                            }}
                        }}
                    }}
                    permsHtml = rows.length
                        ? `<table class="members-table"><thead><tr><th>Permission</th><th>Granted Via</th></tr></thead><tbody>${{rows.join('')}}</tbody></table>`
                        : '<p class="empty-state">No permissions found for this group in the space permission scheme.</p>';
                }} else {{
                    permsHtml = '<p class="empty-state">No permission scheme linked to this space.</p>';
                }}
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
                    <div class="group-sub-panel" data-panel="permissions">${{permsHtml}}</div>
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
