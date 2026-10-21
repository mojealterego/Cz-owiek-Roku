extends SceneTree
## Actual, attributed OSM tiles are read from the project resources.
## Test residency limits, camera migration, eviction, and source identity.
var failures: int = 0

func _initialize() -> void:
    call_deferred("_run")

func _check(ok: bool, description: String) -> void:
    if ok:
        print("PASS: " + description)
    else:
        failures += 1
        push_error("FAIL: " + description)

func _make_streamer(czech: bool):
    var streamer = load("res://scripts/osm_tile_streamer.gd").new()
    streamer.max_resident_tiles = 3
    streamer.radius_tiles = 2
    if czech:
        streamer.world_root = "res://data/world/cesky_tesin_center_osm_2026"
        streamer.expected_city_id = "CESKY_TESIN_CENTER"
        streamer.expected_source_id = "OPENSTREETMAP_2026_CESKY_TESIN_CENTER"
    root.add_child(streamer)
    return streamer

func _advance_frames(n: int) -> void:
    for i in range(n):
        await process_frame

func _run() -> void:
    var pl = _make_streamer(false)
    var cz = _make_streamer(true)
    _check(pl.initialized and cz.initialized, "Both real OSM sources indexed")
    _check(pl.source_tile_count == 4 and cz.source_tile_count == 9,
        "All 13 sector files indexed without loading their meshes")
    _check(pl.active_sector_count() == 0 and cz.active_sector_count() == 0,
        "No sector prefetched before a focus position exists")
    pl.set_focus(Vector3(0, 0, 0))
    cz.set_focus(Vector3(0, 0, 0))
    await _advance_frames(3)
    _check(pl.active_sector_count() <= 3 and cz.active_sector_count() <= 3,
        "Configured RAM cap applies independently per city")
    _check(pl.total_loaded_events > 0, "Real Cieszyn geometry streamed from file")
    _check(pl.active_mesh_count() > 0, "Streamed tile contains renderable road/building meshes")
    _check(pl.invalid_tile_events == 0 and cz.invalid_tile_events == 0,
        "No invalid georeferenced tiles accepted")
    _check(pl.processing_budget_max_observed <= 2 and cz.processing_budget_max_observed <= 2,
        "No more than 2 tile builds in one frame")
    var initial_pl: int = pl.active_sector_count()
    pl.set_focus(Vector3(-550, 0, 210))
    cz.set_focus(Vector3(-550, 0, 210))
    await _advance_frames(3)
    _check(cz.total_loaded_events > 0, "Actual Czech buildings and roads become active")
    _check(cz.active_mesh_count() > 0, "Czech OSM sector is rendered")
    _check(pl.active_sector_count() <= 3 and cz.active_sector_count() <= 3,
        "Residency never exceeds per-layer budget after relocation")
    _check(pl.total_unloaded_events > 0 or initial_pl == 0,
        "Distant Polish sector freed when camera changes bank")
    pl.set_focus(Vector3(100000, 0, -100000))
    cz.set_focus(Vector3(100000, 0, -100000))
    await _advance_frames(2)
    _check(pl.active_sector_count() == 0 and cz.active_sector_count() == 0,
        "All remote sectors unloaded when outside available source coverage")
    _check(pl.total_unloaded_events > 0 and cz.total_unloaded_events > 0,
        "Sector eviction occurred on both sides of Olza")
    _check(pl.last_error.is_empty() and cz.last_error.is_empty(),
        "No silent tile parsing or provenance error")
    var blocked = load("res://scripts/osm_tile_streamer.gd").new()
    blocked.expected_source_id = "UNKNOWN_FAKE_SOURCE"
    root.add_child(blocked)
    _check(not blocked.initialized, "Streaming refuses inconsistent source ID")
    print("OSM STREAMING QA FAILURES: ", failures)
    quit(0 if failures == 0 else 1)
