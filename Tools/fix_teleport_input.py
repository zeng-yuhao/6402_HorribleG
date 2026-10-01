import traceback

import unreal

LOG_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\teleport_fix.txt"
lines = []


def log(msg):
    text = str(msg)
    lines.append(text)
    unreal.log(text)


def flush():
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def describe_key(key):
    if key is None:
        return "None"
    info = [f"type={type(key).__name__}", f"str={key}"]
    for name in ("key_name", "KeyName", "display_name"):
        try:
            info.append(f"{name}={key.get_editor_property(name)}")
        except Exception:
            pass
    for attr in ("key_name", "to_string", "get_display_name", "export_text"):
        if hasattr(key, attr):
            try:
                value = getattr(key, attr)
                info.append(f"attr_{attr}={value() if callable(value) else value}")
            except Exception as exc:
                info.append(f"attr_{attr} ERR {exc}")
    info.append(f"dir={[name for name in dir(key) if not name.startswith('_')][:40]}")
    return " | ".join(info)


def make_key(name):
    attempts = []
    try:
        key = unreal.Key()
        key.set_editor_property("key_name", name)
        attempts.append(("set key_name", key, describe_key(key)))
        if "Q" in describe_key(key) or name in describe_key(key) or "LeftControl" in describe_key(key):
            return key
    except Exception as exc:
        attempts.append(("set key_name", None, str(exc)))
    try:
        key = unreal.Key()
        key.set_editor_property("KeyName", unreal.Name(name))
        attempts.append(("KeyName Name", key, describe_key(key)))
        return key
    except Exception as exc:
        attempts.append(("KeyName Name", None, str(exc)))
    try:
        lib = unreal.InputLibrary
        if hasattr(lib, "key_from_string"):
            key = lib.key_from_string(name)
            attempts.append(("InputLibrary.key_from_string", key, describe_key(key)))
            return key
    except Exception as exc:
        attempts.append(("InputLibrary", None, str(exc)))
    try:
        key = unreal.EnhancedInputLibrary  # noqa: F841
    except Exception:
        pass
    log(f"make_key({name}) attempts={attempts}")
    return None


def mapping_action_name(mapping):
    action = mapping.get_editor_property("action")
    return action.get_name() if action else ""


def rebuild_mappings(imc, ia_teleport):
    mappings = list(imc.get_editor_property("mappings"))
    log("---- current mappings ----")
    for index, mapping in enumerate(mappings):
        log(f"{index} {mapping_action_name(mapping)} {describe_key(mapping.get_editor_property('key'))}")

    key_q = make_key("Q")
    key_ctrl = make_key("LeftControl")
    log(f"key_q={describe_key(key_q)}")
    log(f"key_ctrl={describe_key(key_ctrl)}")

    new_mappings = []
    replaced = False
    for mapping in mappings:
        if mapping_action_name(mapping) == "IA_Teleport":
            if key_q:
                mapping.set_editor_property("key", key_q)
                replaced = True
            new_mappings.append(mapping)
        else:
            new_mappings.append(mapping)

    if key_ctrl:
        extra = unreal.EnhancedActionKeyMapping()
        extra.set_editor_property("action", ia_teleport)
        extra.set_editor_property("key", key_ctrl)
        new_mappings.append(extra)

    imc.set_editor_property("mappings", new_mappings)
    unreal.EditorAssetLibrary.save_asset("/Game/Input/IMC_Default")
    log(f"replaced_teleport_key={replaced} mapping_count={len(new_mappings)}")

    mappings = list(imc.get_editor_property("mappings"))
    log("---- after mappings ----")
    for index, mapping in enumerate(mappings):
        log(f"{index} {mapping_action_name(mapping)} {describe_key(mapping.get_editor_property('key'))}")


def enable_default_can_teleport():
    path = "/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter"
    blueprint = unreal.EditorAssetLibrary.load_asset(path)
    char_cls = unreal.EditorAssetLibrary.load_blueprint_class(path)
    cdo = unreal.get_default_object(char_cls)
    log(f"CanTeleport before={cdo.get_editor_property('CanTeleport')}")
    cdo.set_editor_property("CanTeleport", True)
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    except Exception as exc:
        log(f"compile err={exc}")
    unreal.EditorAssetLibrary.save_asset(path)
    cdo = unreal.get_default_object(unreal.EditorAssetLibrary.load_blueprint_class(path))
    log(f"CanTeleport after={cdo.get_editor_property('CanTeleport')}")


def run():
    log("FIX START")
    imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Default")
    ia = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_Teleport")
    rebuild_mappings(imc, ia)
    enable_default_can_teleport()
    log("FIX DONE")


try:
    run()
except Exception:
    log(traceback.format_exc())
finally:
    flush()
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
