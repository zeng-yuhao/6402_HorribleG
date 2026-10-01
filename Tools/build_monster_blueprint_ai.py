import json
import os
import sys
import traceback

import unreal

PROJECT_PYTHON = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Content\Python"
if PROJECT_PYTHON not in sys.path:
    sys.path.insert(0, PROJECT_PYTHON)

from monster_ai import config
from monster_ai.character import MonsterCharacter
from monster_ai.controller import MonsterController
from monster_ai.tasks import BTTask_GetNextPatrolPoint

LOG_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\monster_ai_build.log"
LAYOUT_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\asylum_base_layout.json"
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


def set_prop(obj, names, value):
    errors = []
    for name in names:
        try:
            obj.set_editor_property(name, value)
            return True
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    log(f"set_prop failed on {obj}: {errors}")
    return False


def ensure_folder(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def load_or_create(name, directory, asset_class, factory):
    asset_path = f"{directory}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    return tools.create_asset(name, directory, asset_class, factory)


def compile_blueprint(blueprint):
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)


def reparent(blueprint, parent_class):
    try:
        unreal.BlueprintEditorLibrary.reparent_blueprint(blueprint, parent_class)
        log(f"reparented {blueprint.get_name()} to {parent_class.get_name()}")
    except Exception as exc:
        log(f"reparent {blueprint.get_name()} failed: {exc}")


def add_component(blueprint, component_class, name):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    handles = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)
    for handle in handles:
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data, False)
        if obj and name in str(obj.get_name()):
            log(f"component exists: {name}")
            return obj
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
    new_handle, reason = subsystem.add_new_subobject(params)
    if not new_handle:
        raise RuntimeError(f"add {name} failed: {reason}")
    try:
        subsystem.rename_subobject(new_handle, unreal.Text(name))
    except Exception as exc:
        log(f"rename {name}: {exc}")
    data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(new_handle)
    return unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data, False)


def component_templates(blueprint):
    subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    found = []
    for handle in subsystem.k2_gather_subobject_data_for_blueprint(blueprint):
        data = unreal.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
        obj = unreal.SubobjectDataBlueprintFunctionLibrary.get_object(data, False)
        if obj:
            found.append(obj)
    return found


def resolve_class(attr_name, script_path):
    existing = getattr(unreal, attr_name, None)
    if existing is not None:
        return existing
    loaded = unreal.load_class(None, script_path)
    if loaded:
        log(f"resolved {attr_name} via {script_path}")
        return loaded
    similar = [name for name in dir(unreal) if attr_name[:8].lower() in name.lower()]
    log(f"MISSING {attr_name} {script_path} similar={similar[:30]}")
    return None


def class_of(wrapper_or_uclass):
    if hasattr(wrapper_or_uclass, "static_class"):
        return wrapper_or_uclass.static_class()
    return wrapper_or_uclass


def enum_value(class_name, member_names):
    enum_cls = getattr(unreal, class_name, None)
    if enum_cls is None:
        log(f"enum missing: {class_name}")
        return None
    for member in member_names:
        if hasattr(enum_cls, member):
            return getattr(enum_cls, member)
    log(f"{class_name} members: {[name for name in dir(enum_cls) if name.isupper()]}")
    return None


def make_affiliation():
    aff = unreal.AISenseAffiliationFilter()
    for name in ("detect_enemies", "detect_neutrals", "detect_friendlies", "b_detect_enemies", "b_detect_neutrals", "b_detect_friendlies"):
        try:
            aff.set_editor_property(name, True)
        except Exception:
            pass
    return aff


def is_composite(node):
    return "Composite" in node.get_class().get_name()


def add_blackboard_key(blackboard, name, key_class, base_class=None):
    key_type = unreal.new_object(key_class, blackboard)
    if base_class is not None:
        set_prop(key_type, ("base_class", "BaseClass"), base_class)
    entry = unreal.BlackboardEntry()
    set_prop(entry, ("entry_name",), unreal.Name(name))
    set_prop(entry, ("key_type",), key_type)
    return entry


