import os
import traceback

import unreal

LOG_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\monster_rotate.log"
LINES = []


def log(msg):
    text = str(msg)
    LINES.append(text)
    unreal.log(text)


def flush_log():
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(LINES))


def turn_mesh(component, label):
    rotation = component.get_editor_property("relative_rotation")
    log(
        f"{label} before pitch={rotation.pitch:.1f} yaw={rotation.yaw:.1f} roll={rotation.roll:.1f}"
    )
    # Positional Rotator args are not pitch/yaw/roll in this editor. Set the axes by name.
    updated = unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0)
    component.set_editor_property("relative_rotation", updated)
    applied = component.get_editor_property("relative_rotation")
    log(
        f"{label} after pitch={applied.pitch:.1f} yaw={applied.yaw:.1f} roll={applied.roll:.1f}"
    )


def rotate_blueprint():
    blueprint = unreal.EditorAssetLibrary.load_asset("/Game/AI/Monster/Monster_Character")
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    changed = 0
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        component = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data, False)
        if component and component.get_class().get_name() == "SkeletalMeshComponent":
            turn_mesh(component, "blueprint")
            changed += 1
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    log(f"blueprint_changed={changed} saved={saved}")


def rotate_placed():
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Asylum/Maps/Showcase")
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    changed = 0
    for actor in subsystem.get_all_level_actors():
        if actor.get_actor_label() != "Monster_Character":
            continue
        mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if not mesh:
            log("placed monster has no mesh")
            continue
        turn_mesh(mesh, "placed")
        changed += 1
    saved = unreal.EditorLevelLibrary.save_current_level()
    log(f"placed_changed={changed} saved_level={saved}")


def run():
    log("ROTATE START")
    rotate_blueprint()
    rotate_placed()
    log("ROTATE DONE")


try:
    run()
except Exception:
    log(traceback.format_exc())
finally:
    flush_log()
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
