import requests

CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"


def fetch_organic_results(query, api_key, cx, num=10, gl=None, lr=None, hl=None, timeout=20):
    params = {
        "key": api_key,
        "cx": cx,
        "q": query,
        "num": max(1, min(num, 10)),
    }
    if gl:
        params["gl"] = gl
    if lr:
        params["lr"] = lr
    if hl:
        params["hl"] = hl

    resp = requests.get(CSE_ENDPOINT, params=params, timeout=timeout)
    if resp.status_code == 429 or resp.status_code == 403:
        raise RuntimeError(
            "Google Custom Search API refused the request "
            f"(HTTP {resp.status_code}). On the free tier you get 100 queries/day; "
            "check your quota in the Google Cloud Console."
        )
    resp.raise_for_status()

    items = resp.json().get("items") or []
    results = []
    for i, item in enumerate(items, start=1):
        results.append(
            {
                "rank": i,
                "url": item.get("link", ""),
                "serp_title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
            }
        )
    return results
