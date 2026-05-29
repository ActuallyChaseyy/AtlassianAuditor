import dotenv
import os
import base64
from handlers.http_util import paginate_jira_api, request_with_retry

dotenv.load_dotenv()
token = base64.b64encode(f"{os.environ['ATLASSIAN_USERNAME']}:{os.environ['ATLASSIAN_API_TOKEN']}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

def _get_role_id_map(tenant):
    """Returns {str(role_id): role_name} for all project roles in the tenant."""
    resp = request_with_retry(
        f"Roles ({tenant})", "get",
        f"https://{tenant}.atlassian.net/rest/api/3/role",
        headers=headers
    )
    if resp.status_code != 200:
        return {}
    return {str(r["id"]): r["name"] for r in resp.json()}

def _parse_holder(holder, role_map=None):
    match holder.get("type", ""):
        case "group":
            return {"type": "group", "name": holder.get("value") or holder.get("parameter", "")}
        case "projectRole":
            role_id = str(holder.get("value") or holder.get("parameter", ""))
            return {"type": "projectRole", "name": (role_map or {}).get(role_id, role_id)}
        case "user":
            return {"type": "user", "accountId": holder.get("parameter", "")}
        case "applicationRole":
            return {"type": "applicationRole", "name": holder.get("parameter", "")}
        case "anyone":
            return {"type": "anyone"}
        case t:
            return {"type": t, "name": holder.get("value") or holder.get("parameter", "")}

def get_permission_schemes(tenant):
    print(f"Fetching permission schemes for tenant {tenant}...")
    resp = request_with_retry(
        f"Permission Schemes ({tenant})", "get",
        f"https://{tenant}.atlassian.net/rest/api/3/permissionscheme?expand=permissions",
        headers=headers
    )
    if resp.status_code != 200:
        print(f"Failed to fetch permission schemes for {tenant}: {resp.status_code}")
        return []

    role_map = _get_role_id_map(tenant)

    schemes = []
    for scheme in resp.json().get("permissionSchemes", []):
        sid = scheme["id"]

        perm_map = {}
        for entry in scheme.get("permissions", []):
            key = entry["permission"]
            perm_map.setdefault(key, []).append(_parse_holder(entry["holder"], role_map))

        permissions = [{"permission": k, "holders": v} for k, v in sorted(perm_map.items())]

        schemes.append({
            "id": sid,
            "name": scheme["name"],
            "description": scheme.get("description", ""),
            "tenant": tenant,
            "project_count": 0,
            "projects": [],
            "permissions": permissions,
        })

    return schemes
