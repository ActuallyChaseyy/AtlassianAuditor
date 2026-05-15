import dotenv
import os
import time
from handlers.http_util import paginate_api

dotenv.load_dotenv()
base_url = "https://api.atlassian.com/admin/v2"

def get_users(org_id):
    print("Fetching users for org...")
    url = f"{base_url}/orgs/{org_id}/directories/-/users?claimStatus=managed" # only returns managed users (internal staff) configured in admin.atlassian.com
    headers = {"Authorization": f"Bearer {os.environ['ADMIN_API_KEY']}"} 
    return [
        {
            "accountId": user["accountId"],
            "name": user["name"],
            "email": user["email"],
            "status": user["accountStatus"],
        }
        for user in paginate_api("Users", url, headers)
    ]