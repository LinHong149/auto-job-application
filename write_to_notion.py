#!/usr/bin/env python3
import os
import sys
import argparse
from datetime import date
from dotenv import load_dotenv
from notion_client import Client

# ==== CONFIG: property names in your Notion DB ====
NAME_PROP        = "Name"          # Title
ROLE_PROP        = "Role"          # Rich text
DATE_APPLIED_PROP= "Date Applied"  # Date
STATUS_PROP      = "Status"        # Status
STATUS_APPLIED   = "Applied"       # Status option
# ==================================================

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DB_ID = os.getenv("NOTION_DB_ID")

if not NOTION_TOKEN or not NOTION_DB_ID:
    print("ERROR: set NOTION_TOKEN and NOTION_DB_ID in your .env", file=sys.stderr)
    sys.exit(1)

notion = Client(auth=NOTION_TOKEN)

def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    if not u.startswith(("http://", "https://")):
        u = "https://" + u
    return u

def _extract_title_link(page) -> str:
    """Return the URL linked in the Title (Name) property, if any."""
    title = page["properties"][NAME_PROP]["title"]
    if not title:
        return ""
    # We take the first text chunk that has a link
    for blk in title:
        link = blk.get("text", {}).get("link", {})
        if link and link.get("url"):
            return link["url"].strip()
    return ""

def find_page_by_url_from_title_link(db_id: str, url: str):
    """
    Iterate the database and find a page whose Name (Title) has a hyperlink equal to url.
    Since we don't have a URL column, we dedupe by the Title's link.
    """
    cursor = None
    target = _normalize_url(url)
    while True:
        resp = notion.databases.query(
            database_id=db_id,
            page_size=100,
            start_cursor=cursor
        )
        for page in resp.get("results", []):
            linked = _extract_title_link(page)
            if _normalize_url(linked) == target:
                return page
        if not resp.get("has_more"):
            break
        cursor = resp.get("next_cursor")
    return None

def upsert_job(company: str, url: str, role: str):
    today_str = date.today().isoformat()
    url = _normalize_url(url)

    # Build properties payload
    props = {
        NAME_PROP: {
            "title": [{
                "type": "text",
                "text": {"content": company},
                "href": url,
            }]
        },
        ROLE_PROP: {
            "rich_text": [{
                "type": "text",
                "text": {"content": role}
            }]
        },
        DATE_APPLIED_PROP: {"date": {"start": today_str}},
        STATUS_PROP: {"select": {"name": STATUS_APPLIED}},  # <-- changed from "status" to "select"
    }

    existing = find_page_by_url_from_title_link(NOTION_DB_ID, url)
    if existing:
        page_id = existing["id"]
        notion.pages.update(page_id=page_id, properties=props)
        return ("updated", page_id)
    else:
        new_page = notion.pages.create(
            parent={"database_id": NOTION_DB_ID},
            properties=props
        )
        return ("created", new_page["id"])

def main():
    parser = argparse.ArgumentParser(description="Add/update a job in Notion. Dedupe by hyperlink on Name.")
    parser.add_argument("--company", required=True, help="Company name (will be the Title text)")
    parser.add_argument("--url", required=True, help="Job URL (used as the hyperlink on Title)")
    parser.add_argument("--role", required=True, help="Role description/title")
    args = parser.parse_args()

    action, page_id = upsert_job(args.company.strip(), args.url.strip(), args.role.strip())
    print(f"Successfully {action} page: {page_id}")

if __name__ == "__main__":
    main()