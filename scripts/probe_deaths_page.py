"""Find death registration download links."""
import re
import httpx

url = "https://www.ons.gov.uk/peoplepopulationandcommunity/birthsdeathsandmarriages/deaths/bulletins/deathsregisteredinenglandandwales/2022"
r = httpx.get(url, follow_redirects=True, timeout=30)
paths = re.findall(r"/peoplepopulationandcommunity[^\"'\\s]+", r.text)
files = sorted({p for p in paths if "xlsx" in p.lower() or "csv" in p.lower()})
for f in files[:20]:
    print(f)
