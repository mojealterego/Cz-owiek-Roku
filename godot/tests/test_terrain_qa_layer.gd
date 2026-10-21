extends SceneTree
## Runtime QA uses a synthetic, generated user:// dataset only.
## No synthetic DEM is committed to game assets or export.
var failures: int = 0
var folder: String = "user://terrain_qa_generated"

func _initialize() -> void:
    call_deferred("_run")

func _check(ok: bool, msg: String) -> void:
    if ok:
        print("PASS: " + msg)
    else:
        failures += 1
        push_error("FAIL: " + msg)


func _fixture(unknown_datum: bool = false, break_seam: bool = false) -> void:
    var abs_path: String = ProjectSettings.globalize_path(folder)
    DirAccess.make_dir_recursive_absolute(abs_path)
    var manifest := {
        "schema_version": 1, "type": "WORLD_SOURCE_TERRAIN_QA",
        "status": "GEOTIFF_IMPORTED_NOT_HISTORICALLY_VALIDATED",
        "city_id": "TEST_SYNTHETIC_ONLY",
        "source_id": "SYNTHETIC_QA_RASTER",
        "source_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        "vertical_datum": "TEST_LOCAL_DATUM" if not unknown_datum else "CZ-BPV",
        "source_crs": "EPSG:2180",
        "vertical_registration_to_game": "NOT_VERIFIED",
        "rights_review_status": "REVIEW_PENDING_INTERNAL_ONLY",
        "terrain_source_coverage_complete": false,
        "tile_size_m": 256, "spacing_m": 64, "tile_count": 2
    }
    _write("manifest.json", manifest)
    for tile_i in [0, 1]:
        var heights: Array = []
        for y in range(5):
            for x in range(5):
                var value: float = 275.0 + float((tile_i * 256 + x * 64) + y * 64) * 0.004
                heights.append(snappedf(value, 0.0001))
        if tile_i == 1:
            heights[2 * 5 + 2] = null
            if break_seam:
                heights[0] += 5.0
        var id: String = "E+000000_N+000000" if tile_i == 0 else "E+000001_N+000000"
        _write(id + ".json", {
            "schema_version": 1, "type": "GEOREFERENCED_TERRAIN_QA_TILE",
            "city_id": "TEST_SYNTHETIC_ONLY", "tile_id": id,
            "origin_east_m": tile_i * 256, "origin_north_m": 0,
            "tile_size_m": 256, "spacing_m": 64,
            "grid_width": 5, "grid_height": 5, "heights_m": heights,
            "nodata_count": 1 if tile_i == 1 else 0,
            "vertical_datum": "TEST_LOCAL_DATUM",
            "terrain_alignment": "UNREGISTERED_TO_BUILDINGS",
        })


func _write(name: String, data: Dictionary) -> void:
    var file := FileAccess.open(folder + "/" + name, FileAccess.WRITE)
    file.store_string(JSON.stringify(data))
    file.close()


func _make_layer(expected_datum: String = "TEST_LOCAL_DATUM",
        qa: bool = true):
    var layer = load("res://scripts/terrain_qa_layer.gd").new()
    layer.qa_folder = folder
    layer.expected_city_id = "TEST_SYNTHETIC_ONLY"
    layer.expected_source_id = "SYNTHETIC_QA_RASTER"
    layer.expected_vertical_datum = expected_datum
    layer.qa_mode_enabled = qa
    root.add_child(layer)
    return layer


func _run() -> void:
    _fixture()
    var layer = _make_layer()
    _check(layer.loaded, "Synthetic internal QA terrain mesh builds")
    _check(layer.tile_count == 2, "Two metrically adjacent 256 m sectors")
    _check(layer.triangle_count == 56, "Missing height discards 4 quads, no fabricated terrain")
    _check(layer.rejected_void_quads == 4, "NoData preserved as missing geometry")
    _check(layer.meshes.size() == 2, "Two renderable 3D meshes")
    _check(layer.valid_sample_count == 49, "49 source samples, one null")
    var box: AABB = layer.meshes[0].get_aabb()
    _check(box.size.x >= 255.0, "Real 256m horizontal tile scale")
    _check(box.position.y >= 274.9, "Absolute source heights retained")
    var blocked = _make_layer("CZ-BPV")
    _check(not blocked.loaded, "Unknown datum conversion is blocked")
    var gated = _make_layer("TEST_LOCAL_DATUM", false)
    _check(not gated.loaded, "Runtime refuses to load private QA DEM by default")
    # Deliberately corrupt one tile border after success; loader must fail.
    _fixture(false, true)
    var broken = _make_layer()
    _check(not broken.loaded, "Misaligned neighbor seam blocked")
    print("WORLD TERRAIN MESH FAILURES: ", failures)
    quit(0 if failures == 0 else 1)
