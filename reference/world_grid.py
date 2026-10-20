"""Deterministic metric tile indexing for future city world streaming.

Coordinates are already projected local East/North offsets in metres,
NEVER raw latitude/longitude degrees. No CRS reprojection is performed here.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

TILE_SIZE_M = 256.0


class GeoGridError(ValueError):
    """Invalid projected coordinates or tile identifier."""


@dataclass(frozen=True)
class Tile:
    east_index: int
    north_index: int

    @property
    def origin_east_m(self) -> float:
        return self.east_index * TILE_SIZE_M

    @property
    def origin_north_m(self) -> float:
        return self.north_index * TILE_SIZE_M

    @property
    def identifier(self) -> str:
        return f"E{self.east_index:+07d}_N{self.north_index:+07d}"


def tile_for(east_m: float, north_m: float) -> Tile:
    """Return 256 m square tile with half-open boundaries [origin, origin+256)."""
    for value in (east_m, north_m):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise GeoGridError("Coordinates must be real numeric metre offsets")
        if not math.isfinite(value):
            raise GeoGridError("Non-finite projected coordinate")
    return Tile(math.floor(east_m / TILE_SIZE_M), math.floor(north_m / TILE_SIZE_M))


def local_offsets_m(east_m: float, north_m: float) -> tuple[Tile, float, float]:
    tile = tile_for(east_m, north_m)
    local_east = float(east_m - tile.origin_east_m)
    local_north = float(north_m - tile.origin_north_m)
    if not (0.0 <= local_east < TILE_SIZE_M and 0.0 <= local_north < TILE_SIZE_M):
        raise GeoGridError("Tile origin precision failure")
    return tile, local_east, local_north
