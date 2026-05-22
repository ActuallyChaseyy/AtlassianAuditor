import dotenv 
import os 
import base64
from handlers.http_util import paginate_jira_api

dotenv.load_dotenv()
token = base64.b64encode(f"{os.environ['ATLASSIAN_USERNAME']}:{os.environ['ATLASSIAN_API_TOKEN']}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

def get_jira_spaces(tenant):
    print(f"Fetching Jira spaces for tenant {tenant}...")
    url = f"https://{tenant}.atlassian.net/rest/api/2/project/search"
    return [
        {
            "id": space["id"],
            "key": space["key"],
            "name": space["name"],
            "type": space["projectTypeKey"],
            "lead": space["lead"]["displayName"] if space.get("lead") else None
        }
        for space in paginate_jira_api(f"Jira Spaces ({tenant})", url, headers)
    ]



