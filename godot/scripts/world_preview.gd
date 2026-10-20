extends Node3D
## WORLD 1:1 geodetic QA preview. Real public point coordinates only.
## No geospatial buildings, terrain or surveyed facades are embedded.

const REFERENCE_PATH := "res://data/world/reference_points.json"
const TILE_SIZE_M := 256.0
const PREVIEW_STATUS := "2 GEOREFERENCED POINTS — THIS IS NOT A RECREATED CITY"

var view_camera: Camera3D
var center: Vector3 = Vector3(-274.3, 0.0, 101.1)
var camera_height: float = 900.0
var title_label: Label
var distance_label: Label
var scene_valid: bool = false

func _ready() -> void:
	var references: Dictionary = _read_references()
	_setup_world()
	_create_grid()
	_create_ui()
	if references.is_empty():
		distance_label.text = "ERROR: REFERENCE DATA INVALID"
		push_error("World preview requires validated georeferenced data.")
		return
	for point in references["points"]:
		_create_marker(point)
	var p: Array = references["points"]
	var start: Vector3 = _position_from_record(p[0])
	var destination: Vector3 = _position_from_record(p[1])
	var d: float = start.distance_to(destination)
	distance_label.text = "Cieszyn — Český Těšín: %.3f m  |  WGS84 / AEQD" % d
	scene_valid = true
	_refresh_camera()

func _read_references() -> Dictionary:
	if not FileAccess.file_exists(REFERENCE_PATH):
		return {}
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(REFERENCE_PATH))
	if typeof(data) != TYPE_DICTIONARY:
		return {}
	var entry: Dictionary = data
	if entry.get("schema_version", -1) != 1 or entry.get("units", "") != "meters":
		return {}
	if entry.get("grid_size_m", 0) != 256:
		return {}
	if not entry.get("points") is Array or entry["points"].size() != 2:
		return {}
	var ids: Dictionary = {}
	for item in entry["points"]:
		if not item is Dictionary:
			return {}
		if not item.has("east_m") or not item.has("north_m") or not item.has("id"):
			return {}
		var id_text: String = str(item["id"])
		if ids.has(id_text):
			return {}
		ids[id_text] = true
		var east: float = float(item["east_m"])
		var north: float = float(item["north_m"])
		if not is_finite(east) or not is_finite(north):
			return {}
	return entry

func _position_from_record(record: Dictionary) -> Vector3:
	# Right-handed Godot X = east, Z = south. N is -Z.
	return Vector3(float(record["east_m"]), 0.0, -float(record["north_m"]))

func _setup_world() -> void:
	view_camera = Camera3D.new()
	add_child(view_camera)
	view_camera.current = true
	view_camera.fov = 65
	var env: WorldEnvironment = WorldEnvironment.new()
	var e: Environment = Environment.new()
	e.background_mode = Environment.BG_COLOR
	e.background_color = Color(0.055, 0.065, 0.073)
	e.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	e.ambient_light_color = Color(0.77, 0.8, 0.83)
	e.ambient_light_energy = 1.2
	env.environment = e
	add_child(env)
	var light := DirectionalLight3D.new()
	light.rotation_degrees = Vector3(-55, 15, 0)
	light.light_energy = 1.0
	add_child(light)

func _create_grid() -> void:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_color = Color(0.34, 0.37, 0.40)
	var mesh := ImmediateMesh.new()
	mesh.surface_begin(Mesh.PRIMITIVE_LINES, material)
	for i in range(-5, 6):
		var axis: float = float(i) * TILE_SIZE_M
		mesh.surface_add_vertex(Vector3(axis, 0, -1280))
		mesh.surface_add_vertex(Vector3(axis, 0, 1280))
		mesh.surface_add_vertex(Vector3(-1280, 0, axis))
		mesh.surface_add_vertex(Vector3(1280, 0, axis))
	mesh.surface_end()
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	add_child(instance)

func _create_marker(data: Dictionary) -> void:
	var p: Vector3 = _position_from_record(data)
	var model := MeshInstance3D.new()
	var sphere := SphereMesh.new()
	sphere.radius = 7.0
	sphere.height = 14.0
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.86, 0.65, 0.27) if str(data["id"]) == "CIESZYN_TOWN_HALL" else Color(0.42, 0.66, 0.84)
	sphere.material = material
	model.mesh = sphere
	model.position = p + Vector3(0, 10, 0)
	add_child(model)
	var label := Label3D.new()
	label.text = str(data.get("label", data["id"])) + "\n" + str(data["id"])
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	label.font_size = 36
	label.pixel_size = 0.08
	label.modulate = Color(0.96, 0.94, 0.89)
	label.position = p + Vector3(0, 35, 0)
	add_child(label)

func _create_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(root)
	title_label = Label.new()
	title_label.text = PREVIEW_STATUS
	title_label.anchor_right = 1.0
	title_label.offset_top = 12.0
	title_label.offset_bottom = 60.0
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_label.add_theme_font_size_override("font_size", 21)
	root.add_child(title_label)
	distance_label = Label.new()
	distance_label.anchor_right = 1.0
	distance_label.offset_top = 64
	distance_label.offset_bottom = 112
	distance_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	distance_label.add_theme_font_size_override("font_size", 20)
	root.add_child(distance_label)
	var dock := HBoxContainer.new()
	dock.set_anchors_preset(Control.PRESET_BOTTOM_WIDE)
	dock.offset_left = 20
	dock.offset_right = -20
	dock.offset_top = -75
	dock.alignment = BoxContainer.ALIGNMENT_CENTER
	root.add_child(dock)
	_add_button(dock, "− / ODDAL", func() -> void: _zoom(1.25))
	_add_button(dock, "+ / ZBLIŻ", func() -> void: _zoom(0.8))
	_add_button(dock, "POWRÓT / BACK", func() -> void: get_tree().change_scene_to_file("res://scenes/main.tscn"))

func _add_button(parent: Control, label_text: String, handler: Callable) -> void:
	var button := Button.new()
	button.text = label_text
	button.custom_minimum_size = Vector2(190, 55)
	button.pressed.connect(handler)
	parent.add_child(button)

func _zoom(factor: float) -> void:
	camera_height = clampf(camera_height * factor, 100.0, 2600.0)
	_refresh_camera()

func _refresh_camera() -> void:
	if view_camera == null:
		return
	view_camera.position = center + Vector3(0.0, camera_height, camera_height * 0.43)
	view_camera.look_at(center, Vector3.UP)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventScreenDrag:
		_pan(event.relative)
	if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_LEFT):
		_pan(event.relative)

func _pan(delta: Vector2) -> void:
	if not scene_valid:
		return
	var metres_per_pixel: float = camera_height / 750.0
	center.x -= delta.x * metres_per_pixel
	center.z -= delta.y * metres_per_pixel
	_refresh_camera()
