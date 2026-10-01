import json
import os

import unreal

BASE2 = unreal.Vector(-151.4, -236.2, -3640.2)
F1_WALK_Z = 730.0
F2_WALK_Z = 1136.0
LAYOUT_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\asylum_base_layout.json"

PATROL = [
    ("MonsterAI_Patrol_F1_Entrance", 0.0, 412.4, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main01", -442.9, 412.4, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main03", 1070.6, -1364.8, F1_WALK_Z),
    ("MonsterAI_Patrol_F1_Main02", 964.8, 2281.9, F1_WALK_Z),
    ("MonsterAI_Patrol_F2_Main02", 662.6, 439.1, F2_WALK_Z),
    ("MonsterAI_Patrol_F2_Main03", 806.3, 2318.5, F2_WALK_Z),
    ("MonsterAI_Patrol_F2_Hall", 94.9, 270.4, F2_WALK_Z),
]


def to_base2(x, y, z):
    return unreal.Vector(x + BASE2.x, y + BASE2.y, z + BASE2.z)


def _already_placed(world_context):
    return bool(unreal.GameplayStatics.get_all_actors_with_tag(world_context, "MonsterPatrol"))


def _spawn(world_context, actor_class, location, label, tags=None, scale=None):
    transform = unreal.Transform(location, unreal.Rotator(), scale or unreal.Vector(1.0, 1.0, 1.0))
    spawned = unreal.GameplayStatics.begin_deferred_actor_spawn_from_class(
        world_context, actor_class, transform, unreal.SpawnActorCollisionHandlingMethod.ALWAYS_SPAWN
    )
    if not spawned:
        return None
    actor = unreal.GameplayStatics.finish_spawning_actor(spawned, transform)
    actor.set_actor_label(label)
    if tags:
        actor.tags = tags
    if scale:
        actor.set_actor_scale3d(scale)
    return actor


def _spawn_volume(world_context, volume_class, location, label, extent, tags):
    scale = unreal.Vector(max(extent.x, 10.0) / 100.0, max(extent.y, 10.0) / 100.0, max(extent.z, 10.0) / 100.0)
    actor = _spawn(world_context, volume_class, location, label, tags, scale)
    if actor and volume_class == unreal.NavModifierVolume:
        try:
            actor.set_editor_property("area_class", unreal.NavArea_Null.static_class())
        except Exception:
            pass
    return actor


def ensure_runtime_layout(world_context):
    if _already_placed(world_context):
        unreal.log("monster_ai: layout already present")
        return

    min_local = unreal.Vector(-800.0, -2300.0, 520.0)
    max_local = unreal.Vector(2000.0, 3400.0, 1260.0)
    center = (min_local + max_local) * 0.5
    extent = (max_local - min_local) * 0.5
    _spawn_volume(
        world_context,
        unreal.NavMeshBoundsVolume,
        to_base2(center.x, center.y, center.z),
        "MonsterAI_NavBounds_Base2_F1F2",
        extent,
        ["MonsterAI"],
    )

    if os.path.isfile(LAYOUT_PATH):
        with open(LAYOUT_PATH, "r", encoding="utf-8") as handle:
            layout = json.load(handle)
        for item in layout.get("actors", []):
            label = item["label"]
            z = item["z"]
            if not label.startswith("BP_Doors"):
                continue
            if not ((600.0 <= z < 800.0) or (1000.0 <= z < 1200.0)):
                continue
            door_extent = unreal.Vector(
                max(item["ex"], 40.0) + 20.0,
                max(item["ey"], 40.0) + 20.0,
                max(item["ez"], 90.0) + 10.0,
            )
            _spawn_volume(
                world_context,
                unreal.NavModifierVolume,
                to_base2(item["x"], item["y"], item["z"]),
                f"MonsterAI_DoorBlock_{label}",
                door_extent,
                ["MonsterAI"],
            )

    for label, x, y, z in PATROL:
        _spawn(world_context, unreal.TargetPoint, to_base2(x, y, z), label, ["MonsterPatrol", "MonsterAI"])

    first = PATROL[0]
    _spawn(
        world_context,
        unreal.TargetPoint,
        to_base2(first[1], first[2], first[3]),
        "MonsterAI_Spawn",
        ["MonsterAI_Spawn", "MonsterAI"],
    )
    unreal.log("monster_ai: spawned Base2 patrol, door blockers, and nav bounds")
