extends RefCounted
## Isolated reference state for the Godot vertical slice; no source dialogue is stored here.

const SCHEMA: int = 1
const MAX_SAVE_BYTES: int = 65536
const MAX_SHOTS: int = 256
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

func add_shot(path: String) -> bool:
	if shots.size() >= MAX_SHOTS or not _valid_photo_path(path) or path in shots:
		return false
	shots.append(path)
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
	if raw["shots"].size() > MAX_SHOTS:
		return null
	for path in raw["shots"]:
		if not path is String or not _valid_photo_path(path):
			return null
		if path in s.shots:
			return null
		s.shots.append(path)
	return s

static func _valid_photo_path(path: String) -> bool:
	if path.length() > 160 or not path.begins_with("user://photos/") or not path.ends_with(".png"):
		return false
	var filename: String = path.trim_prefix("user://photos/").trim_suffix(".png")
	if filename.is_empty() or filename == "." or filename == "..":
		return false
	for character in filename:
		if not (character in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"):
			return false
	return true

func write_save() -> bool:
	var target: String = ProjectSettings.globalize_path("user://moty.save.json")
	var temp: String = target + ".tmp"
	var file: FileAccess = FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return false
	var payload: String = JSON.stringify(to_dictionary())
	if payload.to_utf8_buffer().size() > MAX_SAVE_BYTES:
		file.close()
		DirAccess.remove_absolute(temp)
		return false
	file.store_string(payload)
	file.flush()
	file.close()
	var result: Error = DirAccess.rename_absolute(temp, target)
	return result == OK

static func read_save() -> RefCounted:
	if not FileAccess.file_exists("user://moty.save.json"):
		return null
	var handle: FileAccess = FileAccess.open("user://moty.save.json", FileAccess.READ)
	if handle == null:
		return null
	if handle.get_length() > MAX_SAVE_BYTES:
		handle.close()
		return null
	var raw_text: String = handle.get_buffer(handle.get_length()).get_string_from_utf8()
	handle.close()
	var data: Variant = JSON.parse_string(raw_text)
	return from_dictionary(data)
