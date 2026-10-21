extends Node3D
## Bounded, proximity-based stream of REAL 2026 OSM metric geometry.
## Does not fetch data from network, invent geometry, or claim historical accuracy.
## Keeps legacy full-city loader available for regression tests.

const SIZE_M: int = 256
const MAX_LOADS_PER_FRAME: int = 2
const LEAF_SCENE = preload("res://scripts/osm_preview_layer.gd")

var world_root: String = "res://data/world/cieszyn_rynek_osm_2026"
var expected_city_id: String = "CIESZYN_RYNEK"
var expected_source_id: String = "OPENSTREETMAP_2026_CIESZYN_RYNEK"
var radius_tiles: int = 2
var max_resident_tiles: int = 6

var initialized: bool = false
var source_tile_count: int = 0
var resident: Dictionary = {}           # Vector2i → rendered sector Node3D
var available: Dictionary = {}          # Vector2i → filename (index only)
var wanted: Array[Vector2i] = []
var focus_east_m: float = INF
var focus_north_m: float = INF
var total_loaded_events: int = 0
var total_unloaded_events: int = 0
var invalid_tile_events: int = 0
var processing_budget_max_observed: int = 0
var last_error: String = ""

func _ready() -> void:
    initialized = _index_source()
    if not initialized:
        push_warning("WORLD OSM: no source index; streaming disabled.")
    set_process(initialized)

func _index_source() -> bool:
    if world_root.is_empty() or expected_city_id.is_empty() or expected_source_id.is_empty():
        return _error("City source identity not configured")
    if not world_root.begins_with("res://data/world/"):
        return _error("Refusing nonpublic or external source folders")
    if max_resident_tiles < 1 or max_resident_tiles > 12:
        return _error("Maximum resident tile budget outside mobile guardrail")
    if radius_tiles < 1 or radius_tiles > 4:
        return _error("Invalid tile visibility radius")
    var manifest_path: String = world_root + "/manifest.json"
    if not FileAccess.file_exists(manifest_path):
        return _error("Source manifest absent")
    var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
    if not data is Dictionary:
        return _error("Malformed OSM manifest")
    var m: Dictionary = data
    if m.get("schema_version", 0) != 1 or m.get("city_id", "") != expected_city_id:
        return _error("Unexpected city identity")
    if m.get("tile_size_m", 0) != SIZE_M or m.get("projection", "") != "LOCAL_WGS84_AEQD":
        return _error("World is not on shared metre grid")
    if m.get("build_status", "") != "CURRENT_BASEMAP_NOT_HISTORICALLY_VERIFIED":
        return _error("Incorrect historical-data readiness claim")
    if m.get("historical_year", "") != "2026" or m.get("terrain_status", "") != "MISSING":
        return _error("Source claims verified history or ground heights")
    var source: Variant = m.get("source")
    if not source is Dictionary:
        return _error("Source lineage missing")
    if source.get("id", "") != expected_source_id or source.get("license", "") != "ODbL-1.0":
        return _error("OSM lineage/license mismatch")
    if not m.get("redistribution_allowed", false):
        return _error("Source data rights not approved for this build")
    if str(source.get("sha256", "")).length() != 64:
        return _error("Source digest absent")
    var pattern := RegEx.new()
    if pattern.compile("^E([+-][0-9]{6})_N([+-][0-9]{6})[.]json$") != OK:
        return _error("Cannot compile tile ID parser")
    var found: PackedStringArray = DirAccess.get_files_at(world_root)
    for filename in found:
        if filename == "manifest.json":
            continue
        if not filename.ends_with(".json"):
            continue
        var match_result: RegExMatch = pattern.search(filename)
        if match_result == null:
            return _error("Malformed tile filename: " + filename)
        var key := Vector2i(int(match_result.get_string(1)), int(match_result.get_string(2)))
        if available.has(key):
            return _error("Duplicate indexed sector")
        available[key] = filename
    if available.is_empty() or available.size() != int(m.get("tile_count", -1)):
        return _error("Indexed sector count not consistent with manifest")
    source_tile_count = available.size()
    return true

