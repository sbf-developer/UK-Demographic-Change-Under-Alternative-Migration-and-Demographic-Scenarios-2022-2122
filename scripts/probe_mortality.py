"""Probe Nomis mortality with England and Wales geography."""
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.config import RAW_DIR

http = CachedHTTPClient("https://www.nomisweb.co.uk/api/v01", RAW_DIR / "nomis" / "cache")

for geo in ["2092957703", "2092957699", "2013265930"]:
    for cause in ["0", "1", "2", "10001"]:
        r = http.get_json(
            "/dataset/NM_161_1.data.json",
            params={
                "geography": geo,
                "date": "2022",
                "measures": "20100",
                "gender": "1,2",
                "age": "30",
                "cause_of_death": cause,
            },
        )
        n = len(r.get("obs", []))
        if n:
            print("geo", geo, "cause", cause, "obs", n, r["obs"][0]["obs_value"])
            break
        elif r.get("error") and cause == "0":
            print("geo", geo, "err", r["error"])
http.close()
