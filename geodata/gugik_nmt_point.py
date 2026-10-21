"""Three restrained real NMT point queries to validate Polish Cieszyn heights.

Official historical docs state PUWG92 / EPSG:2180 XY coordinates and
PL-KRON86-NH heights; the acquisition epoch remains unknown. Values are
independent spot checks, NOT a city-wide grid or a vertical transformation.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE = "https://services.gugik.gov.pl/nmt/"
USER_AGENT = "ManOfTheYear-WORLD-QA/0.1 (https://github.com/mojealterego/Cz-owiek-Roku)"
# Point at Cieszyn town hall and two nearby offsets in national metre CRS.
SAMPLES = [
    ("CIESZYN_RYNEK", 473584.178, 209041.273),
    ("CIESZYN_NORTH", 473584.178, 209081.273),
    ("CIESZYN_WEST", 473544.178, 209041.273),
]
NUMBER = re.compile(r"^[+-]?[0-9]{1,4}(?:[.,][0-9]{1,4})?$")


class PolishPointError(ValueError):
    pass


def parse_height(data: bytes) -> float:
    if len(data) > 200:
        raise PolishPointError("Unexpected service response length")
    try:
        text = data.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise PolishPointError("Non-UTF8 response") from exc
    if not NUMBER.fullmatch(text):
        raise PolishPointError("Not a plain numeric terrain-height response: " + repr(text[:60]))
    v = float(text.replace(",", "."))
    if not math.isfinite(v) or not (100.0 < v < 1000.0):
        raise PolishPointError("Implausible or missing Cieszyn height: " + str(v))
    return v


def sample_one(x: float, y: float) -> float:
    if not (470000 < x < 478000 and 206000 < y < 212000):
        raise PolishPointError("Outside strictly bounded Cieszyn testing radius")
    url = BASE + "?" + urlencode({
        "request": "GetHByXY", "x": f"{x:.3f}", "y": f"{y:.3f}"
    })
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*"})
    with urlopen(request, timeout=20) as response:
        body = response.read(201)
    return parse_height(body)


def run() -> dict:
    elevations = []
    for idx, (name, x, y) in enumerate(SAMPLES):
        if idx:
            time.sleep(0.4)  # courtesy delay, only 3 points, no service scraping
        h = sample_one(x, y)
        elevations.append({"id": name, "epsg2180_xy": [x, y], "height_m": h})
    return {
        "source": BASE,
        "source_request": "GetHByXY",
        "xy_crs": "EPSG:2180",
        "height_datum_documented": "PL-KRON86-NH",
        "height_datum_site_verified": False,
        "source_acquisition_epoch": "UNKNOWN",
        "samples": elevations,
        "approved_city_terrain": False,
        "compatible_with_czech_bpv": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-three-points", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(run(), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
