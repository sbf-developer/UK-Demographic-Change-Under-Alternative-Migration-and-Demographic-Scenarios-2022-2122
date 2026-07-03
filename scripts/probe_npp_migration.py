"""Find NPP migration machine-readable dataset."""
import re
import httpx

page = "https://www.ons.gov.uk/peoplepopulationandcommunity/populationandmigration/populationprojections/datasets/v4internationalmigrationinpopulationprojections2022based"
r = httpx.get(page, follow_redirects=True, timeout=30)
print("status", r.status_code)
uris = re.findall(r"file\?uri=([^\"'&]+)", r.text, re.I)
for u in uris[:10]:
    print(u)
