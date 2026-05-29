import dotenv
import os
import base64
from handlers.http_util import paginate_jira_api, request_with_retry

dotenv.load_dotenv()
token = base64.b64encode(f"{os.environ['ATLASSIAN_USERNAME']}:{os.environ['ATLASSIAN_API_TOKEN']}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

def _get_project_roles(tenant, project_key):
    """Returns (users_with_access, groups_with_access) for a project."""
    resp = request_with_retry(
        f"Roles ({project_key})", "get",
        f"https://{tenant}.atlassian.net/rest/api/2/project/{project_key}/role",
        headers=headers
    )
    if resp.status_code != 200:
        return [], []

    users_map = {}
    groups_map = {}

    for role_name, role_url in resp.json().items():
        role_resp = request_with_retry(f"Role detail ({project_key}/{role_name})", "get", role_url, headers=headers)
        if role_resp.status_code != 200:
            continue
        for actor in role_resp.json().get("actors", []):
            if actor["type"] == "atlassian-user-role-actor":
                account_id = actor.get("actorUser", {}).get("accountId")
                if account_id:
                    if account_id not in users_map:
                        users_map[account_id] = {"accountId": account_id, "displayName": actor["displayName"], "roles": []}
                    users_map[account_id]["roles"].append(role_name)
            elif actor["type"] == "atlassian-group-role-actor":
                group_name = actor.get("actorGroup", {}).get("name") or actor["displayName"]
                if group_name not in groups_map:
                    groups_map[group_name] = {
                        "name": group_name,
                        "groupId": actor.get("actorGroup", {}).get("groupId"),
                        "roles": []
                    }
                groups_map[group_name]["roles"].append(role_name)

    return list(users_map.values()), list(groups_map.values())

def _get_project_permission_scheme_id(tenant, project_key):
    """Returns the permission scheme ID for a project, or None on failure."""
    resp = request_with_retry(
        f"Permission Scheme ({project_key})", "get",
        f"https://{tenant}.atlassian.net/rest/api/3/project/{project_key}/permissionscheme",
        headers=headers
    )
    return resp.json().get("id") if resp.status_code == 200 else None

def get_jira_spaces(tenant):
    print(f"Fetching Jira spaces for tenant {tenant}...")
    url = f"https://{tenant}.atlassian.net/rest/api/3/project/search"
    spaces = []
    for space in paginate_jira_api(f"Jira Spaces ({tenant})", url, headers):
        print(f"Found space: {space['key']} - {space['name']}")
        users_with_access, groups_with_access = _get_project_roles(tenant, space["key"])
        permission_scheme_id = _get_project_permission_scheme_id(tenant, space["key"])
        spaces.append({
            "id": space["id"],
            "key": space["key"],
            "name": space["name"],
            "type": space["projectTypeKey"],
            "tenant": tenant,
            "lead": space["lead"]["displayName"] if space.get("lead") else None,
            "permission_scheme_id": permission_scheme_id,
            "users_with_access": users_with_access,
            "groups_with_access": groups_with_access,
        })
    return spaces