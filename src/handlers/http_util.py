import requests
import time 

# Maximum number of retries for failed requests
max_retries = 5 
retryable_statuses = {500, 502, 503, 504}  # Server errors that should be retried

def request_with_retry(method, url, **kwargs): 
    for attempt in range(max_retries):
        try: 
            response = requests.request(method, url, **kwargs)
        except requests.exceptions.RequestException as e:
            # Network error (timeout, connection refused - always retry)
            if attempt < max_retries - 1:
                print(f"Network error - Retrying in 5 seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(5)
                continue
            raise
        
        if response.status_code not in retryable_statuses and response.status_code != 429:
            return response  # Success or non-retryable error
        
        wait = int(response.headers.get("Retry-After", 5))  # Use Retry-After header if present
        print(f"{response.status_code} - Retrying in {wait} seconds... (Attempt {attempt + 1}/{max_retries})")
        time.sleep(wait)

    return response # Return the last response after exhausting retries