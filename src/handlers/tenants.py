import dotenv
import os
from handlers.http_util import paginate_admin_api

dotenv.load_dotenv()

def get_tenants(org_id):
    print("Fetching all tenants for org...")
    url = f"https://api.atlassian.com/admin/v2/orgs/{org_id}/directories"
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    return [
        {
            "directoryId": tenant["directoryId"],
            "name": tenant["name"]
        }
        for tenant in paginate_admin_api("Tenants", url, headers)
    ]