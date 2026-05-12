import requests

def web_get(url):
    if not url.startswith("http"):
        return {"error": "invalid url"}

    r = requests.get(url, timeout=5)

    return {
        "status": r.status_code,
        "text": r.text[:500]
    }