func _error(message: String) -> bool:
    last_error = message
    return false

func set_focus(world_position: Vector3) -> void:
    # Coordinates follow the one fixed AEQD frame: X=east, -Z=north.
    if not initialized or not is_finite(world_position.x) or not is_finite(world_position.z):
        return
    var next_east: float = world_position.x
    var next_north: float = -world_position.z
    if next_east == focus_east_m and next_north == focus_north_m:
        return
    focus_east_m = next_east
    focus_north_m = next_north
    _compute_nearest()
    _evict_outside_target()

func _compute_nearest() -> void:
    var focus_col: int = floori(focus_east_m / SIZE_M)
    var focus_row: int = floori(focus_north_m / SIZE_M)
    var order: Array[Dictionary] = []
    for key in available.keys():
        if absi(key.x - focus_col) > radius_tiles or absi(key.y - focus_row) > radius_tiles:
            continue
        var east_center: float = float(key.x * SIZE_M) + SIZE_M * 0.5
        var north_center: float = float(key.y * SIZE_M) + SIZE_M * 0.5
        var distance_squared: float = pow(east_center - focus_east_m, 2.0) + pow(north_center - focus_north_m, 2.0)
        order.append({"key": key, "distance_squared": distance_squared})
    order.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
        return a["distance_squared"] < b["distance_squared"])
    wanted.clear()
    var count: int = mini(max_resident_tiles, order.size())
    for index in range(count):
        wanted.append(order[index]["key"])

func _evict_outside_target() -> void:
    for key in resident.keys():
        if key not in wanted:
            var sector: Node3D = resident[key]
            resident.erase(key)
            remove_child(sector)
            sector.queue_free()
            total_unloaded_events += 1

func _process(_delta: float) -> void:
    if not initialized or wanted.is_empty():
        return
    var calls: int = 0
    for key in wanted:
        if resident.has(key):
            continue
        if calls >= MAX_LOADS_PER_FRAME:
            break
        if resident.size() >= max_resident_tiles:
            break
        # At most 2 sector JSON reads + geometry meshes per rendered frame.
        calls += 1
        _load_sector(key)
    processing_budget_max_observed = maxi(processing_budget_max_observed, calls)

func _load_sector(key: Vector2i) -> void:
    if not available.has(key) or resident.has(key):
        return
    var path: String = world_root + "/" + str(available[key])
    var decoded: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
    if not decoded is Dictionary:
        invalid_tile_events += 1
        _error("Tile JSON invalid: " + path)
        return
    var tile: Dictionary = decoded
    if tile.get("id", "") != str(available[key]).trim_suffix(".json"):
        invalid_tile_events += 1
        _error("Sector ID not consistent with file name")
        return
    if tile.get("origin_east_m", NAN) != key.x * SIZE_M or tile.get("origin_north_m", NAN) != key.y * SIZE_M:
        invalid_tile_events += 1
        _error("Tile origin not matching indexed location")
        return
    var sector = LEAF_SCENE.new()
    sector.auto_load = false
    sector.world_root = world_root
    sector.expected_city_id = expected_city_id
    sector.expected_source_id = expected_source_id
    sector.name = "OSM_%s_%s" % [expected_city_id, str(tile["id"])]
    add_child(sector)
    if not sector._import_tile(tile):
        remove_child(sector)
        sector.queue_free()
        invalid_tile_events += 1
        _error("Source geometry validation failure: " + str(tile["id"]))
        return
    sector.tile_count = 1
    sector.loaded = true
    resident[key] = sector
    total_loaded_events += 1

func active_sector_count() -> int:
    return resident.size()

func active_mesh_count() -> int:
    var n: int = 0
    for sector in resident.values():
        n += sector.world_meshes.size()
    return n

func unload_all() -> void:
    wanted.clear()
    _evict_outside_target()
