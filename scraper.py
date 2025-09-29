import json, time, requests

RAW_URL = "https://raw.githubusercontent.com/SimplifyJobs/Summer2026-Internships/dev/.github/scripts/listings.json"

def fetch_listings():
    r = requests.get(RAW_URL, timeout=30)
    r.raise_for_status()
    return r.json()

def dedupe_by_url(rows):
    seen, out = set(), []
    for r in rows:
        url = (r.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        out.append({
            "company_name": r.get("company_name"),
            "title":        r.get("title"),
            "url":          url,
            "date_posted":  r.get("date_posted"),
            "active":       r.get("active", True),
        })
    return out

if __name__ == "__main__":
    rows = fetch_listings()
    rows = dedupe_by_url(rows)
    print("total:", len(rows))
    # (optional) write to a local file your bot can use
    with open("listings.json", "w") as f:
        json.dump(rows, f, indent=2)