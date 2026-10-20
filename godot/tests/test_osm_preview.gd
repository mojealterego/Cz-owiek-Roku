extends SceneTree
## Headless data-to-runtime test for real OSM-licensed building/road outlines.
var failures := 0

func _initialize() -> void:
	call_deferred("_run")

func _check(value: bool, message: String) -> void:
	if value:
		print("PASS: " + message)
	else:
		failures += 1
		push_error("FAIL: " + message)

func _run() -> void:
	var layer = load("res://scripts/osm_preview_layer.gd").new()
	root.add_child(layer)
	_check(layer.loaded, "OSM layer loaded")
	_check(layer.tile_count == 4, "Four metric tiles imported")
	_check(layer.building_ids.size() == 117, "117 unique actual building IDs")
	_check(layer.road_ids.size() == 66, "66 unique actual road IDs")
	_check(layer.world_meshes.size() >= 4, "Buildings and roads have renderable lines")
	var found_real_building: bool = layer.building_ids.has("OSM_W198560340")
	_check(found_real_building, "Known real OSM building ID retained")
	var geo_manifest = JSON.parse_string(FileAccess.get_file_as_string("res://data/world/cieszyn_rynek_osm_2026/manifest.json"))
	_check(geo_manifest is Dictionary and geo_manifest.get("terrain_status") == "MISSING", "No fictitious terrain heights")
	_check(geo_manifest is Dictionary and geo_manifest.get("historical_year") == "2026", "OSM data not falsely labelled book-era history")
	print("WORLD OSM RUNTIME FAILURES: ", failures)
	quit(0 if failures == 0 else 1)
