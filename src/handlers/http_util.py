import requests
import time 

# Maximum number of retries for failed requests
max_retries = 5 
retryable_statuses = {500, 502, 503, 504}  # Server errors that should be retried

def request_with_retry(context, method, url, **kwargs): 
    for attempt in range(max_retries):
        try: 
            response = requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            # Network error (timeout, connection refused - always retry)
            if attempt < max_retries - 1:
                print(f"Network error - {context} - Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            raise
        
        if response.status_code not in retryable_statuses and response.status_code != 429:
            return response  # Success or non-retryable error
        
        wait = int(response.headers.get("Retry-After", 5))  # Use Retry-After header if present
        print(f"{response.status_code} - {context} - Retrying in {wait} seconds... (Attempt {attempt + 1}/{max_retries})")
        time.sleep(wait)

    return response # Return the last response after exhausting retries

# cursor-based pagination for the Atlassian admin API
# https://developer.atlassian.com/cloud/admin/organization/rest/intro/#Pagination
def paginate_admin_api(context, url, headers):
    cursor = None
    base_url = url.split("?")[0]
    initial_params = dict(param.split("=", 1) for param in url.split("?")[1].split("&")) if "?" in url else {}
    while True:
        params = {"cursor": cursor} if cursor else initial_params
        response = request_with_retry(context, "get", base_url, headers=headers, params=params)
        data = response.json()
        items = data.get("data", [])
        yield from items
        cursor = data.get("links", {}).get("next")
        if not cursor:
            break

# page-based pagination for the Jira REST API
def paginate_jira_api(context, url, headers):
    start = 0
    max_results = 50
    while True:
        response = request_with_retry(context, "get", url, headers=headers, params={"startAt": start, "maxResults": max_results})
        data = response.json()
        items = data.get("values", [])
        yield from items
        start += len(items)
        if data.get("isLast", True) or not items:
            break