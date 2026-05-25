import dotenv 
import os 

from handlers import groups, tenants, users, jira_spaces
from report import generator
from report.checks import run_checks

dotenv.load_dotenv()
def main():
    tenant_list = tenants.get_tenants(os.environ["ORG_ID"])
    # lookup list to convert directoryId to tenant name when rendering report
    tenant_map = {t["directoryId"]: t["name"] for t in tenant_list}

    # data structure with returned values from atlassian to pass into report generator
    audit_data = {
        "tenant_map": tenant_map,
        "groups": groups.get_groups(os.environ["ORG_ID"]),
        "users": users.get_users(os.environ["ORG_ID"]),
        # "permissions":
        "jira_spaces": [space for name in tenant_map.values() for space in jira_spaces.get_jira_spaces(name)]
    }

    audit_data["suggestions"] = run_checks(audit_data)
    print("Generating report...")
    generator.generate_report(audit_data)

if __name__ == "__main__":
    main()