def build_blackboard():
    factory = unreal.BlackboardDataFactory()
    blackboard = load_or_create("Monster_Blackboard", config.ASSET_DIR, unreal.BlackboardData, factory)
    actor_class = unreal.Actor.static_class()
    bool_key = resolve_class("BlackboardKeyType_Bool", "/Script/AIModule.BlackboardKeyType_Bool")
    object_key = resolve_class("BlackboardKeyType_Object", "/Script/AIModule.BlackboardKeyType_Object")
    vector_key = resolve_class("BlackboardKeyType_Vector", "/Script/AIModule.BlackboardKeyType_Vector")
    if not all((bool_key, object_key, vector_key)):
        raise RuntimeError("blackboard key classes are not available")
    keys = [
        add_blackboard_key(blackboard, "bHasTarget", bool_key),
        add_blackboard_key(blackboard, "TargetActor", object_key, actor_class),
        add_blackboard_key(blackboard, "LastKnownLocation", vector_key),
        add_blackboard_key(blackboard, "bIsChasing", bool_key),
        add_blackboard_key(blackboard, "PatrolPoint", object_key, actor_class),
    ]
    set_prop(blackboard, ("keys",), keys)
    unreal.EditorAssetLibrary.save_loaded_asset(blackboard)
    log(f"blackboard keys={len(keys)} path={blackboard.get_path_name()}")
    return blackboard


def new_node(node_class, outer):
    return unreal.new_object(node_class, outer)


def key_selector(name, key_type):
    selector = unreal.BlackboardKeySelector()
    set_prop(selector, ("selected_key_name",), unreal.Name(name))
    set_prop(selector, ("selected_key_type",), class_of(key_type))
    return selector


def decorator_op(index):
    op = unreal.BTDecoratorLogic()
    operation = enum_value("BTDecoratorLogicOp", ("TEST", "Test"))
    if operation is None:
        operation = enum_value("BTDecoratorLogicOperation", ("TEST", "Test"))
    if operation is not None:
        set_prop(op, ("operation",), operation)
    set_prop(op, ("number",), index)
    return op


def make_child(node, decorators=None):
    child = unreal.BTCompositeChild()
    if is_composite(node):
        set_prop(child, ("child_composite",), node)
    else:
        set_prop(child, ("child_task",), node)
    if decorators:
        set_prop(child, ("decorators",), decorators)
        set_prop(child, ("decorator_ops",), [decorator_op(index) for index in range(len(decorators))])
    return child


def configure_bool_decorator(decorator, key_name, wants_true):
    bool_key = resolve_class("BlackboardKeyType_Bool", "/Script/AIModule.BlackboardKeyType_Bool")
    set_prop(decorator, ("blackboard_key",), key_selector(key_name, bool_key))
    operation_name = "SET" if wants_true else "NOT_SET"
    operation = enum_value("BasicKeyOperation", (operation_name, operation_name.title()))
    if operation is not None:
        set_prop(decorator, ("basic_operation",), operation)
    abort_mode = enum_value("BTFlowAbortMode", ("BOTH", "Both"))
    if abort_mode is not None:
        set_prop(decorator, ("flow_abort_mode",), abort_mode)
    observer = enum_value("BTBlackboardRestart", ("VALUE_CHANGE", "ValueChange"))
    if observer is not None:
        set_prop(decorator, ("notify_observer",), observer)


def build_behavior_tree(blackboard):
    # UE 5.6 Python does not expose BTCompositeChild, so the Patrol/Chase
    # state machine lives on Monster_Controller. This asset keeps the blackboard link.
    factory = unreal.BehaviorTreeFactory()
    tree = load_or_create("Monster_BT", config.ASSET_DIR, unreal.BehaviorTree, factory)
    set_prop(tree, ("blackboard_asset", "BlackboardAsset"), blackboard)
    unreal.EditorAssetLibrary.save_loaded_asset(tree)
    log(f"behavior tree asset={tree.get_path_name()}")
    return tree


