import dotenv
import os
from handlers.http_util import request_with_retry

dotenv.load_dotenv()

def _paginate_api(url, headers): 
    cursor = None 
    while True: 
        params = {"cursor": cursor} if cursor else {}
        response = request_with_retry("get", url, headers=headers, params=params)
        data = response.json()
        tenants = data.get("data", [])
        if not tenants:
            break
        yield from tenants
        cursor = data.get("links", {}).get("next")
        if not cursor: 
            break 

def get_tenants(org_id):
    url = f"https://api.atlassian.com/admin/v2/orgs/{org_id}/directories"
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    return [
        {
            "directoryId": tenant["directoryId"],
            "name": tenant["name"]
        }
        for tenant in _paginate_api(url, headers)
    ]