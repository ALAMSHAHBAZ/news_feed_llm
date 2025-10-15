# app/services/geo_service.py

import os
from functools import lru_cache
import httpx
from typing import Optional, Tuple

class GeoService:
    """
    Convert location name strings to lat/long using an external geocoding API (e.g. OpenCage).
    Use LRU cache to avoid repeated calls.
    """

    def __init__(self, api_key: Optional[str] = None):
        # Read from env or pass in
        self.api_key = api_key or os.getenv("OPENCAGE_API_KEY")
        if not self.api_key:
            raise RuntimeError("GeoService requires OPENCAGE_API_KEY environment variable")

        self.endpoint = "https://api.opencagedata.com/geocode/v1/json"

    @lru_cache(maxsize=256)
    def geocode(self, place: str) -> Optional[Tuple[float, float]]:
        """
        Return (latitude, longitude) for the given place name, or None if failed.
        """

        params = {
            "q": place,
            "key": self.api_key,
            "limit": 1,
            "no_annotations": 1
        }
        try:
            resp = httpx.get(self.endpoint, params=params, timeout=5.0)
            resp.raise_for_status()
        except Exception as e:
            # Could log error
            return None

        data = resp.json()
        results = data.get("results")
        if not results:
            return None

        first = results[0]
        geom = first.get("geometry")
        if not geom or "lat" not in geom or "lng" not in geom:
            return None

        return (geom["lat"], geom["lng"])
