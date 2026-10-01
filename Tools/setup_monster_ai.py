import json
import os
import sys
import traceback

import unreal

PROJECT_PYTHON = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Content\Python"
if PROJECT_PYTHON not in sys.path:
    sys.path.insert(0, PROJECT_PYTHON)

from monster_ai.director import Monster_Director, Monster_Controller

LOG_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\monster_setup_log.txt"
LAYOUT_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\asylum_base_layout.json"
ASSET_DIR = "/Game/AI/Monster"
BASE2 = unreal.Vector(-151.4, -236.2, -3640.2)
F1_WALK_Z = 730.0
F2_WALK_Z = 1136.0

LINES = []


def log(msg):
    text = str(msg)
    LINES.append(text)
    unreal.log(text)


def flush_log():
    folder = os.path.dirname(LOG_PATH)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with open(LOG_PATH, "w", encoding="utf-8") as handle:
        handle.write("\n".join(LINES))


def to_base2(x, y, z):
    return unreal.Vector(x + BASE2.x, y + BASE2.y, z + BASE2.z)


def compile_blueprint(blueprint):
    try:
        unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)
    except Exception as exc:
        log(f"compile_blueprint failed: {exc}")


def ensure_folder(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_or_load_asset(name, directory, asset_class, factory):
    asset_path = f"{directory}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    return tools.create_asset(name, directory, asset_class, factory)


def create_blackboard():
    factory = unreal.BlackboardDataFactory()
    blackboard = create_or_load_asset("Monster_Blackboard", ASSET_DIR, unreal.BlackboardData, factory)
    log(f"blackboard={blackboard}")
    return blackboard


def create_behavior_tree(blackboard):
    factory = unreal.BehaviorTreeFactory()
    tree = create_or_load_asset("Monster_BT", ASSET_DIR, unreal.BehaviorTree, factory)
    if tree and blackboard:
        log("behavior tree and blackboard created as placeholder assets")
    log(f"behavior_tree={tree}")
    return tree


def add_blueprint_component(blueprint, component_class, name):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    parent = None
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        if unreal.SubobjectDataBlueprintFunctionLibrary.is_root_component(data):
            parent = handle
            break
    if parent is None and handles:
        parent = handles[0]
    params = unreal.AddNewSubobjectParams()
    params.parent_handle = parent
    params.new_class = component_class
    params.blueprint_context = blueprint
    new_handle, _reason = subsystem.add_new_subobject(params)
    try:
        subsystem.rename_new_subobject(new_handle, unreal.Text(name))
    except Exception:
        try:
            subsystem.rename_subobject(new_handle, unreal.Text(name))
        except Exception as exc:
            log(f"rename {name} failed: {exc}")
    return new_handle


def set_mesh_on_character_bp(blueprint):
    mesh = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
    anim = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data, False)
        if not obj:
            continue
        class_name = obj.get_class().get_name()
        if class_name == "SkeletalMeshComponent":
            try:
                obj.set_editor_property("skeletal_mesh_asset", mesh)
            except Exception:
                try:
                    obj.set_editor_property("skeletal_mesh", mesh)
                except Exception as exc:
                    log(f"set mesh failed: {exc}")
            if anim:
                try:
                    obj.set_editor_property("anim_class", anim)
                except Exception as exc:
                    log(f"set anim failed: {exc}")
            try:
                obj.set_relative_location(unreal.Vector(0.0, 0.0, -90.0), False, False)
                obj.set_relative_rotation(unreal.Rotator(0.0, -90.0, 0.0), False, False)
            except Exception:
                pass
        if class_name == "BoxComponent" and "Contact" in str(obj.get_name()):
            try:
                obj.set_box_extent(unreal.Vector(70.0, 70.0, 96.0), True)
            except Exception:
                pass
            try:
                obj.set_relative_location(unreal.Vector(40.0, 0.0, 0.0), False, False)
            except Exception:
                pass
            try:
                obj.set_collision_profile_name("Trigger")
            except Exception:
                pass
            try:
                obj.set_editor_property("generate_overlap_events", True)
            except Exception:
                pass


def create_character_blueprint():
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Character)
    blueprint = create_or_load_asset("Monster_Character", ASSET_DIR, unreal.Blueprint, factory)
    if not blueprint:
        raise RuntimeError("failed to create Monster_Character")
    try:
        add_blueprint_component(blueprint, unreal.BoxComponent, "ContactCollision")
    except Exception as exc:
        log(f"add ContactCollision failed: {exc}")
    try:
        add_blueprint_component(blueprint, unreal.AIPerceptionComponent, "AIPerception")
    except Exception as exc:
        log(f"add AIPerception failed: {exc}")
    compile_blueprint(blueprint)
    set_mesh_on_character_bp(blueprint)
    compile_blueprint(blueprint)
    generated = unreal.EditorAssetLibrary.load_blueprint_class(f"{ASSET_DIR}/Monster_Character")
    if generated:
        cdo = unreal.get_default_object(generated)
        try:
            cdo.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.PLACED_IN_WORLD_OR_SPAWNED)
        except Exception as exc:
            log(f"set auto_possess_ai failed: {exc}")
        try:
            capsule = cdo.get_component_by_class(unreal.CapsuleComponent)
            if capsule:
                capsule.set_capsule_size(42.0, 96.0)
        except Exception as exc:
            log(f"set capsule failed: {exc}")
    unreal.EditorAssetLibrary.save_asset(f"{ASSET_DIR}/Monster_Character")
    log(f"character_bp={blueprint}")
    return generated


def create_director_blueprint():
    log("skip python-parent director blueprint; PIE bootstrap starts Monster_Director")
    return None


