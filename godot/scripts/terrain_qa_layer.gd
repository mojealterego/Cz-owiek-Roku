extends Node3D
## WORLD 1:1 experimental 3D heightfield mesh.
## STRICTLY INTERNAL QA. Refuses datasets with unknown source lineage/datum.
## Real-world heights are absolute source-datum values. This must NOT be
## composited with unregistered OSM 2D or the cross-border game world.

const TILE_SIZE_M := 256.0
const ALLOWED_SPACING := [8, 16, 32, 64]
const QA_MANIFEST := "WORLD_SOURCE_TERRAIN_QA"

var qa_folder: String = ""
var expected_city_id: String = ""
var expected_vertical_datum: String = ""
var expected_source_id: String = ""
var qa_mode_enabled: bool = false
var loaded: bool = false
var tile_count: int = 0
var triangle_count: int = 0
var rejected_void_quads: int = 0
var valid_sample_count: int = 0
var meshes: Array[MeshInstance3D] = []
var errors: Array[String] = []


func _ready() -> void:
    loaded = load_heightfield()
    if not loaded:
        push_warning("WORLD 1:1: no QA terrain loaded; no guessed heights generated.")


func _reject(message: String) -> bool:
    errors.append(message)
    return false


func load_heightfield() -> bool:
    if not qa_mode_enabled:
        return _reject("Terrain is available only inside explicit QA mode")
    if qa_folder.is_empty() or expected_city_id.is_empty() or expected_vertical_datum.is_empty():
        return _reject("Explicit folder, city ID and vertical datum required")
    if expected_source_id.is_empty():
        return _reject("Source ID required")
    if not (qa_folder.begins_with("user://") or qa_folder.begins_with("res://")):
        return _reject("Source directory must belong to Godot sandbox")
    if not FileAccess.file_exists(qa_folder + "/manifest.json"):
        return _reject("Terrain manifest missing")
    var manifest_value: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(qa_folder + "/manifest.json"))
    if not manifest_value is Dictionary:
        return _reject("Invalid terrain JSON manifest")
    var manifest: Dictionary = manifest_value
    if manifest.get("schema_version", -1) != 1 or manifest.get("type", "") != QA_MANIFEST:
        return _reject("Unsupported terrain manifest")
    if manifest.get("city_id", "") != expected_city_id:
        return _reject("Mismatched source city")
    if manifest.get("vertical_datum", "") != expected_vertical_datum:
        return _reject("Incompatible vertical datum; cross-border mixing refused")
    if manifest.get("source_id", "") != expected_source_id:
        return _reject("Unverified source ID")
    if manifest.get("tile_size_m", 0) != TILE_SIZE_M:
        return _reject("Nonmetric terrain tile size")
    if manifest.get("status", "") != "GEOTIFF_IMPORTED_NOT_HISTORICALLY_VALIDATED":
        return _reject("Unsupported terrain readiness state")
    if manifest.get("vertical_registration_to_game", "") != "NOT_VERIFIED":
        return _reject("Unexpected claimed vertical registration")
    if manifest.get("rights_review_status", "") != "REVIEW_PENDING_INTERNAL_ONLY":
        return _reject("Wrong QA distribution policy")
    if manifest.get("source_sha256", "").length() != 64:
        return _reject("Source hash absent")
    if manifest.get("terrain_source_coverage_complete", true):
        return _reject("Invalid unverified full-city terrain claim")
    var spacing: int = int(manifest.get("spacing_m", 0))
    if spacing not in ALLOWED_SPACING:
        return _reject("Unsupported metric terrain sample spacing")
    var tile_paths: PackedStringArray = DirAccess.get_files_at(qa_folder)
    var tiles: Dictionary = {}
    for name in tile_paths:
        if not name.ends_with(".json") or name == "manifest.json":
            continue
        var raw: Variant = JSON.parse_string(
            FileAccess.get_file_as_string(qa_folder + "/" + name))
        if not raw is Dictionary:
            return _reject("Invalid tile JSON")
        var tile: Dictionary = raw
        if tile.get("type", "") != "GEOREFERENCED_TERRAIN_QA_TILE":
            return _reject("Unexpected tile payload type")
        if tile.get("schema_version", -1) != 1 or tile.get("city_id", "") != expected_city_id:
            return _reject("Wrong tile metadata")
        if tile.get("vertical_datum", "") != expected_vertical_datum:
            return _reject("Different tile vertical datum")
        if tile.get("terrain_alignment", "") != "UNREGISTERED_TO_BUILDINGS":
            return _reject("Unexpected building alignment claim")
        if tile.get("tile_size_m", 0) != TILE_SIZE_M or int(tile.get("spacing_m", 0)) != spacing:
            return _reject("Misaligned spacing")
        var east: float = float(tile.get("origin_east_m", NAN))
        var north: float = float(tile.get("origin_north_m", NAN))
        if not is_finite(east) or not is_finite(north):
            return _reject("Invalid tile origin")
        if fposmod(east, TILE_SIZE_M) != 0.0 or fposmod(north, TILE_SIZE_M) != 0.0:
            return _reject("Tile origin not on metric grid")
        var key: Vector2i = Vector2i(int(roundf(east / TILE_SIZE_M)),
                                    int(roundf(north / TILE_SIZE_M)))
        if tiles.has(key):
            return _reject("Duplicate grid sector")
        var width: int = TILE_SIZE_M / spacing + 1
        if int(tile.get("grid_width", 0)) != width or int(tile.get("grid_height", 0)) != width:
            return _reject("Grid vertex dimensions do not match spacing")
        var heights: Variant = tile.get("heights_m", null)
        if not heights is Array or heights.size() != width * width:
            return _reject("Wrong number of source height samples")
        for value in heights:
            if value == null:
                continue
            if not (value is int or value is float) or not is_finite(float(value)):
                return _reject("Invalid numeric terrain data")
            if abs(float(value)) > 12000:
                return _reject("Implausible source height")
        tiles[key] = tile
    if tiles.size() != int(manifest.get("tile_count", -1)) or tiles.is_empty():
        return _reject("Tile count mismatch")
    if not _validate_seams(tiles):
        return false
    for key in tiles.keys():
        if not _build_tile(tiles[key]):
            return false
    tile_count = tiles.size()
    return triangle_count > 0


