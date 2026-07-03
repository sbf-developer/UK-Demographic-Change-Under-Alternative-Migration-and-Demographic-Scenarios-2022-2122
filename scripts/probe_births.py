"""Probe mother COB in NM_203_1."""
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.config import RAW_DIR

http = CachedHTTPClient("https://www.nomisweb.co.uk/api/v01", RAW_DIR / "nomis" / "cache")
r = http.get_json(
    "/dataset/NM_203_1.data.json",
    params={
        "geography": "2092957703",
        "date": "2022",
        "measures": "20100",
        "gender": "0",
        "multiple": "0",
        "registration_type": "0",
        "age_of_mother": "0",
    },
)
cobs = sorted({o["cob_mother"]["description"] for o in r["obs"]})
print("cob categories", len(cobs))
for c in cobs[:20]:
    print(" ", c)
http.close()
