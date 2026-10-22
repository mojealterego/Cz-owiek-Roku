extends SceneTree
## Headless smoke test for narrative state contracts. Exits non-zero on failures.

const State = preload("res://scripts/narrative_state.gd")
var failed: int = 0

func _initialize() -> void:
	call_deferred("_run")

func check(condition: bool, name: String) -> void:
	if not condition:
		failed += 1
		push_error("FAIL: " + name)
	else:
		print("PASS: " + name)

func _run() -> void:
	var s = State.new()
	check(s.chapter == 1, "starts at canonical CH01")
	check(s.mark_inspected("CAMERA"), "first inspection")
	check(not s.mark_inspected("CAMERA"), "no double-inspection")
	check(not s.mark_inspected("UNKNOWN"), "unknown object denied")
	check(not s.complete(), "cannot complete before choice")
	check(not s.choose("CHEAT"), "unknown choice denied")
	check(s.choose("PHOTO_AUDIENCE"), "accept canonical local choice")
	check(not s.choose("LISTEN_AUDIENCE"), "choice immutable")
	check(s.complete(), "completes after choosing")
	check(s.chapter_completed, "completed stored")
	var serialized = s.to_dictionary()
	var copy = State.from_dictionary(serialized)
	check(copy != null and copy.choice == "PHOTO_AUDIENCE", "valid state restores")
	var invalid: Dictionary = serialized.duplicate(true)
	invalid["chapter"] = 70
	check(State.from_dictionary(invalid) == null, "rejects incompatible chapter")
	invalid = serialized.duplicate(true)
	invalid["shots"] = ["res://secret.txt"]
	check(State.from_dictionary(invalid) == null, "blocks unauthorized photo paths")
	invalid = serialized.duplicate(true)
	invalid["chapter_completed"] = true
	invalid["choice"] = ""
	check(State.from_dictionary(invalid) == null, "rejects broken ending invariant")
	for malicious_path in ["user://photos/../escape.png", "user://photos/nested/file.png", "user://photos/evil\\\\file.png", "user://photos/.png"]:
		invalid = serialized.duplicate(true)
		invalid["shots"] = [malicious_path]
		check(State.from_dictionary(invalid) == null, "rejects unsafe photo path: " + malicious_path)
	invalid = serialized.duplicate(true)
	invalid["shots"] = []
	for i in range(State.MAX_SHOTS + 1):
		invalid["shots"].append("user://photos/photo_%d.png" % i)
	check(State.from_dictionary(invalid) == null, "rejects excessive photo count")
	invalid = serialized.duplicate(true)
	invalid["shots"] = ["user://photos/photo_01.png"]
	check(State.from_dictionary(invalid) != null, "accepts safe photo path")
	var oversized_path: String = "user://moty.save.json"
	var oversized: FileAccess = FileAccess.open(oversized_path, FileAccess.WRITE)
	check(oversized != null, "create oversized save fixture")
	if oversized != null:
		oversized.store_string("x".repeat(State.MAX_SAVE_BYTES + 1))
		oversized.close()
		check(State.read_save() == null, "reject oversized save before parsing")
		DirAccess.remove_absolute(ProjectSettings.globalize_path(oversized_path))
	print("TESTS FAILED: ", failed)
	quit(0 if failed == 0 else 1)
