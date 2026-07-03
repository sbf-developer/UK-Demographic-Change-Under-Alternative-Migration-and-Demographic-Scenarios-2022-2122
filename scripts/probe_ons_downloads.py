"""Find life tables and deaths dataset file URIs on ONS."""
import re
import httpx

for page in [
    "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/lifeexpectancies/datasets/nationallifetablesunitedkingdomreferencetables",
    "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/datasets/deathregistrationssummarytables",
]:
    r = httpx.get(page, follow_redirects=True, timeout=30)
    print("===", page.split("/")[-1], r.status_code)
    for pat in [r"file\?uri=([^\"']+)", r"/peoplepopulationandcommunity[^\"']+\.xlsx"]:
        found = re.findall(pat, r.text, re.I)
        for f in sorted(set(found))[:15]:
            print(" ", f[:120])
