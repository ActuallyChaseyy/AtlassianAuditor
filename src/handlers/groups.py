import dotenv
import os
from handlers.http_util import request_with_retry

dotenv.load_dotenv()
base_url = "https://api.atlassian.com/admin/v2"

# helper function to handle pagination of admin api 
# uses cursor pagination instead of count based - per https://developer.atlassian.com/cloud/admin/organization/rest/intro/#Pagination
def _paginate_api(url, headers): 
    cursor = None 
    while True: 
        params = {"cursor": cursor} if cursor else {}
        response = request_with_retry("get", url, headers=headers, params=params)
        data = response.json()
        groups = data.get("data", [])
        if not groups:
            break
        yield from groups
        cursor = data.get("links", {}).get("next")
        if not cursor: 
            break 

def get_groups(org_id):
    url = f"{base_url}/orgs/{org_id}/directories/-/groups"
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    return [
        {
            "id": group["id"],
            "name": group["name"],
            "description": group["description"],
            "directory": group["directoryId"], # which org the group belongs to (requires additional api call to resolve)
        }
        for group in _paginate_api(url, headers)
    ]