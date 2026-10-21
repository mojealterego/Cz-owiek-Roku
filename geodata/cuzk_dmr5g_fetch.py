"""Fetch a bounded, official ČÚZK DMR5G height raster for internal technical QA.

No license grant is inferred from public access. Neither raster nor output
terrain geometry is automatically committed or uploaded to public artifacts.
The requested raster is raw Float32, not a rendered hillshade or basemap image.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import rasterio

BASE = "https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer"
BBOX = (-447250.0, -1114000.0, -446350.0, -1113100.0)
WIDTH = HEIGHT = 450
MAX_BYTES = 12 * 1024 * 1024
AGENT = "ManOfTheYear-WorldQA/0.1 (https://github.com/mojealterego/Cz-owiek-Roku)"


class DMRFetchError(ValueError):
    pass


def validate_service(metadata: dict) -> None:
    if not isinstance(metadata, dict) or "error" in metadata:
        raise DMRFetchError("DMR image service returned an error")
    ref = metadata.get("spatialReference", {})
    if ref.get("latestWkid") != 5514 or ref.get("latestVcsWkid") != 8357:
        raise DMRFetchError("Unexpected horizontal or vertical CRS")
    info = metadata.get("heightModelInfo", {})
    if (info.get("vertCRS") != "Baltic_1957_height"
            or info.get("heightUnit") != "meter"):
        raise DMRFetchError("Unknown vertical height reference")
    if metadata.get("bandCount") != 1 or metadata.get("pixelType") != "F32":
        raise DMRFetchError("Elevation source is not a float height raster")


def export_image_url() -> str:
    west, south, east, north = BBOX
    if not (east > west and north > south and max(east-west, north-south) <= 1000):
        raise DMRFetchError("Export window exceeds allowable QA area")
    args = {
        "bbox": ",".join(str(int(v)) for v in BBOX), "bboxSR": "5514",
        "imageSR": "5514", "size": f"{WIDTH},{HEIGHT}",
        "format": "tiff", "pixelType": "F32",
        "interpolation": "RSP_NearestNeighbor", "f": "image",
    }
    return BASE + "/exportImage?" + urlencode(args)


def _fetch(url: str, maximum: int = MAX_BYTES) -> bytes:
    if not url.startswith(BASE) or "@" in url or "\r" in url or "\n" in url:
        raise DMRFetchError("Untrusted source URL")
    request = Request(url, headers={"User-Agent": AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=65) as result:
        data = result.read(maximum + 1)
    if not data or len(data) > maximum:
        raise DMRFetchError("Empty or oversized source response")
    return data


def fetch(destination: Path) -> dict:
    if destination.exists():
        raise DMRFetchError("Refusing to overwrite a raster")
    metadata = json.loads(_fetch(BASE + "?f=pjson", 2_000_000))
    validate_service(metadata)
    raw = _fetch(export_image_url())
    if raw[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        raise DMRFetchError("Expected unrendered GeoTIFF, not a picture or JSON error")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    crs_repaired = False
    try:
        with rasterio.open(destination) as source:
            if source.driver != "GTiff" or source.count != 1 or source.crs is None:
                raise DMRFetchError("Downloaded height raster lacks georeferencing")
            if source.width != WIDTH or source.height != HEIGHT:
                raise DMRFetchError("Downloaded raster grid has unexpected dimensions")
            if not (abs(source.res[0] - 2.0) < 0.1
                    and abs(source.res[1] - 2.0) < 0.1):
                raise DMRFetchError("Unexpected elevation raster spatial resolution")
            west, south, east, north = BBOX
            if not (abs(source.bounds.left - west) < 4
                    and abs(source.bounds.right - east) < 4
                    and abs(source.bounds.bottom - south) < 4
                    and abs(source.bounds.top - north) < 4):
                raise DMRFetchError("Downloaded raster location does not match requested bbox")
            code = source.crs.to_epsg()
            raw_wkt = source.crs.to_wkt()
            if code != 5514:
                expected_local = (
                    raw_wkt.startswith('LOCAL_CS["S-JTSK / Krovak East North"')
                    and 'AUTHORITY["EPSG","5514"]' in raw_wkt
                )
                if not expected_local:
                    raise DMRFetchError("Unexpected downloaded CRS: " + raw_wkt[:350])
                crs_repaired = True
            samples = source.read(1, masked=True)
            valid_count = int(samples.count())
            if valid_count < 50:
                raise DMRFetchError("Insufficient source elevation pixels")
            min_h = float(samples.min())
            max_h = float(samples.max())
            zero_pixels = int((samples == 0.0).sum())
            positive = samples[(samples > 100.0) & (samples < 1000.0)]
            if positive.count() < 50:
                raise DMRFetchError("Not enough plausible non-zero Cieszyn terrain values")
            if not (math.isfinite(min_h) and math.isfinite(max_h)
                    and -1000.0 < min_h <= max_h < 4000.0):
                raise DMRFetchError("Implausible terrain pixel range")
        if crs_repaired:
            # Official ArcGIS GeoTIFF writes a LOCAL_CS with the correct EPSG
            # authority but incomplete PROJ definition. It has already passed
            # service CRS, bounds, pixel size and raw WKT checks above.
            # Re-tag the horizontal CRS only: NO coordinate/elevation edits.
            with rasterio.open(destination, "r+") as editable:
                editable.crs = rasterio.crs.CRS.from_epsg(5514)
            with rasterio.open(destination) as verified:
                if verified.crs.to_epsg() != 5514:
                    raise DMRFetchError("Failed to normalize horizontal CRS")
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return {
        "source": BASE, "source_metadata_validated": True,
        "source_vertical_system": "CZ-BPV", "horizontal_crs": "EPSG:5514",
        "official_metadata_vertical_wkid": 8357,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "horizontal_crs_retagged_after_validation": crs_repaired,
        "width": WIDTH, "height": HEIGHT,
        "valid_pixels": valid_count, "suspect_zero_pixels": zero_pixels,
        "min_sample_m": round(min_h, 3),
        "max_sample_m": round(max_h, 3),
        "not_verified_for_game_release": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(fetch(args.output), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