func _validate_seams(tiles: Dictionary) -> bool:
    for key in tiles.keys():
        var tile: Dictionary = tiles[key]
        var n: int = int(tile["grid_width"])
        var heights: Array = tile["heights_m"]
        for delta in [Vector2i(1, 0), Vector2i(0, 1)]:
            if not tiles.has(key + delta):
                continue
            var adjacent: Dictionary = tiles[key + delta]
            var other: Array = adjacent["heights_m"]
            for t in range(n):
                var a: Variant
                var b: Variant
                if delta.x != 0:
                    a = heights[t * n + n - 1]
                    b = other[t * n]
                else:
                    a = heights[(n - 1) * n + t]
                    b = other[t]
                if a == null or b == null:
                    if a != null or b != null:
                        return _reject("NoData mismatch at source tile seam")
                elif abs(float(a) - float(b)) > 0.001:
                    return _reject("Vertical discontinuity at metric tile seam")
    return true


func _vertex(origin_e: float, origin_n: float,
        x: int, z: int, spacing: int, height_m: float) -> Vector3:
    # Godot X = east, Z = south. Y is the source's absolute vertical datum.
    return Vector3(origin_e + x * spacing, height_m,
                   -(origin_n + z * spacing))


func _build_tile(tile: Dictionary) -> bool:
    var n: int = int(tile["grid_width"])
    var spacing: int = int(tile["spacing_m"])
    var origin_e: float = float(tile["origin_east_m"])
    var origin_n: float = float(tile["origin_north_m"])
    var values: Array = tile["heights_m"]
    var vertices: PackedVector3Array = PackedVector3Array()
    for y in range(n - 1):
        for x in range(n - 1):
            var a: Variant = values[y * n + x]
            var b: Variant = values[y * n + x + 1]
            var c: Variant = values[(y + 1) * n + x]
            var d: Variant = values[(y + 1) * n + x + 1]
            if a == null or b == null or c == null or d == null:
                rejected_void_quads += 1
                continue
            var p0: Vector3 = _vertex(origin_e, origin_n, x, y, spacing, float(a))
            var p1: Vector3 = _vertex(origin_e, origin_n, x + 1, y, spacing, float(b))
            var p2: Vector3 = _vertex(origin_e, origin_n, x, y + 1, spacing, float(c))
            var p3: Vector3 = _vertex(origin_e, origin_n, x + 1, y + 1, spacing, float(d))
            vertices.append_array(PackedVector3Array([p0, p1, p2, p1, p3, p2]))
            triangle_count += 2
    for h in values:
        if h != null:
            valid_sample_count += 1
    if vertices.is_empty():
        return true
    var arrays: Array = []
    arrays.resize(Mesh.ARRAY_MAX)
    arrays[Mesh.ARRAY_VERTEX] = vertices
    var mesh := ArrayMesh.new()
    mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
    var material := StandardMaterial3D.new()
    material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
    material.cull_mode = BaseMaterial3D.CULL_DISABLED
    material.albedo_color = Color(0.22, 0.63, 0.61, 0.8)
    material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
    mesh.surface_set_material(0, material)
    var node := MeshInstance3D.new()
    node.mesh = mesh
    node.name = str(tile["tile_id"])
    add_child(node)
    meshes.append(node)
    return true
