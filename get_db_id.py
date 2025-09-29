from notion_client import Client
from dotenv import load_dotenv
import os

load_dotenv()
notion = Client(auth=os.getenv("NOTION_TOKEN"))

res = notion.search(
    filter={"value": "database", "property": "object"},
    page_size=10,
)

for db in res["results"]:
    title = "".join([t["plain_text"] for t in db.get("title", [])])
    print("Title:", title or "(untitled)")
    print("Database ID:", db["id"])
    print()