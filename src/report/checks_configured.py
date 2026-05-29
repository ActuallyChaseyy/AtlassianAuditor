from report.checks import _finding, _tenant_name

# ── Large groups on Jira ───────────────────────────────────────────────────────
# Flag groups above this member count that are assigned to a Jira project.
LARGE_GROUPS_ON_JIRA_ENABLED   = True
LARGE_GROUPS_ON_JIRA_THRESHOLD = 50

# ── Required group on all Jira spaces ─────────────────────────────────────────
# Set ENABLED to True and provide the group name to flag any Jira project
# that does not have this group assigned.
REQUIRED_GROUP_ENABLED = False
REQUIRED_GROUP_NAME    = ""


def run_checks(audit_data) -> list[dict]:
    groups      = audit_data.get("groups", [])
    jira_spaces = audit_data.get("jira_spaces", [])
    tenant_map  = audit_data.get("tenant_map", {})

    raw = [
        _check_large_groups_on_jira(groups, jira_spaces, tenant_map) if LARGE_GROUPS_ON_JIRA_ENABLED else None,
        _check_required_group_missing_from_spaces(jira_spaces)        if REQUIRED_GROUP_ENABLED else None,
    ]
    return [c for c in raw if c is not None]


# ── Checks ─────────────────────────────────────────────────────────────────────

def _check_large_groups_on_jira(groups, jira_spaces, tenant_map):
    assigned = {g["name"] for s in jira_spaces for g in s.get("groups_with_access", [])}
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map), "members": len(g.get("users", []))}
        for g in groups
        if len(g.get("users", [])) > LARGE_GROUPS_ON_JIRA_THRESHOLD and g["name"] in assigned
    ]
    return _finding(
        "large_groups_on_jira", "info", "Groups",
        f"groups with >{LARGE_GROUPS_ON_JIRA_THRESHOLD} members assigned to a Jira project",
        "Large groups on Jira projects may indicate over-broad access. Consider splitting into more targeted groups.",
        items,
    )


def _check_required_group_missing_from_spaces(jira_spaces):
    items = [
        {"label": s["name"], "key": s["key"]}
        for s in jira_spaces
        if not any(g["name"] == REQUIRED_GROUP_NAME for g in s.get("groups_with_access", []))
    ]
    return _finding(
        "required_group_missing_from_spaces", "warning", "Jira",
        f"Jira projects missing the '{REQUIRED_GROUP_NAME}' group",
        f"The group '{REQUIRED_GROUP_NAME}' is expected on every Jira project but is absent from these.",
        items,
    )
