extends Node3D
## Actual OpenStreetMap 2026 current basemap fragment.
## Geometry is a flat, metrically accurate OUTLINE preview; no fictitious
## 3D heights, facades, historical verification or pretend city completion.

var world_root: String = "res://data/world/cieszyn_rynek_osm_2026"
const TILE_SIZE_M := 256.0
var expected_city_id: String = "CIESZYN_RYNEK"
var expected_source_id: String = "OPENSTREETMAP_2026_CIESZYN_RYNEK"

var loaded: bool = false
var building_ids: Dictionary = {}
var road_ids: Dictionary = {}
var tile_count: int = 0
var world_meshes: Array[MeshInstance3D] = []

func _ready() -> void:
	loaded = load_tiles()
	if not loaded:
		push_warning("OSM geometry unavailable or invalid. Showing two control points only.")

func load_tiles() -> bool:
	var manifest_path: String = world_root + "/manifest.json"
	if not FileAccess.file_exists(manifest_path):
		return false
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not parsed is Dictionary:
		return false
	var manifest: Dictionary = parsed
	if manifest.get("schema_version", 0) != 1 or manifest.get("city_id", "") != expected_city_id:
		return false
	if manifest.get("build_status", "") != "CURRENT_BASEMAP_NOT_HISTORICALLY_VERIFIED":
		return false
	if manifest.get("projection", "") != "LOCAL_WGS84_AEQD":
		return false
	if manifest.get("tile_size_m", 0) != 256 or manifest.get("historical_year", "") != "2026":
		return false
	if manifest.get("source", {}).get("id", "") != expected_source_id:
		return false
	if manifest.get("source", {}).get("license", "") != "ODbL-1.0":
		return false
	if not manifest.get("redistribution_allowed", false):
		return false
	var names: PackedStringArray = DirAccess.get_files_at(ROOT)
	var imported: int = 0
	for filename in names:
		if not filename.ends_with(".json") or filename == "manifest.json":
			continue
		var path: String = world_root + "/" + filename
		var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
		if not value is Dictionary:
			return false
		if not _import_tile(value):
			return false
		imported += 1
	tile_count = imported
	return imported == int(manifest.get("tile_count", -1)) and imported > 0

func _import_tile(tile: Dictionary) -> bool:
	if tile.get("schema_version", 0) != 1 or tile.get("type", "") != "WORLD_METRIC_TILE":
		return false
	if tile.get("city_id", "") != expected_city_id or tile.get("year", "") != "2026":
		return false
	if tile.get("tile_size_m", 0) != 256 or not tile.get("features") is Array:
		return false
	var east_origin: float = float(tile.get("origin_east_m", NAN))
	var north_origin: float = float(tile.get("origin_north_m", NAN))
	if not is_finite(east_origin) or not is_finite(north_origin):
		return false
	if fposmod(east_origin, TILE_SIZE_M) != 0.0 or fposmod(north_origin, TILE_SIZE_M) != 0.0:
		return false
	var building_vertices: PackedVector3Array = PackedVector3Array()
	var road_vertices: PackedVector3Array = PackedVector3Array()
	for raw in tile["features"]:
		if not raw is Dictionary:
			return false
		var feature: Dictionary = raw
		if feature.get("elevation_status", "") != "UNKNOWN_NO_TERRAIN":
			return false
		var kind: String = str(feature.get("kind", ""))
		var id_text: String = str(feature.get("id", ""))
		if not id_text.begins_with("OSM_W"):
			return false
		var geometry_type: String = str(feature.get("geometry_type", ""))
		var coordinates: Variant = feature.get("coordinates")
		if not coordinates is Array:
			return false
		if kind == "building":
			building_ids[id_text] = true
			if geometry_type == "Polygon":
				for ring in coordinates:
					if not _append_lines(building_vertices, ring, east_origin, north_origin, 0.65):
						return false
			elif geometry_type == "MultiPolygon":
				for polygon in coordinates:
					for ring in polygon:
						if not _append_lines(building_vertices, ring, east_origin, north_origin, 0.65):
							return false
			else:
				return false
		elif kind == "road":
			road_ids[id_text] = true
			if geometry_type == "LineString":
				if not _append_lines(road_vertices, coordinates, east_origin, north_origin, 0.35):
					return false
			elif geometry_type == "MultiLineString":
				for line in coordinates:
					if not _append_lines(road_vertices, line, east_origin, north_origin, 0.35):
						return false
			else:
				return false
		else:
			return false
	_render_lines(road_vertices, Color(0.32, 0.64, 0.8), "OSM_ROADS_2026")
	_render_lines(building_vertices, Color(0.94, 0.7, 0.37), "OSM_BUILDINGS_2026")
	return true

func _append_lines(vertices: PackedVector3Array, points: Array,
		east_origin: float, north_origin: float, height: float) -> bool:
	if points.size() < 2:
		return false
	var previous: Vector3 = Vector3.ZERO
	var first: bool = true
	for point in points:
		if not point is Array or point.size() != 2:
			return false
		var east: float = float(point[0])
		var north: float = float(point[1])
		if not is_finite(east) or not is_finite(north):
			return false
		if east < -0.001 or east > TILE_SIZE_M + 0.001:
			return false
		if north < -0.001 or north > TILE_SIZE_M + 0.001:
			return false
		var now := Vector3(east_origin + east, height, -(north_origin + north))
		if not first:
			vertices.append(previous)
			vertices.append(now)
		first = false
		previous = now
	return true

func _render_lines(vertices: PackedVector3Array, color: Color, surface_name: String) -> void:
	if vertices.is_empty():
		return
	var material: StandardMaterial3D = StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = color
	var mesh: ImmediateMesh = ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINES, material)
	for point in vertices:
		mesh.surface_add_vertex(point)
	mesh.surface_end()
	var instance: MeshInstance3D = MeshInstance3D.new()
	instance.name = surface_name + "_" + str(world_meshes.size())
	instance.mesh = mesh
	add_child(instance)
	world_meshes.append(instance)
