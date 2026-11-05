"""NASA PMM Publisher catalog client. Returns product metadata/download links.

This is a catalog connector, not yet a raster-to-location extraction pipeline.
"""
from datetime import date, timedelta
import httpx

BASE_URL = "https://pmmpublisher.pps.eosdis.nasa.gov/opensearch"
ALLOWED_PRODUCTS = {
    "precip_30mn", "precip_30mn_3hr", "precip_30mn_1d",
    "precip_1d", "precip_3d", "precip_7d",
    "global_landslide_nowcast", "global_landslide_nowcast_30mn",
}

async def search_catalog(product: str = "global_landslide_nowcast_30mn",
                         start_time: str | None = None,
                         end_time: str | None = None,
                         limit: int = 10) -> dict:
    if product not in ALLOWED_PRODUCTS:
        raise ValueError(f"Unsupported NASA PMM product: {product}")
    today = date.today()
    end_time = end_time or today.isoformat()
    start_time = start_time or (today - timedelta(days=2)).isoformat()
    params = {"q": product, "limit": max(1, min(limit, 100)),
              "startTime": start_time, "endTime": end_time}
    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.get(BASE_URL, params=params,
                                    headers={"Accept": "application/activity+json, application/json"})
        response.raise_for_status()
        payload = response.json()
    items = []
    for item in payload.get("items", []):
        actions = []
        for action in item.get("action", []):
            for resource in action.get("using", []):
                if resource.get("url"):
                    actions.append({"kind": action.get("displayName"),
                                    "media_type": resource.get("mediaType"),
                                    "url": resource["url"]})
        props = item.get("properties", {})
        items.append({"id": item.get("@id"), "title": item.get("displayName"),
                      "geometry": item.get("geometry"), "actions": actions,
                      "properties": props})
    return {"product": product, "total_items": payload.get("totalItems", len(items)),
            "items": items, "source": "NASA_GPM_PMM_PUBLISHER",
            "catalog_url": str(response.url)}
