import argparse
import dotenv
import os
import json

from handlers import groups, tenants, users, jira_spaces, permission_schemes
from report import generator
from report.checks import run_checks
from report.checks_configured import run_checks as run_configured_checks

dotenv.load_dotenv()

# When TRUE, the script will load data from local audit_data.json file instead of API calls.
# Must be ran in live mode at least once to generate the cache. Useful for development and testing.
DEBUG_MODE = False
CACHE_FILE = "audit_data.json"

def main():
    parser = argparse.ArgumentParser(description="Atlassian Auditor")
    parser.add_argument(
        "--tenants", nargs="+", metavar="TENANT",
        help="Tenant subdomains to scan (e.g. --tenants foo bar). Scans all if omitted."
    )
    parser.add_argument("--debug", action="store_true", help="Load data from cache instead of API.")
    args = parser.parse_args()

    debug_mode = args.debug or DEBUG_MODE
    scan_tenants = args.tenants or []

    if debug_mode:
        print(f"DEBUG_MODE: loading data from {CACHE_FILE}...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
        if scan_tenants:
            scan_lower = {t.lower() for t in scan_tenants}
            filtered_tenant_map = {did: name for did, name in audit_data["tenant_map"].items()
                                   if name.lower() in scan_lower}
            filtered_names = {n.lower() for n in filtered_tenant_map.values()}
            audit_data["tenant_map"] = filtered_tenant_map
            audit_data["groups"] = [g for g in audit_data["groups"] if g["directoryId"] in filtered_tenant_map]
            audit_data["jira_spaces"] = [s for s in audit_data["jira_spaces"] if s.get("tenant", "").lower() in filtered_names]
            audit_data["permission_schemes"] = [s for s in audit_data["permission_schemes"] if s["tenant"].lower() in filtered_names]
            print(f"Filtering to tenants: {list(filtered_tenant_map.values())}")
    else:
        tenant_list = tenants.get_tenants(os.environ["ORG_ID"])
        if scan_tenants:
            scan_lower = {t.lower() for t in scan_tenants}
            tenant_list = [t for t in tenant_list if t["name"].lower() in scan_lower]
            print(f"Filtering to tenants: {[t['name'] for t in tenant_list]}")

        # lookup list to convert directoryId to tenant name when rendering report
        tenant_map = {t["directoryId"]: t["name"] for t in tenant_list}

        all_groups = groups.get_groups(os.environ["ORG_ID"])

        # data structure with returned atlassian data to be used with report generation, checks and cache.
        audit_data = {
            "tenant_map": tenant_map,
            "groups": [g for g in all_groups if g["directoryId"] in tenant_map],
            "users": users.get_users(os.environ["ORG_ID"]),
            "permission_schemes": [s for name in tenant_map.values() for s in permission_schemes.get_permission_schemes(name)],
            "jira_spaces": [space for name in tenant_map.values() for space in jira_spaces.get_jira_spaces(name)]
        }

        # Derive scheme->project mapping from jira_spaces and populate permission_schemes.
        # The project search API does not expose permissionScheme via expand, so we use per-project
        # calls in jira_spaces and build the reverse mapping here to avoid redundant API calls.
        scheme_projects = {}
        for space in audit_data["jira_spaces"]:
            sid = space.get("permission_scheme_id")
            if sid is not None:
                scheme_projects.setdefault(sid, []).append({"key": space["key"], "name": space["name"]})
        for scheme in audit_data["permission_schemes"]:
            projects = scheme_projects.get(scheme["id"], [])
            scheme["projects"] = projects
            scheme["project_count"] = len(projects)

        # Write cache file for debug mode
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        print(f"Audit data cached to {CACHE_FILE}")

    # Run checks and add to audit_data map
    audit_data["suggestions"] = run_checks(audit_data) + run_configured_checks(audit_data)
    print("Generating report...")
    generator.generate_report(audit_data)

if __name__ == "__main__":
    main()