extends RefCounted
## Isolated reference state for the Godot vertical slice; no source dialogue is stored here.

const SCHEMA: int = 1
const CANONICAL_ENDING: String = "CCR_MAIN_INEVITABLE_END"

var language: String = "pl"
var chapter: int = 1
var inspected: Array[String] = []
var choice: String = ""
var shots: Array[String] = []
var chapter_completed: bool = false

func mark_inspected(subject: String) -> bool:
	if subject not in ["CAMERA", "GALA_PROGRAM", "FAMILY_PHOTO"]:
		return false
	if subject in inspected:
		return false
	inspected.append(subject)
	return true

func choose(value: String) -> bool:
	if value not in ["PHOTO_AUDIENCE", "LISTEN_AUDIENCE"]:
		return false
	if choice != "":
		return choice == value
	choice = value
	return true

func complete() -> bool:
	if choice == "":
		return false
	chapter_completed = true
	return true

func to_dictionary() -> Dictionary:
	return {
		"schema": SCHEMA,
		"language": language,
		"chapter": chapter,
		"inspected": inspected,
		"choice": choice,
		"shots": shots,
		"chapter_completed": chapter_completed,
	}

static func from_dictionary(raw: Variant) -> RefCounted:
	if not raw is Dictionary:
		return null
	if raw.get("schema", -1) != SCHEMA or raw.get("chapter", -1) != 1:
		return null
	var lang: String = str(raw.get("language", ""))
	var option: String = str(raw.get("choice", ""))
	if lang not in ["pl", "en"] or option not in ["", "PHOTO_AUDIENCE", "LISTEN_AUDIENCE"]:
		return null
	if not raw.get("inspected", null) is Array or not raw.get("shots", null) is Array:
		return null
	if not raw.get("chapter_completed", null) is bool:
		return null
	if raw["chapter_completed"] and option == "":
		return null
	var s = load("res://scripts/narrative_state.gd").new()
	s.language = lang
	s.chapter = 1
	s.choice = option
	s.chapter_completed = raw["chapter_completed"]
	for value in raw["inspected"]:
		if not value is String or value not in ["CAMERA", "GALA_PROGRAM", "FAMILY_PHOTO"]:
			return null
		if value in s.inspected:
			return null
		s.inspected.append(value)
	for path in raw["shots"]:
		if not path is String or not path.begins_with("user://photos/") or not path.ends_with(".png"):
			return null
		if path in s.shots:
			return null
		s.shots.append(path)
	return s

func write_save() -> bool:
	var target: String = ProjectSettings.globalize_path("user://moty.save.json")
	var temp: String = target + ".tmp"
	var file: FileAccess = FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return false
	file.store_string(JSON.stringify(to_dictionary()))
	file.flush()
	file.close()
	var result: Error = DirAccess.rename_absolute(temp, target)
	return result == OK

static func read_save() -> RefCounted:
	if not FileAccess.file_exists("user://moty.save.json"):
		return null
	var raw_text: String = FileAccess.get_file_as_string("user://moty.save.json")
	var data: Variant = JSON.parse_string(raw_text)
	return from_dictionary(data)
