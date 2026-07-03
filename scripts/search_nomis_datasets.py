"""Search Nomis for deaths and births datasets."""
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.config import RAW_DIR

http = CachedHTTPClient("https://www.nomisweb.co.uk/api/v01", RAW_DIR / "nomis" / "cache")
for ds_id in range(1, 250):
    ds = f"NM_{ds_id}_1"
    try:
        d = http.get_json(f"/dataset/{ds}.def.sdmx.json")
        kfs = d.get("structure", {}).get("keyfamilies", {}).get("keyfamily", [])
        if not kfs:
            continue
        name = str(kfs[0].get("name", "")).lower()
        if any(k in name for k in ["death", "birth", "live birth", "mortality", "life table"]):
            print(ds, kfs[0].get("name", {}).get("value", "")[:80])
    except Exception:
        pass
http.close()
