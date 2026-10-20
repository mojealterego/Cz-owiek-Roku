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
	print("TESTS FAILED: ", failed)
	quit(0 if failed == 0 else 1)
