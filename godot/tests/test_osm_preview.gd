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
	var cz = load("res://scripts/osm_preview_layer.gd").new()
	cz.world_root = "res://data/world/cesky_tesin_center_osm_2026"
	cz.expected_city_id = "CESKY_TESIN_CENTER"
	cz.expected_source_id = "OPENSTREETMAP_2026_CESKY_TESIN_CENTER"
	root.add_child(cz)
	_check(cz.loaded, "Real Czech OSM layer loaded")
	_check(cz.tile_count == 9, "Nine Czech geospatial 256m tiles")
	_check(cz.building_ids.size() == 280, "280 real Czech building IDs")
	_check(cz.road_ids.size() == 79, "79 real Czech road IDs")
	_check(layer.building_ids.size() + cz.building_ids.size() == 397, "397 real PL and CZ building outlines")
	_check(layer.road_ids.size() + cz.road_ids.size() == 145, "145 real PL and CZ road ways")
	_check(layer.world_meshes.size() >= 4, "Buildings and roads have renderable lines")
	var found_real_building: bool = layer.building_ids.has("OSM_W198560340")
	_check(found_real_building, "Known real OSM building ID retained")
	var geo_manifest = JSON.parse_string(FileAccess.get_file_as_string("res://data/world/cieszyn_rynek_osm_2026/manifest.json"))
	_check(geo_manifest is Dictionary and geo_manifest.get("terrain_status") == "MISSING", "No fictitious terrain heights")
	_check(geo_manifest is Dictionary and geo_manifest.get("historical_year") == "2026", "OSM data not falsely labelled book-era history")
	# Artificial test value must remain a TEST; never claim actual OSM heights.
	var synthetic := {
		"schema_version": 1, "type": "WORLD_METRIC_TILE",
		"city_id": "CIESZYN_RYNEK", "year": "2026", "tile_size_m": 256,
		"origin_east_m": 0, "origin_north_m": 0,
		"features": [{
			"id": "OSM_W999999998", "kind": "building", "name": "SYNTHETIC_TEST_ONLY",
			"geometry_type": "Polygon", "elevation_status": "UNKNOWN_NO_TERRAIN",
			"coordinates": [[[10, 10], [20, 10], [20, 20], [10, 20], [10, 10]]],
			"height_m": 12.5, "height_source": "OSM_HEIGHT_TAG",
			"height_status": "OSM_REPORTED_UNVERIFIED"
		}]
	}
	_check(layer._import_tile(synthetic), "Tagged-height test fixture is accepted")
	_check(layer.sourced_height_ids.has("OSM_W999999998"), "Explicit metres retained")
	_check(layer.height_wireframe_count > 0, "Tagged-height vertical wireframe emitted")
	var no_provenance := synthetic.duplicate(true)
	no_provenance["features"][0].erase("height_source")
	_check(not layer._import_tile(no_provenance), "Height missing provenance rejected")
	var only_floors := synthetic.duplicate(true)
	for attribute in ["height_m", "height_source", "height_status"]:
		only_floors["features"][0].erase(attribute)
	only_floors["features"][0]["building_levels"] = 4
	only_floors["features"][0]["levels_status"] = "OSM_LEVEL_COUNT_ONLY_NOT_HEIGHT"
	_check(layer._import_tile(only_floors), "Floor count is not converted to metres")
	_check(layer.levels_only_ids.has("OSM_W999999998"), "Floor count tracked without 3D height")
	print("WORLD OSM RUNTIME FAILURES: ", failures)
	quit(0 if failures == 0 else 1)
