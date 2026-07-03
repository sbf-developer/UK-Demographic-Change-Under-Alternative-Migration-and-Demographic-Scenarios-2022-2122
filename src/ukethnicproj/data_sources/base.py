"""Base HTTP client with caching for official data APIs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import httpx


class CachedHTTPClient:
    """HTTP client that caches responses for reproducible offline reruns."""

    def __init__(
        self,
        base_url: str,
        cache_dir: Path,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers={"User-Agent": "ukethnicproj/0.1.0 (research; Scott Brodie Forsyth)"},
            follow_redirects=True,
        )

    def _cache_key(self, path: str, params: dict[str, Any] | None) -> str:
        payload = json.dumps({"path": path, "params": params or {}}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def _cache_path(self, key: str, suffix: str = ".json") -> Path:
        return self.cache_dir / f"{key}{suffix}"

    def get(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
        accept: str = "application/json",
    ) -> httpx.Response:
        key = self._cache_key(path, params)
        cache_file = self._cache_path(key, suffix=".body")

        if use_cache and cache_file.exists():
            content = cache_file.read_bytes()
            meta = json.loads(self._cache_path(key, suffix=".meta").read_text(encoding="utf-8"))
            # Strip content-encoding headers; cached body is already decompressed
            headers = {k: v for k, v in meta.get("headers", {}).items()
                       if k.lower() not in ("content-encoding", "transfer-encoding")}
            response = httpx.Response(
                status_code=meta["status_code"],
                headers=headers,
                content=content,
                request=httpx.Request("GET", self.base_url + path),
            )
            return response

        headers = {"Accept": accept}
        response = self.client.get(path, params=params, headers=headers)
        response.raise_for_status()

        if use_cache:
            cache_file.write_bytes(response.content)
            meta = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "url": str(response.url),
            }
            self._cache_path(key, suffix=".meta").write_text(
                json.dumps(meta, indent=2), encoding="utf-8"
            )

        return response

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Any:
        response = self.get(path, params=params, use_cache=use_cache)
        return response.json()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> CachedHTTPClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
