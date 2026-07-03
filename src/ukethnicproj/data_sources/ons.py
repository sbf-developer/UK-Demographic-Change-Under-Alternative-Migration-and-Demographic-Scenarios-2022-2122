"""ONS Beta API client."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ukethnicproj.config import RAW_DIR
from ukethnicproj.data_sources.base import CachedHTTPClient
from ukethnicproj.data_sources.manifest import ManifestRegistry


class ONSClient:
    """Client for https://api.beta.ons.gov.uk/v1."""

    BASE_URL = "https://api.beta.ons.gov.uk/v1"

    def __init__(self, cache_dir: Path | None = None) -> None:
        cache = cache_dir or RAW_DIR / "ons" / "cache"
        self.http = CachedHTTPClient(self.BASE_URL, cache)
        self.manifest = ManifestRegistry(RAW_DIR / "ons" / "manifest.jsonl")

    def list_datasets(self, *, limit: int = 100, offset: int = 0) -> dict[str, Any]:
        return self.http.get_json("/datasets", params={"limit": limit, "offset": offset})

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        return self.http.get_json(f"/datasets/{dataset_id}")

    def get_editions(self, dataset_id: str) -> dict[str, Any]:
        return self.http.get_json(f"/datasets/{dataset_id}/editions")

    def get_latest_version(self, dataset_id: str, edition: str = "time-series") -> dict[str, Any]:
        return self.http.get_json(f"/datasets/{dataset_id}/editions/{edition}/versions")

    def get_census_observations(
        self,
        *,
        population_type: str = "UR",
        area_type: str = "ctry",
        area_code: str = "E92000001",
        dimensions: list[str],
    ) -> dict[str, Any]:
        """Query Census 2021 custom observations endpoint."""
        dim_param = ",".join(dimensions)
        params = {
            "area-type": f"{area_type},{area_code}",
            "dimensions": dim_param,
        }
        return self.http.get_json(
            f"/population-types/{population_type}/census-observations",
            params=params,
        )

    def get_rm032_metadata(self) -> dict[str, Any]:
        """Retrieve metadata for Census 2021 RM032 (ethnic group by sex by age)."""
        return self.get_dataset("RM032")

    def fetch_rm032_json(
        self,
        *,
        area_code: str = "E92000001",
        output_dir: Path | None = None,
    ) -> Path:
        """Attempt to fetch RM032 observations via ONS API."""
        out_dir = output_dir or RAW_DIR / "ons" / "rm032"
        out_dir.mkdir(parents=True, exist_ok=True)

        metadata = self.get_rm032_metadata()
        meta_path = out_dir / f"rm032_metadata_{area_code}.json"
        meta_path.write_text(
            __import__("json").dumps(metadata, indent=2), encoding="utf-8"
        )

        # RM032 is available via editions/2021/versions/1
        try:
            data = self.http.get_json(
                "/datasets/RM032/editions/2021/versions/1/json",
                params={"area-type": f"ctry,{area_code}"},
            )
            out_path = out_dir / f"rm032_{area_code}.json"
            out_path.write_text(__import__("json").dumps(data, indent=2), encoding="utf-8")

            self.manifest.register(
                filepath=out_path,
                source_organisation="Office for National Statistics",
                dataset_title="Ethnic group by sex by age (RM032)",
                dataset_identifier="RM032",
                source_location=f"{self.BASE_URL}/datasets/RM032",
                reference_period="Census Day 21 March 2021",
                geographical_coverage=area_code,
                variable_definitions="Ethnic group, sex, age (broad bands)",
                licence="Open Government Licence v3.0",
                processing_script="ukethnicproj.data_sources.ons.ONClient.fetch_rm032_json",
                known_limitations=(
                    "Age provided in six broad bands only (not single-year-of-age). "
                    "Disaggregation requires mid-year population age structure (Phase 2)."
                ),
            )
            return out_path
        except Exception as exc:
            error_path = out_dir / f"rm032_{area_code}_error.txt"
            error_path.write_text(str(exc), encoding="utf-8")
            raise

    def parse_rm032_to_dataframe(self, json_path: Path) -> "pd.DataFrame":
        """Parse ONS RM032 JSON into a tidy DataFrame."""
        import itertools

        import pandas as pd

        payload = __import__("json").loads(json_path.read_text(encoding="utf-8"))
        dimensions = payload.get("dimensions", [])
        observations = payload.get("observations", [])

        dim_options: list[list[dict[str, str]]] = []
        dim_names: list[str] = []
        for dim in dimensions:
            dim_names.append(dim["dimension_name"])
            dim_options.append(dim["options"])

        records: list[dict[str, object]] = []
        for combo, value in zip(itertools.product(*dim_options), observations):
            if value is None:
                continue
            record: dict[str, object] = {"count": value}
            for name, opt in zip(dim_names, combo):
                record[f"{name}_id"] = opt["id"]
                record[f"{name}_label"] = opt["label"]
            records.append(record)

        return pd.DataFrame(records)

    def discover_census_datasets(self) -> list[dict[str, str]]:
        """List Census-related datasets available via ONS API."""
        result = self.list_datasets(limit=200)
        items = result.get("items", [])
        census_items: list[dict[str, str]] = []
        for item in items:
            title = item.get("title", "")
            dataset_id = item.get("id", "")
            if "census" in title.lower() or dataset_id.startswith(("TS", "RM")):
                census_items.append({"id": dataset_id, "title": title})
        return census_items

    def close(self) -> None:
        self.http.close()

    def __enter__(self) -> ONSClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