def build_behavior_tree_unused(blackboard):
    factory = unreal.BehaviorTreeFactory()
    tree = load_or_create("Monster_BT", config.ASSET_DIR, unreal.BehaviorTree, factory)
    set_prop(tree, ("blackboard_asset",), blackboard)

    selector_class = resolve_class("BTComposite_Selector", "/Script/AIModule.BTComposite_Selector")
    sequence_class = resolve_class("BTComposite_Sequence", "/Script/AIModule.BTComposite_Sequence")
    move_class = resolve_class("BTTask_MoveTo", "/Script/AIModule.BTTask_MoveTo")
    wait_class = resolve_class("BTTask_Wait", "/Script/AIModule.BTTask_Wait")
    decorator_class = resolve_class("BTDecorator_Blackboard", "/Script/AIModule.BTDecorator_Blackboard")
    object_key = resolve_class("BlackboardKeyType_Object", "/Script/AIModule.BlackboardKeyType_Object")
    bool_key = resolve_class("BlackboardKeyType_Bool", "/Script/AIModule.BlackboardKeyType_Bool")
    if not all((selector_class, sequence_class, move_class, wait_class, decorator_class, object_key, bool_key)):
        raise RuntimeError("behavior tree classes are not available")

    selector = new_node(selector_class, tree)
    chase = new_node(sequence_class, tree)
    patrol = new_node(sequence_class, tree)

    chase_move = new_node(move_class, tree)
    set_prop(chase_move, ("blackboard_key",), key_selector("TargetActor", object_key))
    set_prop(chase_move, ("acceptable_radius",), config.CHASE_ACCEPT_RADIUS)
    set_prop(chase_move, ("b_track_moving_goal", "track_moving_goal"), True)

    patrol_move = new_node(move_class, tree)
    set_prop(patrol_move, ("blackboard_key",), key_selector("PatrolPoint", object_key))
    set_prop(patrol_move, ("acceptable_radius",), config.PATROL_ACCEPT_RADIUS)

    wait = new_node(wait_class, tree)
    set_prop(wait, ("wait_time",), (config.PATROL_WAIT_MIN + config.PATROL_WAIT_MAX) * 0.5)
    set_prop(wait, ("random_deviation",), (config.PATROL_WAIT_MAX - config.PATROL_WAIT_MIN) * 0.5)

    get_next = new_node(BTTask_GetNextPatrolPoint, tree)
    log(f"patrol task class={BTTask_GetNextPatrolPoint.static_class().get_path_name()}")

    chase_dec = new_node(decorator_class, tree)
    configure_bool_decorator(chase_dec, "bHasTarget", True)
    patrol_dec = new_node(decorator_class, tree)
    configure_bool_decorator(patrol_dec, "bHasTarget", False)

    set_prop(chase, ("children",), [make_child(chase_move)])
    set_prop(patrol, ("children",), [make_child(get_next), make_child(patrol_move), make_child(wait)])
    set_prop(selector, ("children",), [make_child(chase, [chase_dec]), make_child(patrol, [patrol_dec])])
    set_prop(tree, ("root_node",), selector)
    unreal.EditorAssetLibrary.save_loaded_asset(tree)
    log(f"behavior tree={tree.get_path_name()} root={selector.get_name()}")
    return tree


def configure_perception(component):
    if not component:
        log("perception component missing")
        return
    sight_class = resolve_class("AISenseConfig_Sight", "/Script/AIModule.AISenseConfig_Sight")
    hearing_class = resolve_class("AISenseConfig_Hearing", "/Script/AIModule.AISenseConfig_Hearing")
    sight_sense = resolve_class("AISense_Sight", "/Script/AIModule.AISense_Sight")
    if not all((sight_class, hearing_class, sight_sense)):
        log("perception sense classes missing")
        return
    sight = unreal.new_object(sight_class, component)
    set_prop(sight, ("sight_radius",), config.SIGHT_RADIUS)
    set_prop(sight, ("lose_sight_radius",), config.SIGHT_LOSE_RADIUS)
    set_prop(sight, ("peripheral_vision_angle_degrees",), config.SIGHT_HALF_ANGLE_DEGREES)
    set_prop(sight, ("detection_by_affiliation",), make_affiliation())
    set_prop(sight, ("auto_success_range_from_last_seen_location",), -1.0)
    hearing = unreal.new_object(hearing_class, component)
    set_prop(hearing, ("hearing_range",), config.HEARING_RADIUS)
    set_prop(hearing, ("detection_by_affiliation",), make_affiliation())
    set_prop(component, ("senses_config",), [sight, hearing])
    set_prop(component, ("dominant_sense",), class_of(sight_sense))


