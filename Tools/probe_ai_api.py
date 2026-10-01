import unreal

path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\probe_ai_api.log"
lines = []


def log(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


try:
    interesting = [
        name for name in dir(unreal)
        if any(token in name.lower() for token in ("black", "bt", "behavi", "nav", "percept", "sense", "decorator", "composite"))
    ]
    log("SYMBOLS")
    log("\n".join(interesting))
    move_class = unreal.load_class(None, "/Script/AIModule.BTTask_MoveTo")
    node = unreal.new_object(move_class)
    log("MOVE DIR")
    log("\n".join(dir(node)))
    for prop in ("AcceptableRadius", "acceptable_radius", "BlackboardKey", "blackboard_key"):
        try:
            value = node.get_editor_property(prop)
            log(f"GET OK {prop}={value}")
        except Exception as exc:
            log(f"GET FAIL {prop}: {exc}")
except Exception as exc:
    log(f"PROBE ERROR {exc}")
finally:
    lines.append("PROBE DONE")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
