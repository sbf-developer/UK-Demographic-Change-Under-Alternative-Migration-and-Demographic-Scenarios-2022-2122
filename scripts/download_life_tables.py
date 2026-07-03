"""Download ONS national life tables xlsx."""
import re
import httpx
from pathlib import Path

page = "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/lifeexpectancies/datasets/nationallifetablesunitedkingdomreferencetables"
r = httpx.get(page, follow_redirects=True, timeout=30)
uris = re.findall(r"file\?uri=([^\"'&]+)", r.text, re.I)
print("found", len(uris), "uris")
for u in uris:
    if "2020" in u or "2022" in u or "current" in u:
        print(u)
        url = "https://www.ons.gov.uk/file?uri=" + u
        resp = httpx.get(url, follow_redirects=True, timeout=60)
        print("  download", resp.status_code, len(resp.content))
        if resp.status_code == 200 and len(resp.content) > 10000:
            out = Path("data/raw/ons/life_tables/life_tables_uk.xlsx")
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(resp.content)
            print("  saved", out)
