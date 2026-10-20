extends Node3D
## Executable greybox: title, opening cards, stage, inspectable objects, choices,
## photograph capture, touchscreen movement, persistent chapter progress.

const State = preload("res://scripts/narrative_state.gd")
const THEME_BG := Color(0.035, 0.035, 0.042, 0.94)
const IVORY := Color(0.94, 0.88, 0.76)
const GOLD := Color(0.83, 0.65, 0.31)
const BURGUNDY := Color(0.29, 0.045, 0.065)
const MOVE_SPEED := 3.4

const TEXT := {
	"pl": {
		"start": "ROZPOCZNIJ", "continue": "KONTYNUUJ ZAPIS", "resume": "KONTYNUUJ",
		"prologue": "SŁOWO OD CZŁOWIEKA ROKU",
		"prologue_note": "Prolog filmowy. Pełny odczyt autorskiego tekstu i nagranie lektora muszą zostać dołączone jako zatwierdzony, chroniony zasób. Ta wersja zawiera oryginalną inscenizację bez zastępczej imitacji nagrania.",
		"prologue_skip": "PRZEJDŹ DO AKTU I (BEZ NAGRANIA)",
		"act": "AKT I — PĘKNIĘCIE", "act_quote": "Każde pęknięcie zaczyna się od milczenia.",
		"chapter": "ROZDZIAŁ I", "chapter_quote": "„Piekło to inni.” — Jean-Paul Sartre",
		"chapter_note": "(Albo po prostu Cieszyn w grudniowy wieczór.) — Andrzej, Pamiętnik Sprawcy, Cieszyn 2023 r.",
		"enter": "WEJDŹ ZA KULISY", "inspect": "ZBADAJ", "photo": "ZDJĘCIE", "gallery": "GALERIA",
		"movement": "Ruch: WASD / przyciski dotykowe. Podejdź do aparatu, programu gali lub fotografii.",
		"camera": "Aparat fotograficzny — narzędzie obserwacji i przyszłych dowodów.",
		"gala": "Program gali — sceniczna fasada sukcesu i lista gości.",
		"family": "Fotografia rodzinna — pamięć, której nie widać w świetle reflektorów.",
		"choose_header": "CO ZROBISZ, ZANIM WYJDZIESZ NA SCENĘ?",
		"choice_a": "SFOTOGRAFUJ WIDOWNIĘ", "choice_b": "ODŁÓŻ APARAT I SŁUCHAJ",
		"choice_result_a": "Pozostaje kadr pierwszego rzędu. Dźwięki sali zagłusza migawka.",
		"choice_result_b": "Zapamiętujesz urywki rozmów i niespokojny szmer sali.",
		"checkpoint": "ZAPISANO. CH01: WRĘCZENIE WYRÓŻNIENIA",
		"prototype_end": "Koniec grywalnego fragmentu CH01. Rozdziały 02–70 nie są jeszcze implementacją 3D.",
		"restart": "POWRÓT DO MENU", "close": "ZAMKNIJ", "no_photos": "Brak zdjęć z tego przejścia.",
		"snapshot": "Fotografia zapisana w urządzeniu.", "snapshot_error": "Błąd zapisu fotografii.",
		"save_error": "Uwaga: zapis postępu nie powiódł się.",
	},
	"en": {
		"start": "BEGIN", "continue": "CONTINUE SAVE", "resume": "CONTINUE",
		"prologue": "A WORD FROM THE MAN OF THE YEAR",
		"prologue_note": "Film prologue. The complete author-approved reading and narrator recording must be provided as an approved, protected asset. This build uses an original staged opening without fabricating a replacement recording.",
		"prologue_skip": "CONTINUE TO ACT I (NO RECORDING)",
		"act": "ACT I — THE FRACTURE", "act_quote": "Every fracture begins with silence.",
		"chapter": "CHAPTER I", "chapter_quote": "“Hell is other people.” — Jean-Paul Sartre",
		"chapter_note": "(Or simply Cieszyn on a December evening.) — Andrzej, The Perpetrator's Diary, Cieszyn 2023.",
		"enter": "STEP BEHIND THE CURTAIN", "inspect": "INSPECT", "photo": "TAKE PHOTO", "gallery": "GALLERY",
		"movement": "Move: WASD / touch buttons. Approach the camera, gala program or photograph.",
		"camera": "Camera — a tool for observation and future evidence.",
		"gala": "Gala program — the public façade of success and a list of guests.",
		"family": "Family photograph — the memory lost beneath the spotlights.",
		"choose_header": "WHAT WILL YOU DO BEFORE TAKING THE STAGE?",
		"choice_a": "PHOTOGRAPH THE AUDIENCE", "choice_b": "LOWER THE CAMERA AND LISTEN",
		"choice_result_a": "The first row remains on film. The shutter drowns out the hall.",
		"choice_result_b": "You remember scraps of conversation and the uneasy murmur of the hall.",
		"checkpoint": "SAVED. CH01: THE AWARD CEREMONY",
		"prototype_end": "End of playable CH01 slice. Chapters 02–70 are not yet implemented in 3D.",
		"restart": "RETURN TO MENU", "close": "CLOSE", "no_photos": "No photographs captured in this run.",
		"snapshot": "Photograph stored on device.", "snapshot_error": "Failed to save photograph.",
		"save_error": "Warning: could not save progress.",
	},
}