def cleanup_our_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for actor in list(subsystem.get_all_level_actors()):
        label = actor.get_actor_label()
        if label.startswith("MonsterAI_") or label in ("Monster_Character", "BP_MonsterDirector", "Monster_Director"):
            actor.destroy_actor()
            removed += 1
    log(f"removed_old_actors={removed}")


def spawn_labeled(actor_class, location, label, tags=None, rotation=None):
    rotator = rotation or unreal.Rotator()
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotator)
    actor.set_actor_label(label, True)
    if tags:
        actor.tags = tags
    return actor


def spawn_volume(volume_class, location, label, extent):
    actor = spawn_labeled(volume_class, location, label)
    actor.set_actor_scale3d(unreal.Vector(extent.x / 100.0, extent.y / 100.0, extent.z / 100.0))
    if volume_class == unreal.NavModifierVolume:
        try:
            actor.set_editor_property("area_class", unreal.NavArea_Null.static_class())
        except Exception as exc:
            log(f"set area_class failed: {exc}")
    return actor


def load_layout():
    with open(LAYOUT_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def place_patrol_points():
    points = [
        ("MonsterAI_Patrol_F1_Entrance", 0.0, 412.4, F1_WALK_Z),
        ("MonsterAI_Patrol_F1_Main01", -442.9, 412.4, F1_WALK_Z),
        ("MonsterAI_Patrol_F1_Main03", 1070.6, -1364.8, F1_WALK_Z),
        ("MonsterAI_Patrol_F1_Main02", 964.8, 2281.9, F1_WALK_Z),
        ("MonsterAI_Patrol_F2_Main02", 662.6, 439.1, F2_WALK_Z),
        ("MonsterAI_Patrol_F2_Main03", 806.3, 2318.5, F2_WALK_Z),
        ("MonsterAI_Patrol_F2_Hall", 94.9, 270.4, F2_WALK_Z),
    ]
    spawned = []
    for label, x, y, z in points:
        actor = spawn_labeled(unreal.TargetPoint, to_base2(x, y, z), label, ["MonsterPatrol"])
        spawned.append(actor)
    log(f"patrol_points={len(spawned)}")
    return spawned


def place_door_blockers(layout):
    count = 0
    for item in layout["actors"]:
        label = item["label"]
        z = item["z"]
        if not label.startswith("BP_Doors"):
            continue
        on_f1 = 600.0 <= z < 800.0
        on_f2 = 1000.0 <= z < 1200.0
        if not (on_f1 or on_f2):
            continue
        location = to_base2(item["x"], item["y"], item["z"])
        extent = unreal.Vector(max(item["ex"], 40.0) + 20.0, max(item["ey"], 40.0) + 20.0, max(item["ez"], 90.0) + 10.0)
        spawn_volume(unreal.NavModifierVolume, location, f"MonsterAI_DoorBlock_{label}", extent)
        count += 1
    log(f"door_blockers={count}")


def place_nav_bounds():
    min_local = unreal.Vector(-800.0, -2300.0, 520.0)
    max_local = unreal.Vector(2000.0, 3400.0, 1260.0)
    center_local = (min_local + max_local) * 0.5
    extent = (max_local - min_local) * 0.5
    location = to_base2(center_local.x, center_local.y, center_local.z)
    spawn_volume(unreal.NavMeshBoundsVolume, location, "MonsterAI_NavBounds_Base2_F1F2", extent)
    log(f"nav_bounds center={location} extent={extent}")


def place_monster(character_class, patrol_points):
    start = patrol_points[0].get_actor_location() if patrol_points else to_base2(0.0, 412.4, F1_WALK_Z)
    actor = spawn_labeled(character_class, start, "Monster_Character", ["Monster_Character"])
    log(f"monster={actor} at {start}")
    return actor


def place_director(director_class):
    location = to_base2(0.0, 412.4, F1_WALK_Z + 80.0)
    actor = spawn_labeled(director_class, location, "BP_MonsterDirector")
    log(f"director={actor}")
    return actor


def rebuild_navigation():
    world = unreal.EditorLevelLibrary.get_editor_world()
    try:
        navsys = unreal.NavigationSystemV1.get_navigation_system(world)
        if navsys:
            navsys.build()
            log("navsys.build() ok")
    except Exception as exc:
        log(f"navsys.build failed: {exc}")
    unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
    log("RebuildNavigation command sent")


def run():
    log("SETUP START")
    ensure_folder("/Game/AI")
    ensure_folder(ASSET_DIR)
    blackboard = create_blackboard()
    create_behavior_tree(blackboard)
    character_class = create_character_blueprint()
    create_director_blueprint()
    if not character_class:
        raise RuntimeError("Monster_Character class missing")

    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Asylum/Maps/Showcase")
    cleanup_our_actors()
    layout = load_layout()
    place_nav_bounds()
    place_door_blockers(layout)
    patrol_points = place_patrol_points()
    spawn_labeled(
        unreal.TargetPoint,
        patrol_points[0].get_actor_location() if patrol_points else to_base2(0.0, 412.4, F1_WALK_Z),
        "MonsterAI_Spawn",
        ["MonsterAI_Spawn"],
    )
    rebuild_navigation()
    world = unreal.EditorLevelLibrary.get_editor_world()
    saved_map = unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Asylum/Maps/Showcase")
    saved_dirty = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    saved_dir = unreal.EditorAssetLibrary.save_directory("/Game/AI")
    log(f"saved_map={saved_map} saved_dirty={saved_dirty} saved_dir={saved_dir} character_class={character_class}")
    log("SETUP DONE")


try:
    run()
except Exception:
    log(traceback.format_exc())
finally:
    flush_log()
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
