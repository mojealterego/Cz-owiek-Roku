extends RefCounted
## In-game performance observations, NOT device benchmark certification.
## Data stays in user:// and is never uploaded or shared automatically.
const SCHEMA: int = 1
const WINDOW: int = 240
const MAX_FRAME_DELTA_S: float = 2.0
const REPORT_STATUS := "OBSERVATIONAL_DEBUG_ONLY_NOT_DEVICE_CERTIFICATION"

var recent_ms: Array[float] = []
var frame_count: int = 0
var total_frame_time_ms: float = 0.0
var peak_frame_ms: float = 0.0
var peak_static_memory_bytes: int = 0
var peak_resident_sectors: int = 0
var peak_resident_meshes: int = 0
var invalid_frame_count: int = 0

func record_frame(delta_seconds: float, resident_sectors: int,
        resident_meshes: int, static_memory_bytes: int) -> bool:
    if not is_finite(delta_seconds) or delta_seconds <= 0.0 or delta_seconds > MAX_FRAME_DELTA_S:
        invalid_frame_count += 1
        return false
    if resident_sectors < 0 or resident_meshes < 0 or static_memory_bytes < 0:
        invalid_frame_count += 1
        return false
    var ms: float = delta_seconds * 1000.0
    frame_count += 1
    total_frame_time_ms += ms
    peak_frame_ms = maxf(peak_frame_ms, ms)
    peak_resident_sectors = maxi(peak_resident_sectors, resident_sectors)
    peak_resident_meshes = maxi(peak_resident_meshes, resident_meshes)
    peak_static_memory_bytes = maxi(peak_static_memory_bytes, static_memory_bytes)
    recent_ms.append(ms)
    if recent_ms.size() > WINDOW:
        recent_ms.pop_front()
    return true

func _percentile95() -> float:
    if recent_ms.is_empty():
        return 0.0
    var ordered: Array[float] = recent_ms.duplicate()
    ordered.sort()
    var offset: int = clampi(ceili(float(ordered.size()) * 0.95) - 1, 0, ordered.size() - 1)
    return ordered[offset]

func snapshot() -> Dictionary:
    return {
        "schema_version": SCHEMA,
        "status": REPORT_STATUS,
        "sample_count": frame_count,
        "sample_duration_seconds": snappedf(total_frame_time_ms / 1000.0, 0.001),
        "sample_average_fps": (float(frame_count) * 1000.0 / total_frame_time_ms if total_frame_time_ms > 0.0 else 0.0),
        "recent_frame_window_count": recent_ms.size(),
        "window_p95_frame_ms": _percentile95(),
        "worst_observed_frame_ms": peak_frame_ms,
        "peak_static_memory_bytes": peak_static_memory_bytes,
        "peak_resident_sectors": peak_resident_sectors,
        "peak_resident_meshes": peak_resident_meshes,
        "invalid_frame_count": invalid_frame_count,
        "run_source": "RUNTIME_OBSERVATION_NO_CPU_GPU_PROFILING",
        "historical_city_verified": false,
        "real_device_test_report": false,
    }

func save_report(path: String) -> bool:
    if frame_count < 10 or path != "user://world_qa_metrics.json":
        return false
    var report: Dictionary = snapshot()
    report["save_utc_unix_time"] = int(Time.get_unix_time_from_system())
    var target: String = ProjectSettings.globalize_path(path)
    var temporary: String = target + ".tmp"
    var stream := FileAccess.open(temporary, FileAccess.WRITE)
    if stream == null:
        return false
    stream.store_string(JSON.stringify(report))
    stream.flush()
    stream.close()
    return DirAccess.rename_absolute(temporary, target) == OK