var state = State.new()
var phase: String = "TITLE"
var hero: Node3D
var view_camera: Camera3D
var interface: Control
var overlay: Control
var status_label: Label
var interact_button: Button
var photo_button: Button
var nearest: String = ""
var inspect_locations: Dictionary = {
	"CAMERA": Vector3(-3, 0, 0),
	"GALA_PROGRAM": Vector3(0, 0, -2.0),
	"FAMILY_PHOTO": Vector3(3, 0, 0),
}
var pad: Dictionary = {"left": false, "right": false, "up": false, "down": false}
var shot_in_progress: bool = false
var shot_count: int = 0

func t(key: String) -> String:
	return str(TEXT[state.language].get(key, key))

func _ready() -> void:
	_build_environment()
	_build_interface()
	_show_menu()

func _make_material(color: Color, metallic: float = 0.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metallic
	material.roughness = 0.77
	return material

func _box(at: Vector3, dims: Vector3, color: Color, metal: float = 0.0) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = dims
	mesh.material = _make_material(color, metal)
	var obj := MeshInstance3D.new()
	obj.mesh = mesh
	obj.position = at
	add_child(obj)
	return obj

func _build_environment() -> void:
	_box(Vector3(0, -0.15, 0), Vector3(23, 0.3, 17), Color(0.15, 0.13, 0.12))
	_box(Vector3(0, 2.5, -7.4), Vector3(23, 5, 0.4), Color(0.10, 0.09, 0.10))
	_box(Vector3(-11, 2, 0), Vector3(0.35, 4, 17), Color(0.16, 0.13, 0.14))
	_box(Vector3(11, 2, 0), Vector3(0.35, 4, 17), Color(0.16, 0.13, 0.14))
	_box(Vector3(0, 0.25, -5.5), Vector3(11, 0.5, 3), Color(0.22, 0.16, 0.11))
	_box(Vector3(-5.4, 2.8, -5.55), Vector3(0.6, 5.6, 0.45), GOLD)
	_box(Vector3(5.4, 2.8, -5.55), Vector3(0.6, 5.6, 0.45), GOLD)
	_box(Vector3(-2.85, 2.3, -5.7), Vector3(5.5, 4.6, 0.25), BURGUNDY)
	_box(Vector3(2.85, 2.3, -5.7), Vector3(5.5, 4.6, 0.25), BURGUNDY)
	_box(Vector3(0, 5.5, -5.7), Vector3(11, 0.4, 0.55), GOLD)
	for i in range(9):
		var x: float = -8.0 + float(i) * 2.0
		_box(Vector3(x, 0.42, 5), Vector3(1.35, 0.8, 1.15), Color(0.075, 0.068, 0.075))
		_box(Vector3(x, 0.55, 6.6), Vector3(1.35, 1.1, 0.25), Color(0.11, 0.085, 0.095))
	var prop_colors: Array[Color] = [Color(0.22, 0.24, 0.28), GOLD, Color(0.37, 0.32, 0.26)]
	var subjects: Array[String] = ["CAMERA", "GALA_PROGRAM", "FAMILY_PHOTO"]
	for i in range(3):
		_box(inspect_locations[subjects[i]] + Vector3(0, 0.55, 0), Vector3(0.8, 1.1, 0.55), prop_colors[i])
		_box(inspect_locations[subjects[i]] + Vector3(0, 1.16, 0), Vector3(0.55, 0.07, 0.52), IVORY)
	hero = Node3D.new()
	add_child(hero)
	hero.position = Vector3(0, 0, 3.0)
	var body := CapsuleMesh.new()
	body.radius = 0.3
	body.height = 1.75
	body.material = _make_material(Color(0.065, 0.14, 0.27))
	var figure := MeshInstance3D.new()
	figure.mesh = body
	figure.position = Vector3(0, 1.0, 0)
	hero.add_child(figure)
	view_camera = Camera3D.new()
	add_child(view_camera)
	view_camera.current = true
	view_camera.fov = 67
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-56, 19, 0)
	sun.light_energy = 0.7
	add_child(sun)
	var light := OmniLight3D.new()
	light.position = Vector3(0, 4.8, -4.5)
	light.light_color = Color(1, 0.78, 0.48)
	light.light_energy = 1.5
	light.omni_range = 16
	add_child(light)
	var env := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.055, 0.05, 0.06)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.43, 0.35, 0.29)
	environment.ambient_light_energy = 0.9
	env.environment = environment
	add_child(env)
	_sync_camera()

