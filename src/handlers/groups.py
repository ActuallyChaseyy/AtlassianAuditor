import dotenv
import os
import time
from handlers.http_util import request_with_retry

dotenv.load_dotenv()
base_url = "https://api.atlassian.com/admin/v2"

# helper function to handle pagination of admin api 
# uses cursor pagination instead of count based - per https://developer.atlassian.com/cloud/admin/organization/rest/intro/#Pagination
def _paginate_api(context, url, headers): 
    cursor = None 
    while True: 
        params = {"cursor": cursor} if cursor else {}
        response = request_with_retry(context, "get", url, headers=headers, params=params)
        data = response.json()
        items = data.get("data", [])
        yield from items
        cursor = data.get("links", {}).get("next")
        if not cursor:
            break

def get_group_members(org_id, group_id, headers):
    time.sleep(1) # small delay to help avoid rate limits
    print(f"Fetching members for group {group_id}...")
    url = f"{base_url}/orgs/{org_id}/directories/-/users?groupIds={group_id}"
    return [
        {
            "accountId": member["accountId"],
            "accountType": member["accountType"],
            "name": member["name"],
            "email": member["email"],
            "status": member["accountStatus"],
        }
        for member in _paginate_api("Group Members", url, headers=headers)
    ]

def get_groups(org_id):
    print("Fetching groups for org...")
    url = f"{base_url}/orgs/{org_id}/directories/-/groups"
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    groups = [] 
    for group in _paginate_api("Groups", url, headers):
        groups.append({
            "id": group["id"],
            "name": group["name"],
            "description": group["description"],
            "directoryId": group["directoryId"], # which org the group belongs to (requires additional api call to resolve)
            "users": get_group_members(org_id, group["id"], headers)
        })
    return groups