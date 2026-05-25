from collections import defaultdict


def run_checks(audit_data) -> list[dict]:
    groups      = audit_data.get("groups", [])
    users       = audit_data.get("users", [])
    jira_spaces = audit_data.get("jira_spaces", [])
    tenant_map  = audit_data.get("tenant_map", {})

    raw = [
        # Warnings
        _check_empty_groups(groups, tenant_map),
        _check_all_inactive_groups(groups, tenant_map),
        _check_inactive_users_in_groups(groups),
        _check_duplicate_email_accounts(users),
        _check_over_privileged_users(jira_spaces, users),
        _check_users_direct_jira_access(jira_spaces, users),
        _check_jira_projects_direct_user_assignments(jira_spaces),
        _check_jira_empty_group_assigned(jira_spaces, groups),
        # Info
        _check_groups_no_jira_access(groups, jira_spaces, tenant_map),
        _check_groups_no_description(groups, tenant_map),
        _check_ungrouped_users(groups, users),
        _check_jira_no_lead(jira_spaces),
        _check_jira_no_group_access(jira_spaces),
        _check_large_groups_on_jira(groups, jira_spaces, tenant_map),
        _check_same_group_name_multi_tenant(groups, tenant_map),
    ]
    return [c for c in raw if c is not None]


# ── Helpers ────────────────────────────────────────────────────────────────────

_ADDON_ROLE = "atlassian-addons-project-access"

def _human_users(users_with_access):
    return [u for u in users_with_access if _ADDON_ROLE not in u.get("roles", [])]


def _finding(id_, severity, category, title, detail, items):
    if not items:
        return None
    return {
        "id": id_,
        "severity": severity,
        "category": category,
        "title": f"{len(items)} {title}",
        "detail": detail,
        "count": len(items),
        "items": items,
    }


def _tenant_name(group, tenant_map):
    return tenant_map.get(group["directoryId"], group["directoryId"])


# ── Group checks ───────────────────────────────────────────────────────────────

def _check_empty_groups(groups, tenant_map):
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map)}
        for g in groups if not g.get("users")
    ]
    return _finding(
        "empty_groups", "warning", "Groups",
        "empty groups",
        "These groups have no members. Consider removing them to reduce clutter.",
        items,
    )


def _check_all_inactive_groups(groups, tenant_map):
    items = []
    for g in groups:
        members = g.get("users", [])
        if members and all(u.get("status") != "active" for u in members):
            items.append({
                "label": g["name"],
                "tenant": _tenant_name(g, tenant_map),
                "members": len(members),
            })
    return _finding(
        "all_inactive_groups", "warning", "Groups",
        "groups where all members are inactive",
        "Every member of these groups is inactive. Remove the group or update its membership.",
        items,
    )


def _check_groups_no_jira_access(groups, jira_spaces, tenant_map):
    assigned = {g["name"] for s in jira_spaces for g in s.get("groups_with_access", [])}
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map), "members": len(g.get("users", []))}
        for g in groups if g["name"] not in assigned
    ]
    return _finding(
        "groups_no_jira_access", "info", "Groups",
        "groups not assigned to any Jira project",
        "These groups exist but aren't used in any Jira project. Verify they're needed elsewhere or remove them.",
        items,
    )


def _check_groups_no_description(groups, tenant_map):
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map)}
        for g in groups if not g.get("description")
    ]
    return _finding(
        "groups_no_description", "info", "Groups",
        "groups with no description",
        "Adding descriptions makes it easier to understand a group's purpose and avoid duplicate groups.",
        items,
    )


def _check_large_groups_on_jira(groups, jira_spaces, tenant_map, threshold=50):
    assigned = {g["name"] for s in jira_spaces for g in s.get("groups_with_access", [])}
    items = [
        {"label": g["name"], "tenant": _tenant_name(g, tenant_map), "members": len(g.get("users", []))}
        for g in groups
        if len(g.get("users", [])) > threshold and g["name"] in assigned
    ]
    return _finding(
        "large_groups_on_jira", "info", "Groups",
        f"groups with >{threshold} members assigned to a Jira project",
        "Large groups on Jira projects may indicate over-broad access. Consider splitting into more targeted groups.",
        items,
    )


def _check_same_group_name_multi_tenant(groups, tenant_map):
    name_to_tenants = defaultdict(set)
    for g in groups:
        name_to_tenants[g["name"]].add(_tenant_name(g, tenant_map))
    items = [
        {"label": name, "tenants": ", ".join(sorted(tenants))}
        for name, tenants in name_to_tenants.items() if len(tenants) > 1
    ]
    return _finding(
        "same_group_name_multi_tenant", "info", "Groups",
        "group names that exist in multiple tenants",
        "Identically-named groups across tenants can cause confusion when managing access. Consider prefixing with the tenant name.",
        items,
    )


# ── User checks ────────────────────────────────────────────────────────────────