func _sync_camera() -> void:
	if view_camera == null:
		return
	view_camera.global_position = hero.global_position + Vector3(2.8, 3.0, 6.6)
	view_camera.look_at(hero.global_position + Vector3(0, 1.25, -0.25))

func _label(message: String, size: int = 25, gold: bool = false) -> Label:
	var label := Label.new()
	label.text = message
	label.add_theme_color_override("font_color", GOLD if gold else IVORY)
	label.add_theme_font_size_override("font_size", size)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return label

func _button(message: String, into: Node, action: Callable) -> Button:
	var btn := Button.new()
	btn.text = message
	btn.custom_minimum_size = Vector2(240, 54)
	btn.add_theme_font_size_override("font_size", 20)
	btn.pressed.connect(action)
	into.add_child(btn)
	return btn

func _build_interface() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	interface = Control.new()
	interface.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(interface)
	overlay = Control.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	interface.add_child(overlay)

func _clear_overlay() -> void:
	for child in overlay.get_children():
		child.queue_free()
	status_label = null
	interact_button = null
	photo_button = null

func _modal(title: String, body: String) -> VBoxContainer:
	_clear_overlay()
	var shade := ColorRect.new()
	shade.color = THEME_BG
	shade.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.add_child(shade)
	var margins := MarginContainer.new()
	margins.set_anchors_preset(Control.PRESET_FULL_RECT)
	margins.add_theme_constant_override("margin_left", 90)
	margins.add_theme_constant_override("margin_right", 90)
	margins.add_theme_constant_override("margin_top", 40)
	margins.add_theme_constant_override("margin_bottom", 40)
	overlay.add_child(margins)
	var content := VBoxContainer.new()
	content.alignment = BoxContainer.ALIGNMENT_CENTER
	content.add_theme_constant_override("separation", 22)
	margins.add_child(content)
	content.add_child(_label(title, 37, true))
	var sub := _label(body, 21)
	sub.custom_minimum_size.y = 100
	content.add_child(sub)
	return content

