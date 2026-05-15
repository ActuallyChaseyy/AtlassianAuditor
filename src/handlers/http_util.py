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

# helper function to handle pagination of admin api 
# uses cursor pagination instead of count based - per https://developer.atlassian.com/cloud/admin/organization/rest/intro/#Pagination
def paginate_api(context, url, headers): 
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