def configure_contact(component):
    if not component:
        log("contact box missing")
        return
    set_prop(component, ("box_extent",), unreal.Vector(70.0, 70.0, 96.0))
    try:
        component.set_relative_location(unreal.Vector(40.0, 0.0, 0.0), False, False)
    except Exception as exc:
        log(f"contact location: {exc}")
    try:
        component.set_collision_profile_name("Trigger")
    except Exception as exc:
        log(f"contact profile: {exc}")
    set_prop(component, ("generate_overlap_events", "b_generate_overlap_events"), True)


def configure_mesh(component):
    if not component:
        return
    mesh = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple")
    anim = unreal.EditorAssetLibrary.load_blueprint_class("/Game/Characters/Mannequins/Anims/Unarmed/ABP_Unarmed")
    if mesh:
        set_prop(component, ("skeletal_mesh_asset", "skeletal_mesh"), mesh)
    if anim:
        set_prop(component, ("anim_class",), anim)
    try:
        component.set_relative_location(unreal.Vector(0.0, 0.0, -90.0), False, False)
        component.set_relative_rotation(unreal.Rotator(0.0, 0.0, 0.0), False, False)
    except Exception as exc:
        log(f"mesh offset: {exc}")


def build_character(controller_class):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Character)
    blueprint = load_or_create("Monster_Character", config.ASSET_DIR, unreal.Blueprint, factory)
    reparent(blueprint, unreal.Character)
    add_component(blueprint, unreal.BoxComponent, "ContactCollision")
    perception_class = resolve_class("AIPerceptionComponent", "/Script/AIModule.AIPerceptionComponent")
    if not perception_class:
        raise RuntimeError("AIPerceptionComponent is not available")
    add_component(blueprint, class_of(perception_class), "AIPerception")
    for component in component_templates(blueprint):
        class_name = component.get_class().get_name()
        if class_name == "SkeletalMeshComponent":
            configure_mesh(component)
        elif class_name == "BoxComponent" and "Contact" in str(component.get_name()):
            configure_contact(component)
        elif class_name == "AIPerceptionComponent":
            set_prop(component, ("senses_config", "SensesConfig"), [])
    compile_blueprint(blueprint)
    generated = unreal.EditorAssetLibrary.load_blueprint_class(config.CHARACTER_PATH)
    cdo = unreal.get_default_object(generated)
    set_prop(cdo, ("auto_possess_ai", "AutoPossessAI"), unreal.AutoPossessAI.DISABLED)
    movement = cdo.get_component_by_class(unreal.CharacterMovementComponent)
    if movement:
        set_prop(movement, ("max_walk_speed",), config.PATROL_WALK_SPEED)
        set_prop(movement, ("b_orient_rotation_to_movement", "orient_rotation_to_movement"), True)
    set_prop(cdo, ("b_use_controller_rotation_yaw", "use_controller_rotation_yaw"), False)
    capsule = cdo.get_component_by_class(unreal.CapsuleComponent)
    if capsule:
        try:
            capsule.set_capsule_size(42.0, 96.0, True)
        except Exception as exc:
            log(f"capsule: {exc}")
    compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    log(f"character={blueprint.get_path_name()} controller={controller_class.get_name()}")
    return generated


def build_controller(tree):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.AIController)
    blueprint = load_or_create("Monster_Controller", config.ASSET_DIR, unreal.Blueprint, factory)
    reparent(blueprint, unreal.AIController)
    compile_blueprint(blueprint)
    generated = unreal.EditorAssetLibrary.load_blueprint_class(config.CONTROLLER_PATH)
    cdo = unreal.get_default_object(generated)
    set_prop(cdo, ("behavior_tree_asset",), tree)
    compile_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    log(f"controller={blueprint.get_path_name()}")
    return generated


