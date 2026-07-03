"""Nomis API client for Census 2021 England and Wales tables."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from ukethnicproj.config import PROJECT_ROOT, RAW_DIR
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.data_sources.manifest import ManifestRegistry

_CODES_PATH = PROJECT_ROOT / "configs" / "nomis_nm2132_codes.yml"


class NomisClient:
    """Client for https://www.nomisweb.co.uk/api/v01."""

    BASE_URL = "https://www.nomisweb.co.uk/api/v01"
    C2021RM032_DATASET_ID = "NM_2132"
    C2021RM032_CODE = "C2021RM032"

    def __init__(self, cache_dir: Path | None = None) -> None:
        cache = cache_dir or RAW_DIR / "nomis" / "cache"
        self.http = CachedHTTPClient(self.BASE_URL, cache)
        self.manifest = ManifestRegistry(RAW_DIR / "nomis" / "manifest.jsonl")
        self._codes = self._load_codes()

    def _load_codes(self) -> dict[str, Any]:
        if _CODES_PATH.exists():
            with _CODES_PATH.open(encoding="utf-8") as handle:
                return yaml.safe_load(handle)
        return {}

    def dataset_definition(self, dataset_id: str | None = None) -> dict[str, Any]:
        """Retrieve SDMX-JSON dataset definition."""
        ds = dataset_id or self.C2021RM032_DATASET_ID
        return self.http.get_json(f"/dataset/{ds}.def.sdmx.json")

    def discover_c2021rm032_dimensions(self) -> dict[str, Any]:
        """Discover dimension structure for C2021RM032."""
        definition = self.dataset_definition()
        keyfamilies = (
            definition.get("structure", {})
            .get("keyfamilies", {})
            .get("keyfamily", [])
        )
        dimensions = []
        if keyfamilies:
            dimensions = [
                d.get("conceptref")
                for d in keyfamilies[0].get("components", {}).get("dimension", [])
            ]
        return {
            "dataset_id": self.C2021RM032_DATASET_ID,
            "dataset_code": self.C2021RM032_CODE,
            "dimensions": dimensions,
            "definition": definition,
            "codes_config": self._codes,
        }

    def fetch_c2021rm032(
        self,
        *,
        geography_type: str | None = None,
        geography: str = "0",
        sex_codes: str | None = None,
        age_codes: str | None = None,
        ethnic_codes: str | None = None,
        output_dir: Path | None = None,
    ) -> Path:
        """
        Fetch C2021RM032 (ethnic group by sex by age) from Nomis.

        Uses NM_2132 with Nomis-specific dimension parameter names.
        Geography code 0 with TYPE480 returns all standard regions.
        """
        out_dir = output_dir or RAW_DIR / "nomis" / "c2021rm032"
        out_dir.mkdir(parents=True, exist_ok=True)

        discovery = self.discover_c2021rm032_dimensions()
        discovery_path = out_dir / "c2021rm032_discovery.json"
        discovery_path.write_text(json.dumps(discovery, indent=2, default=str), encoding="utf-8")

        gtype = geography_type or self._codes.get("GEOGRAPHY_TYPE_REGIONS", "TYPE480")
        ethnic = ethnic_codes or ",".join(self._codes.get("ETHNIC_CODES", []))
        age = age_codes or ",".join(self._codes.get("AGE_CODES", []))
        sex = sex_codes or ",".join(self._codes.get("SEX_CODES", []))
        measures = self._codes.get("MEASURES_CODE", "20100")

        # Fetch all regions by querying each region code
        region_codes = self._codes.get("REGION_CODES", [])
        if geography == "0" and region_codes:
            all_obs: list[dict[str, Any]] = []
            for rc in region_codes:
                params = {
                    "geography": f"{gtype},{rc}",
                    self._codes.get("DIM_ETHNIC", "c2021_eth_20"): ethnic,
                    self._codes.get("DIM_AGE", "c2021_age_6"): age,
                    self._codes.get("DIM_SEX", "c_sex"): sex,
                    self._codes.get("DIM_MEASURES", "measures"): measures,
                }
                chunk = self.http.get_json(
                    f"/dataset/{self.C2021RM032_DATASET_ID}.data.json",
                    params=params,
                )
                if chunk.get("error"):
                    raise RuntimeError(
                        f"Nomis query error for region {rc}: {chunk['error']}"
                    )
                all_obs.extend(chunk.get("obs", []))
            data: dict[str, Any] = {"obs": all_obs, "header": {"regions_fetched": len(region_codes)}}
        else:
            params = {
                "geography": f"{gtype},{geography}",
                self._codes.get("DIM_ETHNIC", "c2021_eth_20"): ethnic,
                self._codes.get("DIM_AGE", "c2021_age_6"): age,
                self._codes.get("DIM_SEX", "c_sex"): sex,
                self._codes.get("DIM_MEASURES", "measures"): measures,
            }
            data = self.http.get_json(
                f"/dataset/{self.C2021RM032_DATASET_ID}.data.json",
                params=params,
            )
            if data.get("error"):
                raise RuntimeError(f"Nomis query error: {data['error']}")

        out_path = out_dir / f"c2021rm032_{gtype}_{geography}.json"
        out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

        n_obs = len(data.get("obs", []))
        self.manifest.register(
            filepath=out_path,
            source_organisation="Nomis (Office for National Statistics)",
            dataset_title="C2021RM032: Ethnic group by sex by age",
            dataset_identifier=self.C2021RM032_CODE,
            source_location=(
                f"{self.BASE_URL}/dataset/{self.C2021RM032_DATASET_ID}.data.json"
            ),
            reference_period="Census Day 21 March 2021",
            geographical_coverage=f"Nomis {gtype} geography code {geography}",
            variable_definitions=(
                f"Ethnic group, sex, age; {n_obs} observations retrieved"
            ),
            licence="Open Government Licence v3.0",
            processing_script="ukethnicproj.data_sources.nomis.NomisClient.fetch_c2021rm032",
            known_limitations=(
                "Age bands are broad (6 categories). "
                "TYPE480 returns regions; England total requires aggregation. "
                "Dimension codes from configs/nomis_nm2132_codes.yml."
            ),
        )
        return out_path

    def parse_c2021rm032_to_dataframe(self, json_path: Path) -> Any:
        """Parse Nomis JSON response into a tidy DataFrame."""
        import pandas as pd

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        observations = payload.get("obs", [])
        if not observations:
            raise ValueError(f"No observations found in {json_path}")

        records: list[dict[str, Any]] = []
        for obs in observations:
            records.append(
                {
                    "geography_code": obs.get("geography", {}).get("geogcode"),
                    "geography_name": obs.get("geography", {}).get("description"),
                    "geography_value": obs.get("geography", {}).get("value"),
                    "sex_value": obs.get("c_sex", {}).get("value"),
                    "sex_name": obs.get("c_sex", {}).get("description"),
                    "age_value": obs.get("c2021_age_6", {}).get("value"),
                    "age_name": obs.get("c2021_age_6", {}).get("description"),
                    "ethnic_value": obs.get("c2021_eth_20", {}).get("value"),
                    "ethnic_name": obs.get("c2021_eth_20", {}).get("description"),
                    "count": obs.get("obs_value", {}).get("value"),
                }
            )
        return pd.DataFrame(records)

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> NomisClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
