extends SceneTree
## CH01 interactive scene contract (headless GDScript, not touch-device acceptance).
const State = preload("res://scripts/narrative_state.gd")
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
    var saved_path: String = ProjectSettings.globalize_path("user://moty.save.json")
    DirAccess.remove_absolute(saved_path)
    for locale in ["pl", "en"]:
        var game = load("res://scenes/main.tscn").instantiate()
        root.add_child(game)
        await process_frame
        await process_frame
        _check(game.phase == "TITLE", "Main menu loads " + locale)
        game.state.language = locale
        game._new_game()
        _check(game.phase == "PROLOGUE", "Opens prologue " + locale)
        game._show_curtain()
        _check(game.phase == "ACT", "Act title " + locale)
        game._show_chapter_card()
        _check(game.phase == "CHAPTER_CARD", "Chapter card " + locale)
        game._enter_world()
        _check(game.phase == "EXPLORATION", "Playable gala " + locale)
        _check(game.state.mark_inspected("CAMERA"), "Can inspect first object " + locale)
        _check(game.state.mark_inspected("FAMILY_PHOTO"), "Can inspect second object " + locale)
        game._show_choice()
        _check(game.phase == "CHOICE", "Shows a real choice " + locale)
        var option: String = "PHOTO_AUDIENCE" if locale == "pl" else "LISTEN_AUDIENCE"
        game._commit_choice(option)
        _check(game.phase == "CH01_COMPLETED", "Chapter checkpoint " + locale)
        _check(game.state.chapter_completed, "Chapter completion set " + locale)
        _check(game.state.choice == option, "Exact branching flag persists " + locale)
        var saved = State.read_save()
        _check(saved != null and saved.language == locale and saved.choice == option,
               "Atomic save/load retains locale and decision " + locale)
        game._show_menu()
        _check(game.phase == "TITLE", "Menu recovers after chapter " + locale)
        game._continue_game()
        _check(game.phase == "CH01_COMPLETED", "Continue save returns to checkpoint " + locale)
        game.queue_free()
        await process_frame
    # Corrupted save is rejected, not loaded as an impossible narrative path.
    var f := FileAccess.open("user://moty.save.json", FileAccess.WRITE)
    f.store_string("{\"schema\": 999, \"chapter\":70}")
    f.close()
    _check(State.read_save() == null, "Reject corrupt or forged 70th chapter state")
    DirAccess.remove_absolute(saved_path)
    print("CH01 INTERACTIVE E2E FAILURES: ", fails)
    quit(0 if fails == 0 else 1)
