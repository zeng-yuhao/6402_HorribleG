import unreal

out = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\teleport_input.txt"
lines = []


def log(msg):
    lines.append(str(msg))
    unreal.log(str(msg))


imc = unreal.EditorAssetLibrary.load_asset("/Game/Input/IMC_Default")
log(f"IMC={imc}")
try:
    mappings = imc.get_editor_property("mappings")
except Exception as exc:
    mappings = None
    log(f"mappings err={exc}")

if mappings is not None:
    log(f"mapping_count={len(mappings)}")
    for index, mapping in enumerate(mappings):
        action = None
        key = None
        try:
            action = mapping.get_editor_property("action")
        except Exception:
            pass
        try:
            key = mapping.get_editor_property("key")
        except Exception:
            pass
        log(f"MAP {index} action={action} key={key}")

char_cls = unreal.EditorAssetLibrary.load_blueprint_class("/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter")
cdo = unreal.get_default_object(char_cls)
for name in (
    "CanTeleport",
    "IsTeleporting",
    "IsTeleportCooldown",
    "TeleportHeight",
    "TeleportCooldownTime",
):
    try:
        log(f"CHAR {name}={cdo.get_editor_property(name)}")
    except Exception as exc:
        log(f"CHAR {name} ERR {exc}")

ia = unreal.EditorAssetLibrary.load_asset("/Game/Input/IA_Teleport")
log(f"IA_Teleport={ia}")
try:
    log(f"IA value_type={ia.get_editor_property('value_type')}")
except Exception as exc:
    log(f"IA props err={exc}")

with open(out, "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines))
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
