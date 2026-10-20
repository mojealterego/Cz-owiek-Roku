extends SceneTree

func _initialize() -> void:
	print("DIAGNOSTIC res:// project: ", ProjectSettings.globalize_path("res://project.godot"))
	print("DIAGNOSTIC renderer: ", ProjectSettings.get_setting("rendering/renderer/rendering_method", "MISSING"))
	print("DIAGNOSTIC ETC2 key defined: ", ProjectSettings.has_setting("rendering/textures/vram_compression/import_etc2_astc"))
	print("DIAGNOSTIC ETC2 setting: ", ProjectSettings.get_setting("rendering/textures/vram_compression/import_etc2_astc", "MISSING"))
	quit()
