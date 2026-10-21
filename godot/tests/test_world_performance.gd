extends SceneTree
const Model = preload("res://scripts/world_performance.gd")
var fails: int = 0

func _initialize() -> void:
    call_deferred("_run")

func _check(ok: bool, context: String) -> void:
    if ok:
        print("PASS: " + context)
    else:
        fails += 1
        push_error("FAIL: " + context)

func _run() -> void:
    var s = Model.new()
    _check(not s.save_report("user://world_qa_metrics.json"), "No false empty report")
    _check(not s.record_frame(-1.0, 2, 4, 4096), "Reject negative frame time")
    _check(not s.record_frame(0.016, -1, 4, 4096), "Reject impossible sector count")
    for i in range(250):
        var delta: float = 0.04 if i >= 235 else 0.016
        s.record_frame(delta, (i % 6) + 1, (i % 9) + 1, 1024 * (i + 1))
    var report: Dictionary = s.snapshot()
    _check(report["sample_count"] == 250, "Cumulative frame count")
    _check(report["recent_frame_window_count"] == 240, "Rolling 240-frame window capped")
    _check(is_equal_approx(report["window_p95_frame_ms"], 40.0), "p95 reflects slower frames")
    _check(report["peak_static_memory_bytes"] == 250 * 1024, "Peak memory preserved")
    _check(report["peak_resident_sectors"] == 6, "Resident sector peak preserved")
    _check(report["invalid_frame_count"] == 2, "Invalid samples recorded")
    _check(not report["real_device_test_report"], "Never assert certified Android test")
    _check(s.save_report("user://world_qa_metrics.json"), "Local report can be saved")
    var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string("user://world_qa_metrics.json"))
    _check(saved is Dictionary and saved.get("sample_count") == 250, "Stored telemetry is valid JSON")
    _check(not s.save_report("user://other_file.json"), "Restrict unapproved file location")
    DirAccess.remove_absolute(ProjectSettings.globalize_path("user://world_qa_metrics.json"))
    print("WORLD PERFORMANCE MODEL FAILURES: ", fails)
    quit(0 if fails == 0 else 1)
