"""Fetch official PL terrain WCS GeoTIFF only after validating coverage metadata.

A coverage's name is NOT sufficient to establish a legal or vertical transformation.
This uses PL-KRON86-NH and cannot be merged with CZ-BPV without verified
vertical-datum conversion. Never upload the raw or derivative terrain automatically.
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
from defusedxml import ElementTree as SafeET

from geodata.gugik_wcs_probe import BASE, GUGiKWCSProbeError, parse_capabilities

COVERAGE_ID = "DTM_PL-KRON86-NH_TIFF"
CENTRE_EPSG2180 = (473584.1781628306, 209041.2727031326)
# Small extraction around Cieszyn Rynek; ~512 m x 512 m in PL-1992.
BBOX = (473328, 208784, 473840, 209296)
MAX_RASTER_BYTES = 15 * 1024 * 1024
MAX_XML_BYTES = 3 * 1024 * 1024
USER_AGENT = "ManOfTheYear-WORLD-QA/0.1 (https://github.com/mojealterego/Cz-owiek-Roku)"


class PolishNMTError(ValueError):
    pass


def _request(url: str, byte_limit: int) -> bytes:
    if not url.startswith(BASE + "?") or "@" in url or "\n" in url or "\r" in url:
        raise PolishNMTError("Noncanonical WCS endpoint")
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=70) as result:
        raw = result.read(byte_limit + 1)
    if not raw or len(raw) > byte_limit:
        raise PolishNMTError("Empty or oversized WCS response")
    return raw


def query(operation: str, extra: dict | None = None) -> str:
    if operation not in ("GetCapabilities", "DescribeCoverage", "GetCoverage"):
        raise PolishNMTError("Forbidden WCS operation")
    params = {"SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": operation}
    if extra:
        params.update(extra)
    return BASE + "?" + urlencode(params, doseq=True)


def parse_description(raw: bytes) -> dict:
    if len(raw) > MAX_XML_BYTES:
        raise PolishNMTError("Excessive XML description")
    try:
        root = SafeET.fromstring(raw)
    except Exception as exc:
        raise PolishNMTError("Unsafe XML response") from exc
    local_root = root.tag.rsplit("}", 1)[-1]
    if local_root not in ("CoverageDescriptions", "CoverageDescription"):
        raise PolishNMTError("WCS coverage description expected, got " + local_root)
    ids = [el.text.strip() for el in root.iter()
           if el.tag.rsplit("}", 1)[-1] in ("CoverageId", "CoverageID")
           and el.text and el.text.strip()]
    if COVERAGE_ID not in ids:
        raise PolishNMTError("Advertised Polish NMT coverage absent in description")
    envelopes = []
    for el in root.iter():
        if el.tag.rsplit("}", 1)[-1] == "Envelope":
            crs = el.get("srsName", "")
            labels = el.get("axisLabels", "").split()
            envelopes.append({"crs": crs, "axis_labels": labels,
                              "srs_dimension": el.get("srsDimension")})
    if not envelopes:
        raise PolishNMTError("No explicit geographic envelope in WCS description")
    matches = [v for v in envelopes if ("2180" in v["crs"]
               and len(v["axis_labels"]) == 2)]
    if not matches:
        raise PolishNMTError(
            "No explicit EPSG:2180 coverage envelope with two axes. Advertised: "
            + json.dumps(envelopes[:8], ensure_ascii=False))
    selected = matches[0]
    if not all(s and s.replace("_", "").isalnum() for s in selected["axis_labels"]):
        raise PolishNMTError("Invalid axis label")
    return {"coverage_id": COVERAGE_ID, "wcs_version": "2.0.1",
            "horizontal_crs": "EPSG:2180",
            "axis_labels": selected["axis_labels"],
            "vertical_datum_from_id": "PL-KRON86-NH",
            "vertical_datum_independently_verified": False,
            "envelopes": envelopes[:10]}


def coverage_url(axis_labels: list[str]) -> str:
    if len(axis_labels) != 2:
        raise PolishNMTError("Two WCS axis labels required")
    if len(set(axis_labels)) != 2:
        raise PolishNMTError("Duplicated axes")
    west, south, east, north = BBOX
    def axis_range(label: str) -> str:
        if label in ("x", "X", "E", "e", "Easting", "easting"):
            return f"{label}({west},{east})"
        if label in ("y", "Y", "N", "n", "Northing", "northing"):
            return f"{label}({south},{north})"
        raise PolishNMTError("Unrecognized coverage axis: " + label)
    subsets = [axis_range(label) for label in axis_labels]
    if not any(s.startswith(("x(", "X(", "E(", "e(", "Easting(", "easting("))
               for s in subsets):
        raise PolishNMTError("Missing easting axis")
    if not any(s.startswith(("y(", "Y(", "N(", "n(", "Northing(", "northing("))
               for s in subsets):
        raise PolishNMTError("Missing northing axis")
    return query("GetCoverage", {
        "COVERAGEID": COVERAGE_ID,
        "FORMAT": "image/tiff",
        "SUBSET": subsets,
    })


def obtain(output: Path) -> dict:
    if output.exists():
        raise PolishNMTError("Refusing to replace Polish DEM")
    capabilities = parse_capabilities(_request(query("GetCapabilities"), MAX_XML_BYTES))
    if COVERAGE_ID not in capabilities["coverage_ids"]:
        raise PolishNMTError("Official WCS no longer advertises requested coverage")
    described_raw = _request(
        query("DescribeCoverage", {"COVERAGEID": COVERAGE_ID}), MAX_XML_BYTES)
    description = parse_description(described_raw)
    url = coverage_url(description["axis_labels"])
    raw = _request(url, MAX_RASTER_BYTES)
    if raw[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
        raise PolishNMTError("WCS GetCoverage did not return raw TIFF")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    try:
        with rasterio.open(output) as ds:
            if ds.driver != "GTiff" or ds.count != 1 or ds.crs is None:
                raise PolishNMTError("GeoTIFF is not a single georeferenced height band")
            if ds.crs.to_epsg() != 2180:
                raise PolishNMTError("GeoTIFF CRS not verified EPSG:2180: "
                                     + ds.crs.to_string()[:200])
            if ds.width > 4096 or ds.height > 4096:
                raise PolishNMTError("GeoTIFF too large for bounded QA")
            west, south, east, north = BBOX
            if not (abs(ds.bounds.left-west)<3 and abs(ds.bounds.right-east)<3
                    and abs(ds.bounds.top-north)<3 and abs(ds.bounds.bottom-south)<3):
                raise PolishNMTError("GeoTIFF extent differs from Cieszyn request")
            raster = ds.read(1, masked=True)
            nvalid = int(raster.count())
            if nvalid < 100:
                raise PolishNMTError("Not enough terrain pixels")
            min_h, max_h = float(raster.min()), float(raster.max())
            if not (math.isfinite(min_h) and math.isfinite(max_h)
                    and 100 < min_h <= max_h < 1500):
                raise PolishNMTError("Implausible heights in Cieszyn")
            summary = {
                "official_source": BASE,
                "coverage_id": COVERAGE_ID,
                "source_vertical_datum_label": "PL-KRON86-NH",
                "vertical_datum_independently_verified": False,
                "source_epoch": "UNKNOWN",
                "source_crs": "EPSG:2180",
                "source_sha256": hashlib.sha256(raw).hexdigest(),
                "height_range_m": [round(min_h, 3), round(max_h, 3)],
                "valid_pixels": nvalid,
                "dimensions": [ds.width, ds.height],
                "source_nodata": ds.nodata,
                "output_status": "INTERNAL_QA_NOT_PUBLIC_WORLD",
            }
    except Exception:
        output.unlink(missing_ok=True)
        raise
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("describe", "download"),
                        default="describe")
    parser.add_argument("--out", type=Path)
    options = parser.parse_args()
    if options.mode == "describe":
        description = parse_description(_request(
            query("DescribeCoverage", {"COVERAGEID": COVERAGE_ID}), MAX_XML_BYTES))
        print(json.dumps(description, ensure_ascii=False, sort_keys=True))
        return
    if options.out is None:
        parser.error("--out required for download")
    print(json.dumps(obtain(options.out), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