def _check_inactive_users_in_groups(groups):
    # {accountId: {name, email, groups: set}}
    user_map = {}
    for g in groups:
        for u in g.get("users", []):
            if u.get("status") != "active":
                aid = u["accountId"]
                if aid not in user_map:
                    user_map[aid] = {"name": u["name"], "email": u["email"], "groups": set()}
                user_map[aid]["groups"].add(g["name"])
    items = [
        {"label": v["name"], "email": v["email"], "groups": ", ".join(sorted(v["groups"]))}
        for v in user_map.values()
    ]
    return _finding(
        "inactive_users_in_groups", "warning", "Users",
        "inactive users still assigned to groups",
        "These accounts are inactive but remain in groups, potentially retaining access. Remove them from all groups.",
        items,
    )


def _check_ungrouped_users(groups, users):
    grouped_ids = {u["accountId"] for g in groups for u in g.get("users", [])}
    items = [
        {"label": u["name"], "email": u["email"], "status": u["status"]}
        for u in users if u["accountId"] not in grouped_ids
    ]
    return _finding(
        "ungrouped_users", "info", "Users",
        "managed users not in any group",
        "These users are managed but not assigned to any group, which means they have no group-based Jira access.",
        items,
    )


def _check_duplicate_email_accounts(users):
    email_to_accounts = defaultdict(list)
    for u in users:
        email = (u.get("email") or "").lower()
        if email:
            email_to_accounts[email].append(u["name"])
    items = [
        {"label": email, "accounts": ", ".join(names), "count": len(names)}
        for email, names in email_to_accounts.items() if len(names) > 1
    ]
    return _finding(
        "duplicate_email_accounts", "warning", "Users",
        "email addresses with multiple managed accounts",
        "Multiple managed accounts share the same email. These are likely duplicates that should be merged.",
        items,
    )


def _check_over_privileged_users(jira_spaces, users):
    managed_ids = {u["accountId"] for u in users}
    # {accountId: {displayName, projects: list}}
    admin_projects = defaultdict(lambda: {"name": "", "projects": []})
    for s in jira_spaces:
        for u in _human_users(s.get("users_with_access", [])):
            if u["accountId"] not in managed_ids:
                continue
            if any("admin" in r.lower() for r in u.get("roles", [])):
                admin_projects[u["accountId"]]["name"] = u["displayName"]
                admin_projects[u["accountId"]]["projects"].append(s["name"])
    items = [
        {"label": v["name"], "admin_projects": ", ".join(v["projects"]), "count": len(v["projects"])}
        for v in admin_projects.values() if len(v["projects"]) >= 3
    ]
    return _finding(
        "over_privileged_users", "warning", "Users",
        "users with Admin role across 3+ Jira projects",
        "These users hold admin roles on many projects. Review whether each assignment is intentional.",
        items,
    )


def _check_users_direct_jira_access(jira_spaces, users):
    managed_ids = {u["accountId"] for u in users}
    # {accountId: {displayName, projects: list}}
    direct_access = defaultdict(lambda: {"name": "", "projects": []})
    for s in jira_spaces:
        for u in _human_users(s.get("users_with_access", [])):
            if u["accountId"] in managed_ids:
                direct_access[u["accountId"]]["name"] = u["displayName"]
                direct_access[u["accountId"]]["projects"].append(s["name"])
    items = [
        {"label": v["name"], "projects": ", ".join(v["projects"])}
        for v in direct_access.values()
    ]
    return _finding(
        "users_direct_jira_access", "warning", "Users",
        "managed users with direct Jira project access",
        "Best practice is to assign access via groups, not directly. Migrate these users to appropriate groups.",
        items,
    )


# ── Jira checks ────────────────────────────────────────────────────────────────

def _check_jira_projects_direct_user_assignments(jira_spaces):
    items = [
        {"label": s["name"], "key": s["key"], "direct_users": len(_human_users(s.get("users_with_access", [])))}
        for s in jira_spaces if len(_human_users(s.get("users_with_access", []))) >= 2
    ]
    return _finding(
        "jira_projects_direct_user_assignments", "warning", "Jira",
        "Jira projects with multiple directly-assigned users",
        "Projects should use groups for access management. Migrate direct user assignments to groups.",
        items,
    )


def _check_jira_empty_group_assigned(jira_spaces, groups):
    group_members = {g["name"]: len(g.get("users", [])) for g in groups}
    items = []
    for s in jira_spaces:
        for ga in s.get("groups_with_access", []):
            member_count = group_members.get(ga["name"])
            if member_count is not None and member_count == 0:
                items.append({"label": s["name"], "key": s["key"], "group": ga["name"]})
    return _finding(
        "jira_empty_group_assigned", "warning", "Jira",
        "Jira projects with an empty group assigned",
        "These projects have groups with no members assigned. Remove the group assignment or populate the group.",
        items,
    )


def _check_jira_no_lead(jira_spaces):
    items = [
        {"label": s["name"], "key": s["key"], "type": s["type"]}
        for s in jira_spaces if not s.get("lead")
    ]
    return _finding(
        "jira_no_lead", "info", "Jira",
        "Jira projects with no lead assigned",
        "Every project should have an accountable lead. Assign one so there's a clear owner.",
        items,
    )


def _check_jira_no_group_access(jira_spaces):
    items = [
        {"label": s["name"], "key": s["key"]}
        for s in jira_spaces if not s.get("groups_with_access")
    ]
    return _finding(
        "jira_no_group_access", "info", "Jira",
        "Jira projects with no group-based access",
        "Access is not managed via groups for these projects. Group-based access is easier to audit and maintain.",
        items,
    )
