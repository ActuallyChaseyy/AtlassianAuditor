import dotenv
import os
import time
from handlers.http_util import request_with_retry, paginate_admin_api

dotenv.load_dotenv()
base_url = "https://api.atlassian.com/admin/v2"

def get_group_members(org_id, group_id, headers):
    time.sleep(0.5) # small delay to help avoid rate limits
    print(f"Fetching members for group {group_id}...")
    url = f"{base_url}/orgs/{org_id}/directories/-/users?groupIds={group_id}"
    return [
        {
            "accountId": member["accountId"],
            "name": member["name"],
            "email": member["email"],
            "status": member["accountStatus"],
        }
        for member in paginate_admin_api("Group Members", url, headers=headers)
    ]

def get_groups(org_id):
    print("Fetching groups for org...")
    url = f"{base_url}/orgs/{org_id}/directories/-/groups"
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    groups = [] 
    for group in paginate_admin_api("Groups", url, headers):
        groups.append({
            "id": group["id"],
            "name": group["name"],
            "description": group["description"],
            "directoryId": group["directoryId"], # which org the group belongs to (requires additional api call to resolve)
            "users": get_group_members(org_id, group["id"], headers)
        })
    return groups