import dotenv 
import os 

from handlers import groups, tenants, users
from report import generator

dotenv.load_dotenv()
def main():
    tenant_list = tenants.get_tenants(os.environ["ORG_ID"])
    # lookup list to convert directoryId to tenant name when rendering report
    tenant_map = {t["directoryId"]: t["name"] for t in tenant_list}

    # data structure with returned values from atlassian to pass into report generator
    audit_data = {
        "tenant_map": tenant_map,
        "groups": groups.get_groups(os.environ["ORG_ID"]),
        "users": users.get_users(os.environ["ORG_ID"])
        # "permissions": 
        # "jira_spaces": 
    }

    print("Generating report...")
    generator.generate_report(audit_data)

if __name__ == "__main__":
    main()