def find_labeled(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def to_world(instance, x, y, z):
    local = unreal.Vector(float(x), float(y), float(z))
    try:
        return unreal.MathLibrary.transform_location(instance.get_actor_transform(), local)
    except Exception:
        origin = instance.get_actor_location()
        return unreal.Vector(origin.x + local.x, origin.y + local.y, origin.z + local.z)


def cleanup_our_actors():
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    removed = 0
    for actor in list(subsystem.get_all_level_actors()):
        label = actor.get_actor_label()
        if label.startswith("MonsterAI_") or label in ("Monster_Character", "BP_MonsterDirector", "Monster_Director"):
            actor.destroy_actor()
            removed += 1
    log(f"removed_old_actors={removed}")


def spawn_labeled(actor_class, location, label, tags, rotation=None):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation or unreal.Rotator())
    actor.set_actor_label(label, True)
    if tags:
        actor.tags = tags
    return actor


def spawn_volume(volume_class, location, label, extent, rotation, area_class=None):
    actor = spawn_labeled(volume_class, location, label, ["MonsterAI"], rotation)
    actor.set_actor_scale3d(unreal.Vector(max(extent.x, 10.0) / 100.0, max(extent.y, 10.0) / 100.0, max(extent.z, 10.0) / 100.0))
    if area_class is not None:
        set_prop(actor, ("area_class",), area_class)
    return actor


def place_level_actors(character_class):
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Asylum/Maps/Showcase")
    base2 = find_labeled(config.BASE2_LABEL)
    if not base2:
        raise RuntimeError("LI_Asylum_Base2 was not found in Showcase")
    log(f"Base2 at {base2.get_actor_location()}")
    cleanup_our_actors()

    rotation = base2.get_actor_rotation()
    min_local = unreal.Vector(-800.0, -2300.0, 520.0)
    max_local = unreal.Vector(2000.0, 3400.0, 1260.0)
    center_local = (min_local + max_local) * 0.5
    extent = (max_local - min_local) * 0.5
    spawn_volume(
        unreal.NavMeshBoundsVolume,
        to_world(base2, center_local.x, center_local.y, center_local.z),
        "MonsterAI_NavBounds_Base2_F1F2",
        extent,
        rotation,
    )

    door_count = 0
    with open(LAYOUT_PATH, "r", encoding="utf-8") as handle:
        layout = json.load(handle)
    for item in layout["actors"]:
        label = item["label"]
        z = item["z"]
        if not label.startswith("BP_Doors"):
            continue
        if not (config.DOOR_Z_MIN <= z < config.DOOR_Z_MAX):
            continue
        door_extent = unreal.Vector(max(item["ex"], 50.0) + 40.0, max(item["ey"], 50.0) + 40.0, max(item["ez"], 90.0))
        spawn_volume(
            unreal.NavModifierVolume,
            to_world(base2, item["ox"], item["oy"], item["oz"]),
            f"MonsterAI_DoorBlock_{label}",
            door_extent,
            rotation,
            unreal.NavArea_Null.static_class(),
        )
        door_count += 1
    log(f"door_blockers={door_count}")

    first_location = None
    for label, x, y, z in config.PATROL_POINTS:
        location = to_world(base2, x, y, z)
        spawn_labeled(unreal.TargetPoint, location, label, ["MonsterPatrol", "MonsterAI"])
        if first_location is None:
            first_location = location
    monster = spawn_labeled(character_class, first_location, "Monster_Character", ["Monster_Character", "MonsterAI"])
    log(f"monster={monster.get_actor_label()} at {monster.get_actor_location()}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    try:
        unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
        log("RebuildNavigation command sent")
    except Exception as exc:
        log(f"nav rebuild: {exc}")
    saved = unreal.EditorLevelLibrary.save_current_level()
    log(f"saved_level={saved}")


def run():
    log("BUILD START")
    log(f"task_class={BTTask_GetNextPatrolPoint.static_class().get_path_name()}")
    ensure_folder("/Game/AI")
    ensure_folder(config.ASSET_DIR)
    blackboard = build_blackboard()
    tree = build_behavior_tree(blackboard)
    controller_class = build_controller(tree)
    character_class = build_character(controller_class)
    place_level_actors(character_class)
    log("BUILD DONE")


try:
    run()
except Exception:
    log(traceback.format_exc())
finally:
    flush_log()
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
