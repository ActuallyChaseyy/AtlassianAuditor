from jinja2 import Environment, BaseLoader
from datetime import datetime, timezone

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Atlassian Audit Report</title>
    <style>
        :root {
            --bg:         #0D1117;
            --surface:    #161B22;
            --surface-2:  #21262D;
            --border:     #30363D;
            --text:       #E6EDF3;
            --text-muted: #8B949E;
            --accent:     #388BFD;
            --accent-dim: #1F6FEB;
        }

        * { box-sizing: border-box; }

        body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
               background: var(--bg); color: var(--text); }

        h1 { margin: 0; font-size: 20px; }

        header { background: var(--surface); border-bottom: 1px solid var(--border);
                 padding: 16px 24px; display: flex; justify-content: space-between; align-items: center; }
        header .meta { font-size: 12px; color: var(--text-muted); }

        nav { background: var(--surface); border-bottom: 1px solid var(--border);
              padding: 0 16px; display: flex; gap: 4px; }
        nav button { background: none; border: none; color: var(--text-muted);
                     padding: 12px 16px; cursor: pointer; font-size: 14px;
                     border-bottom: 2px solid transparent; transition: color 0.15s; }
        nav button:hover { color: var(--text); }
        nav button.active { color: var(--accent); border-bottom-color: var(--accent); }

        .tab { display: none; padding: 24px; }
        .tab.active { display: block; }

        details { background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
                  margin-bottom: 6px; padding: 12px 16px; transition: border-color 0.15s; }
        details:hover { border-color: var(--accent-dim); }
        details[open] { border-color: var(--accent); }
        summary { cursor: pointer; font-weight: 600; list-style: none;
                  display: flex; justify-content: space-between; align-items: center; }
        summary::-webkit-details-marker { display: none; }
        .summary-left { display: flex; gap: 8px; align-items: baseline; }
        .summary-left span { color: var(--text-muted); font-weight: normal; font-size: 14px; }
        .summary-right { font-size: 12px; font-weight: normal; color: var(--text-muted);
                         white-space: nowrap;
                         background: var(--surface-2); border: 1px solid var(--border);
                         border-radius: 12px; padding: 2px 10px; }

        .members-table { width: 100%; border-collapse: collapse; margin-top: 12px; font-size: 13px; }
        .members-table th { text-align: left; padding: 6px 12px; color: var(--text-muted);
                            border-bottom: 1px solid var(--border); font-weight: 600; }
        .members-table td { padding: 6px 12px; border-bottom: 1px solid var(--border); }
        .members-table tr:last-child td { border-bottom: none; }
        .members-table tr:hover td { background: var(--surface-2); }
        .member-count { font-size: 12px; color: var(--text-muted); font-weight: normal;
                        margin-left: 8px; }

        .stat-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; }
        .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px;
                     padding: 24px; text-align: center; }
        .stat-card .number { font-size: 40px; font-weight: 700; color: var(--accent); }
        .stat-card .label { font-size: 13px; color: var(--text-muted); margin-top: 6px; }

        input[type=search] { width: 100%; max-width: 400px; padding: 8px 12px; margin-bottom: 16px;
                             background: var(--surface); border: 1px solid var(--border);
                             border-radius: 6px; font-size: 14px; color: var(--text);
                             outline: none; transition: border-color 0.15s; }
        input[type=search]:focus { border-color: var(--accent); }
        input[type=search]::placeholder { color: var(--text-muted); }

        .empty-state { color: var(--text-muted); font-style: italic; padding: 32px 0; }

        .group-tabs { display: flex; gap: 0; margin-top: 12px; border-bottom: 1px solid var(--border); }
        .group-tab { background: none; border: none; color: var(--text-muted); padding: 8px 12px;
                     cursor: pointer; font-size: 13px; border-bottom: 2px solid transparent; transition: color 0.15s; }
        .group-tab:hover { color: var(--text); }
        .group-tab.active { color: var(--accent); border-bottom-color: var(--accent); }
        .group-tab-panel { display: none; padding-top: 4px; }
        .group-tab-panel.active { display: block; }

        /* Scrollbar styling for webkit browsers */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: var(--bg); }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
    </style>
