import dotenv
import os
import base64
from handlers.http_util import paginate_jira_api, request_with_retry

dotenv.load_dotenv()
token = base64.b64encode(f"{os.environ['ATLASSIAN_USERNAME']}:{os.environ['ATLASSIAN_API_TOKEN']}".encode()).decode()
headers = {"Authorization": f"Basic {token}"}

def _scheme_to_projects_map(tenant):
    """Returns {scheme_id: [{"key": ..., "name": ...}]} for all projects in a tenant."""
    url = f"https://{tenant}.atlassian.net/rest/api/3/project/search?expand=permissionScheme"
    scheme_map = {}
    for project in paginate_jira_api(f"Projects (permScheme) ({tenant})", url, headers):
        ps = project.get("permissionScheme")
        if not ps:
            continue
        sid = ps["id"]
        scheme_map.setdefault(sid, []).append({"key": project["key"], "name": project["name"]})
    return scheme_map

def _parse_holder(holder):
    match holder.get("type", ""):
        case "group" | "projectRole":
            return {"type": holder["type"], "name": holder.get("value") or holder.get("parameter", "")}
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

    scheme_map = _scheme_to_projects_map(tenant)

    schemes = []
    for scheme in resp.json().get("permissionSchemes", []):
        sid = scheme["id"]

        perm_map = {}
        for entry in scheme.get("permissions", []):
            key = entry["permission"]
            perm_map.setdefault(key, []).append(_parse_holder(entry["holder"]))

        permissions = [{"permission": k, "holders": v} for k, v in sorted(perm_map.items())]
        projects = scheme_map.get(sid, [])

        schemes.append({
            "id": sid,
            "name": scheme["name"],
            "description": scheme.get("description", ""),
            "tenant": tenant,
            "project_count": len(projects),
            "projects": projects,
            "permissions": permissions,
        })

    return schemes