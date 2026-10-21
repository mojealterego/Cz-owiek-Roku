extends SceneTree
## INTERNAL CI ONLY. Imports genuine ČÚZK data generated during this same run.
## Source and meshes remain on this runner; nothing is uploaded or committed.

var failures: int = 0
const ARG_PREFIX := "--terrain-source="
const EXPECTED_FOLDER := "/tmp/cuzk_dmr5g_unpublished_world_tiles"
const QA_FOLDER := "user://cuzk_dmr5g_ci_only"

func _initialize() -> void:
    call_deferred("_run")

func _check(test_value: bool, message: String) -> void:
    if test_value:
        print("PASS: " + message)
    else:
        failures += 1
        push_error("FAIL: " + message)

func _prepare_qa_input() -> bool:
    var provided: String = ""
    for parameter in OS.get_cmdline_user_args():
        if parameter.begins_with(ARG_PREFIX):
            provided = parameter.trim_prefix(ARG_PREFIX)
    if provided != EXPECTED_FOLDER:
        push_error("Private QA input path missing or unexpected")
        return false
    if not FileAccess.file_exists(provided + "/manifest.json"):
        push_error("Real ČÚZK dataset was not generated")
        return false
    var output_abs: String = ProjectSettings.globalize_path(QA_FOLDER)
    if DirAccess.make_dir_recursive_absolute(output_abs) != OK:
        push_error("Failed to create Godot user:// QA directory")
        return false
    var names: PackedStringArray = DirAccess.get_files_at(provided)
    var copied: int = 0
    for name in names:
        if not name.ends_with(".json"):
            continue
        if DirAccess.copy_absolute(provided + "/" + name, output_abs + "/" + name) != OK:
            push_error("Unable to import private JSON into isolated user://")
            return false
        copied += 1
    return copied == 5

func _make_layer(datum: String, enabled: bool):
    var layer = load("res://scripts/terrain_qa_layer.gd").new()
    layer.qa_folder = QA_FOLDER
    layer.expected_city_id = "CESKY_TESIN_CENTER"
    layer.expected_source_id = "CUZK_DMR5G_IMAGESERVER"
    layer.expected_vertical_datum = datum
    layer.qa_mode_enabled = enabled
    root.add_child(layer)
    return layer

func _run() -> void:
    if not _prepare_qa_input():
        quit(1)
        return
    var manifest_variant: Variant = JSON.parse_string(
        FileAccess.get_file_as_string(QA_FOLDER + "/manifest.json"))
    _check(manifest_variant is Dictionary, "Private real terrain manifest parses")
    if not manifest_variant is Dictionary:
        quit(1)
        return
    var manifest: Dictionary = manifest_variant
    _check(manifest.get("source_crs", "") == "EPSG:5514",
           "Official horizontal CRS 5514")
    _check(manifest.get("vertical_datum", "") == "CZ-BPV",
           "Official Czech Bpv heights retained")
    _check(manifest.get("vertical_registration_to_game", "") == "NOT_VERIFIED",
           "No fabricated cross-border datum conversion")
    _check(manifest.get("rights_review_status", "") == "REVIEW_PENDING_INTERNAL_ONLY",
           "Unapproved source cannot enter public Android APK")
    _check(manifest.get("tile_count", 0) == 4, "4 sourced 256-metre tiles")

    var terrain = _make_layer("CZ-BPV", true)
    _check(terrain.loaded, "Real ČÚZK heights loaded into Godot 3D mesh")
    _check(terrain.tile_count == 4, "Four real terrain meshes tile-consistent")
    _check(terrain.meshes.size() == 4, "Four generated Godot ArrayMeshes")
    _check(terrain.valid_sample_count == int(manifest.get("valid_sample_count", -1)),
           "Godot used every actually imported source sample")
    _check(terrain.valid_sample_count > 100, "At least 100 noninvented height samples")
    _check(terrain.triangle_count > 300, "Real 3D surfaces triangulated, not flat wireframes")
    var min_h: float = INF
    var max_h: float = -INF
    for node in terrain.meshes:
        var bounds: AABB = node.get_aabb()
        min_h = minf(min_h, bounds.position.y)
        max_h = maxf(max_h, bounds.end.y)
        _check(bounds.size.x > 250.0, "Each mesh retains metre-scale tile width")
    _check(min_h > 150.0 and max_h < 500.0, "Raw Bpv height values remain physical")
    _check(max_h - min_h > 1.0, "3D height differences came from source DEM")
    print("REAL_CUZK_GODOT_QA HEIGHT_RANGE_M: %.3f ... %.3f" % [min_h, max_h])
    print("REAL_CUZK_GODOT_QA TRIANGLES: ", terrain.triangle_count)

    var forbidden = _make_layer("PL-KRON86-NH", true)
    _check(not forbidden.loaded, "Polish KRON86 and Czech Bpv cannot be silently mixed")
    var closed = _make_layer("CZ-BPV", false)
    _check(not closed.loaded, "Private sourced terrain blocked in game default mode")
    print("REAL_CUZK_GODOT_QA FAILURES: ", failures)
    quit(0 if failures == 0 else 1)