</head>
<body>
    <header>
        <h1>Atlassian Audit Report</h1>
        <div class="meta">Generated {{ generated_at }}</div>
    </header>
    <nav>
        <button data-tab="summary" class="active">Summary</button>
        <button data-tab="groups">Groups ({{ audit_data.groups | length }})</button>
        <button data-tab="users">Users</button>
        <button data-tab="permissions">Permissions</button>
        <button data-tab="jira-spaces">Jira Spaces</button>
    </nav>
    <main>
        <section id="summary" class="tab active">
            <div class="stat-grid">
                <div class="stat-card">
                    <div class="number">{{ audit_data.groups | length }}</div>
                    <div class="label">Groups</div>
                </div>
                <div class="stat-card">
                    <div class="number">N/A</div>
                    <div class="label">Users</div>
                </div>
                <div class="stat-card">
                    <div class="number">N/A</div>
                    <div class="label">Confluence Spaces</div>
                </div>
                <div class="stat-card">
                    <div class="number">N/A</div>
                    <div class="label">Jira Projects</div>
                </div>
            </div>
        </section>

        <section id="groups" class="tab">
            <input type="search" id="group-search" placeholder="Search groups...">
            {% for group in audit_data.groups %}
            <details class="group-card" data-name="{{ group.name | lower }}">
                <summary>
                    <div class="summary-left">
                        {{ group.name }}
                        <span style="color:#6B778C; font-weight:normal"> - {{ group.description or 'No description' }}</span>
                    </div>
                    <div class="summary-right">{{ audit_data.tenant_map.get(group.directoryId, group.directoryId) }}</div>
                </summary>
                <div class="group-tabs">
                    <button class="group-tab active" data-target="users">Users ({{ group.users | length }})</button>
                    <button class="group-tab" data-target="spaces">Spaces</button>
                    <button class="group-tab" data-target="permissions">Permissions</button>
                </div>

                <div class="group-tab-panel active" data-panel="users">
                    {% if group.users %}
                    <table class="members-table">
                        <thead>
                            <tr>
                                <th>Name <span class="member-count">({{ group.users | length }})</span></th>
                                <th>Email</th>
                                <th>Account Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for user in group.users %}
                            <tr>
                                <td>{{ user.name }}</td>
                                <td>{{ user.email }}</td>
                                <td>{{ user.status }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                    {% else %}
                    <p class="empty-state">No members.</p>
                    {% endif %}
                </div>

                <div class="group-tab-panel" data-panel="spaces">
                    <p class="empty-state">Spaces data not yet collected.</p>
                </div>

                <div class="group-tab-panel" data-panel="permissions">
                    <p class="empty-state">Permissions data not yet collected.</p>
                </div>
            </details>
            {% else %}
            <p class="empty-state">No groups found.</p>
            {% endfor %}
        </section>

        <section id="users" class="tab">
            <p class="empty-state">No data collected yet.</p>
        </section>

        <section id="permissions" class="tab">
            <p class="empty-state">No data collected yet.</p>
        </section>

        <section id="jira-spaces" class="tab">
            <p class="empty-state">No data collected yet.</p>
        </section>
    </main>

    <script>
        // Tab switching
        document.querySelectorAll('nav button').forEach(btn => {
            btn.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(s => s.classList.remove('active'));
                document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
                document.getElementById(btn.dataset.tab).classList.add('active');
                btn.classList.add('active');
            });
        });

        // Inner tabs per group card - scoped to the clicked card only
        document.querySelectorAll('.group-tab').forEach(tab => {
            tab.addEventListener('click', e => {
                e.preventDefault();
                const card = e.target.closest('details');
                const target = e.target.dataset.target;
                card.querySelectorAll('.group-tab').forEach(t => t.classList.remove('active'));
                card.querySelectorAll('.group-tab-panel').forEach(p => p.classList.remove('active'));
                e.target.classList.add('active');
                card.querySelector(`.group-tab-panel[data-panel="${target}"]`).classList.add('active');
            });
        });

        // Group search - filters cards by name
        const groupSearch = document.getElementById('group-search');
        if (groupSearch) {
            groupSearch.addEventListener('input', e => {
                const q = e.target.value.toLowerCase();
                document.querySelectorAll('.group-card').forEach(card => {
                    card.style.display = card.dataset.name.includes(q) ? '' : 'none';
                });
            });
        }
    </script>
</body>
</html>
"""

def generate_report(audit_data, output_path="report.html"):
    env = Environment(loader=BaseLoader())
    template = env.from_string(REPORT_TEMPLATE)
    rendered_report = template.render(
        audit_data=audit_data,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered_report)
    return output_path
