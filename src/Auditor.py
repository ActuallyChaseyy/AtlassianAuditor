import dotenv
import os
import json

from handlers import groups, tenants, users, jira_spaces, permission_schemes
from report import generator
from report.checks import run_checks

dotenv.load_dotenv()

# When TRUE, the script will load data from local audit_data.json file instead of API calls.
# Must be ran in live mode at least once to generate the cache. Useful for development and testing.
DEBUG_MODE = False
CACHE_FILE = "audit_data.json"

# Tenant subdomains to include in the audit (e.g. ["example"] for example.atlassian.net).
# Leave empty to scan all tenants.
SCAN_TENANTS = []

def main():
    if DEBUG_MODE:
        print(f"DEBUG_MODE: loading data from {CACHE_FILE}...")
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            audit_data = json.load(f)
    else:
        tenant_list = tenants.get_tenants(os.environ["ORG_ID"])
        if SCAN_TENANTS:
            scan_lower = {t.lower() for t in SCAN_TENANTS}
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

        # Write cache file for debug mode
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        print(f"Audit data cached to {CACHE_FILE}")

    # Run checks and add to audit_data map
    audit_data["suggestions"] = run_checks(audit_data)
    print("Generating report...")
    generator.generate_report(audit_data)

if __name__ == "__main__":
    main()