func _show_menu() -> void:
	phase = "TITLE"
	var container := _modal("CZŁOWIEK ROKU / MAN OF THE YEAR", "ANDROID • CINEMATIC DRAMA • CH01 GREYBOX")
	_button(t("start"), container, _new_game)
	var old = State.read_save()
	if old != null:
		_button(t("continue"), container, _continue_game)
	_button("POLSKI / ENGLISH", container, _toggle_language)
	_button(t("gallery"), container, _show_gallery)

func _toggle_language() -> void:
	state.language = "en" if state.language == "pl" else "pl"
	_show_menu()

func _new_game() -> void:
	var lang: String = state.language
	state = State.new()
	state.language = lang
	hero.position = Vector3(0, 0, 3)
	_show_prologue()

func _continue_game() -> void:
	var loaded = State.read_save()
	if loaded == null:
		_show_menu()
		return
	state = loaded
	if state.chapter_completed:
		_show_end()
	else:
		_enter_world()

func _show_prologue() -> void:
	phase = "PROLOGUE"
	var panel := _modal(t("prologue"), t("prologue_note"))
	_button(t("prologue_skip"), panel, _show_curtain)

func _show_curtain() -> void:
	phase = "ACT"
	var content := _modal(t("act"), t("act_quote"))
	_button(t("resume"), content, _open_curtain)

func _open_curtain() -> void:
	phase = "CURTAIN"
	_clear_overlay()
	var dims: Vector2 = get_viewport().get_visible_rect().size
	var left := ColorRect.new()
	left.color = BURGUNDY
	left.position = Vector2.ZERO
	left.size = Vector2(dims.x / 2.0 + 2.0, dims.y)
	overlay.add_child(left)
	var right := ColorRect.new()
	right.color = BURGUNDY
	right.position = Vector2(dims.x / 2.0, 0)
	right.size = Vector2(dims.x / 2.0 + 2.0, dims.y)
	overlay.add_child(right)
	var tween := create_tween()
	tween.set_parallel(true)
	tween.tween_property(left, "position:x", -dims.x / 2.0 - 4.0, 1.35)
	tween.tween_property(right, "position:x", dims.x + 4.0, 1.35)
	await tween.finished
	_show_chapter_card()

func _show_chapter_card() -> void:
	phase = "CHAPTER_CARD"
	var panel := _modal(t("chapter"), t("chapter_quote") + "\n" + t("chapter_note"))
	_button(t("enter"), panel, _enter_world)

func _enter_world() -> void:
	phase = "EXPLORATION"
	_clear_overlay()
	status_label = _label(t("movement"), 18)
	status_label.anchor_right = 1.0
	status_label.offset_top = 10
	status_label.offset_bottom = 68
	overlay.add_child(status_label)
	var top := HBoxContainer.new()
	top.position = Vector2(18, 70)
	overlay.add_child(top)
	_button(t("gallery"), top, _show_gallery)
	var bottom := HBoxContainer.new()
	bottom.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_left = 16
	bottom.offset_right = -16
	bottom.offset_top = -90
	bottom.offset_bottom = -12
	bottom.alignment = BoxContainer.ALIGNMENT_END
	overlay.add_child(bottom)
	for binding in [["◀","left"],["▲","up"],["▼","down"],["▶","right"]]:
		var btn := _button(binding[0], bottom, func() -> void: pass)
		btn.custom_minimum_size = Vector2(75, 65)
		btn.button_down.connect(func() -> void: pad[binding[1]] = true)
		btn.button_up.connect(func() -> void: pad[binding[1]] = false)
	photo_button = _button(t("photo"), bottom, _take_photo)
	photo_button.custom_minimum_size = Vector2(148, 65)
	interact_button = _button(t("inspect"), bottom, _inspect_nearest)
	interact_button.custom_minimum_size = Vector2(140, 65)
	interact_button.visible = false
	_sync_camera()

