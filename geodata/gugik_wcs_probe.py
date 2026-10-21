"""Inspect the actual GUGiK Polish NMT WCS capabilities safely and reproducibly.

This is metadata discovery only, not invented Polish terrain geometry. The
GeoTIFF coverage ID and vertical reference MUST come from official metadata.
The probe deliberately does not download or republish raster data.
"""
from __future__ import annotations

import argparse
import json
import re
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from defusedxml import ElementTree as SafeET

BASE = "https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF"
MAX_XML_BYTES = 6 * 1024 * 1024
USER_AGENT = "ManOfTheYear-WORLD-QA/0.1 (https://github.com/mojealterego/Cz-owiek-Roku)"


class GUGiKWCSProbeError(ValueError):
    pass


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_capabilities(data: bytes) -> dict:
    if not data or len(data) > MAX_XML_BYTES:
        raise GUGiKWCSProbeError("Capabilities XML empty or excessive")
    try:
        root = SafeET.fromstring(data)
    except Exception as exc:
        raise GUGiKWCSProbeError("Invalid or unsafe service XML") from exc
    if local_name(root.tag) not in ("Capabilities", "WCS_Capabilities"):
        raise GUGiKWCSProbeError("Not a WCS capabilities document")
    version = root.get("version") or "UNSPECIFIED"
    ids: list[str] = []
    formats: set[str] = set()
    crs: set[str] = set()
    for el in root.iter():
        name = local_name(el.tag)
        value = (el.text or "").strip()
        if name in ("CoverageId", "CoverageID", "CoverageIdentifier", "name", "Name"):
            if value and len(value) <= 200:
                # Include only identifiers under an actual CoverageSummary/
                # CoverageOffering node, avoiding operation names like GetMap.
                parent_names = [local_name(a.tag) for a in root.iter()
                                if el in list(a)]
                if any(p in ("CoverageSummary", "CoverageOffering",
                             "CoverageOfferingBrief") for p in parent_names):
                    ids.append(value)
        if name in ("formatSupported", "FormatSupported", "format", "Format"):
            if value and len(value) <= 150:
                formats.add(value)
        if name in ("supportedCRS", "SupportedCRS", "requestResponseCRSs",
                    "nativeCRSs", "srsName"):
            if value and len(value) <= 150:
                crs.add(value)
    ids = sorted(set(ids))
    if not ids:
        raise GUGiKWCSProbeError("No advertised coverage names, refusing to guess")
    return {
        "source": BASE, "wcs_version": version, "coverage_ids": ids[:40],
        "available_coverage_count": len(ids),
        "advertised_formats": sorted(formats)[:30],
        "advertised_crs": sorted(crs)[:30],
        "vertical_datum_status": "NOT_VERIFIED_FROM_CAPABILITIES",
        "source_geometry_imported": False,
    }


def get_capabilities(version: str) -> bytes:
    if version not in ("2.0.1", "1.0.0"):
        raise GUGiKWCSProbeError("Unexpected WCS version")
    query = urlencode({
        "SERVICE": "WCS", "REQUEST": "GetCapabilities", "VERSION": version,
    })
    request = Request(BASE + "?" + query,
                      headers={"User-Agent": USER_AGENT, "Accept": "application/xml,text/xml,*/*"})
    with urlopen(request, timeout=60) as response:
        b = response.read(MAX_XML_BYTES + 1)
    if len(b) > MAX_XML_BYTES:
        raise GUGiKWCSProbeError("Excessive capabilities response")
    return b


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("2.0.1", "1.0.0"), default="2.0.1")
    args = parser.parse_args()
    doc = get_capabilities(args.version)
    result = parse_capabilities(doc)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