func _physics_process(delta: float) -> void:
	if phase != "EXPLORATION":
		return
	var axis := Vector2(
		float(Input.is_key_pressed(KEY_D)) - float(Input.is_key_pressed(KEY_A)) + float(pad["right"]) - float(pad["left"]),
		float(Input.is_key_pressed(KEY_S)) - float(Input.is_key_pressed(KEY_W)) + float(pad["down"]) - float(pad["up"])
	).normalized()
	hero.position.x = clampf(hero.position.x + axis.x * MOVE_SPEED * delta, -8.0, 8.0)
	hero.position.z = clampf(hero.position.z + axis.y * MOVE_SPEED * delta, -4.4, 6.4)
	_sync_camera()
	nearest = ""
	var nearest_distance: float = 2.1
	for key in inspect_locations:
		var distance: float = hero.position.distance_to(inspect_locations[key])
		if distance < nearest_distance:
			nearest_distance = distance
			nearest = key
	if interact_button != null:
		interact_button.visible = nearest != "" and nearest not in state.inspected

func _inspect_nearest() -> void:
	if phase != "EXPLORATION" or nearest == "":
		return
	if not state.mark_inspected(nearest):
		return
	if not state.write_save():
		push_warning(t("save_error"))
	var descriptions := {
		"CAMERA": "camera",
		"GALA_PROGRAM": "gala",
		"FAMILY_PHOTO": "family"
	}
	phase = "INSPECTED"
	var panel := _modal(t("inspect"), t(descriptions[nearest]))
	if state.inspected.size() >= 2:
		_button(t("resume"), panel, _show_choice)
	else:
		_button(t("resume"), panel, _enter_world)

func _show_choice() -> void:
	phase = "CHOICE"
	var panel := _modal(t("choose_header"), t("chapter"))
	_button(t("choice_a"), panel, func() -> void: _commit_choice("PHOTO_AUDIENCE"))
	_button(t("choice_b"), panel, func() -> void: _commit_choice("LISTEN_AUDIENCE"))

func _commit_choice(value: String) -> void:
	if not state.choose(value) or not state.complete():
		return
	if not state.write_save():
		push_warning(t("save_error"))
	_show_end()

func _show_end() -> void:
	phase = "CH01_COMPLETED"
	var response := t("choice_result_a") if state.choice == "PHOTO_AUDIENCE" else t("choice_result_b")
	var panel := _modal(t("checkpoint"), response + "\n\n" + t("prototype_end"))
	_button(t("gallery"), panel, _show_gallery)
	_button(t("restart"), panel, _show_menu)

func _take_photo() -> void:
	if phase != "EXPLORATION" or shot_in_progress:
		return
	shot_in_progress = true
	await RenderingServer.frame_post_draw
	var picture: Image = get_viewport().get_texture().get_image()
	shot_count += 1
	var path: String = "user://photos/shot_%s_%s.png" % [str(Time.get_unix_time_from_system()), str(shot_count)]
	var directory: String = ProjectSettings.globalize_path("user://photos")
	DirAccess.make_dir_recursive_absolute(directory)
	var error: Error = picture.save_png(path)
	if error == OK:
		state.shots.append(path)
		if not state.write_save():
			push_warning(t("save_error"))
		if status_label != null:
			status_label.text = t("snapshot")
	else:
		if status_label != null:
			status_label.text = t("snapshot_error")
	shot_in_progress = false

func _show_gallery() -> void:
	var previous: String = phase
	phase = "GALLERY"
	var panel := _modal(t("gallery"), t("no_photos") if state.shots.is_empty() else "%s: %s" % [t("photo"), str(state.shots.size())])
	if not state.shots.is_empty():
		var image_path: String = state.shots.back()
		if FileAccess.file_exists(image_path):
			var png := Image.new()
			if png.load(image_path) == OK:
				var picture := TextureRect.new()
				picture.texture = ImageTexture.create_from_image(png)
				picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
				picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
				picture.custom_minimum_size = Vector2(320, 190)
				panel.add_child(picture)
	_button(t("close"), panel, func() -> void:
		if previous == "EXPLORATION":
			_enter_world()
		elif previous == "CH01_COMPLETED":
			_show_end()
		else:
			_show_menu()
	)
