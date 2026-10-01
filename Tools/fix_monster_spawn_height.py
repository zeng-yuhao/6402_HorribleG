import os
import traceback

import unreal

LOG_PATH = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\monster_spawn_height.log"
LINES = []
SAMPLE = unreal.Vector(0.0, 412.4, 0.0)


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


def find_labeled(label):
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def contains_xy(origin, extent, x, y, pad=20.0):
    return abs(origin.x - x) <= extent.x + pad and abs(origin.y - y) <= extent.y + pad


def trace_channels(world, z_top, z_bottom):
    start = unreal.Vector(SAMPLE.x, SAMPLE.y, z_top)
    end = unreal.Vector(SAMPLE.x, SAMPLE.y, z_bottom)
    hits = []
    channels = []
    for name in dir(unreal.TraceTypeQuery):
        if name.startswith("TRACE_TYPE_QUERY"):
            channels.append(getattr(unreal.TraceTypeQuery, name))
    object_types = []
    for name in dir(unreal.ObjectTypeQuery):
        if name.startswith("OBJECT_TYPE_QUERY"):
            object_types.append(getattr(unreal.ObjectTypeQuery, name))

    def absorb(tag, result):
        log(f"{tag} type={type(result).__name__}")
        candidates = []
        if isinstance(result, tuple):
            log(f"{tag} tuple={[type(item).__name__ for item in result]}")
            for item in result:
                if isinstance(item, (list, tuple)):
                    candidates.extend(item)
                elif item is not None and not isinstance(item, (bool, int, float, str)):
                    candidates.append(item)
        elif isinstance(result, (list, tuple)):
            candidates.extend(result)
        elif result is not None and not isinstance(result, bool):
            candidates.append(result)
        for hit in candidates:
            try:
                impact = hit.get_editor_property("impact_point")
                normal = hit.get_editor_property("impact_normal")
            except Exception:
                continue
            blocking = True
            try:
                blocking = bool(hit.get_editor_property("b_blocking_hit"))
            except Exception:
                pass
            if not blocking or normal.z < 0.45:
                continue
            name = ""
            try:
                name = hit.get_editor_property("hit_component").get_name()
            except Exception:
                pass
            hits.append((impact.z, name, tag))
            log(f"  hit z={impact.z:.1f} n={normal.z:.2f} {name} via {tag}")

    for channel in channels:
        try:
            result = unreal.SystemLibrary.line_trace_multi(
                world, start, end, channel, True, [], unreal.DrawDebugTrace.NONE, True
            )
            absorb(f"trace {channel}", result)
        except Exception as exc:
            log(f"trace {channel} failed: {exc}")
    try:
        result = unreal.SystemLibrary.line_trace_multi_for_objects(
            world, start, end, object_types, True, [], unreal.DrawDebugTrace.NONE, True
        )
        absorb("objects", result)
    except Exception as exc:
        log(f"object trace failed: {exc}")
    return hits


def component_tops(actor):
    tops = []
    primitives = actor.get_components_by_class(unreal.PrimitiveComponent)
    log(f"  primitives={len(primitives)} class={actor.get_class().get_name()}")
    for comp in primitives:
        collision = ""
        try:
            collision = str(comp.get_collision_enabled())
        except Exception:
            pass
        mesh_name = ""
        thin_top = None
        try:
            mesh = comp.get_editor_property("static_mesh")
            if mesh:
                mesh_name = mesh.get_name()
                box = mesh.get_bounding_box()
                thin_top = (box.min.z, box.max.z)
        except Exception:
            pass
        origin = None
        try:
            bounds = comp.bounds
            origin = bounds.origin
            extent = bounds.box_extent
            if contains_xy(origin, extent, SAMPLE.x, SAMPLE.y):
                top = origin.z + extent.z
                tops.append(top)
                log(
                    f"  comp {comp.get_name()} mesh={mesh_name} collision={collision} "
                    f"top={top:.1f} ez={extent.z:.1f} local_mesh={thin_top}"
                )
        except Exception as exc:
            log(f"  comp {comp.get_name()} bounds failed: {exc}")
        if "Instanced" in comp.get_class().get_name():
            try:
                count = comp.get_instance_count()
            except Exception:
                count = 0
            log(f"  ism {comp.get_name()} count={count} mesh={mesh_name}")
            limit = min(count, 400)
            for index in range(limit):
                try:
                    transform = comp.get_instance_transform(index, True)
                except Exception:
                    continue
                loc = transform.translation
                if abs(loc.x - SAMPLE.x) > 250.0 or abs(loc.y - SAMPLE.y) > 250.0:
                    continue
                scale = transform.scale3d
                top = loc.z
                if thin_top:
                    # Mesh local +Z, assuming the instance is not rolled over.
                    top = loc.z + thin_top[1] * abs(scale.z)
                tops.append(top)
                log(f"    instance {index} loc_z={loc.z:.1f} top={top:.1f}")
    return tops


def mesh_z_extent(mesh, cache):
    name = mesh.get_name()
    if name in cache:
        return cache[name]
    box = mesh.get_bounding_box()
    cache[name] = (box.min.z, box.max.z, name)
    return cache[name]


def measure_floor_z():
    log("LOAD BASE")
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/LI_Asylum_Base")
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    cache = {}
    surfaces = []
    for actor in subsystem.get_all_level_actors():
        try:
            components = actor.get_components_by_class(unreal.PrimitiveComponent)
        except Exception:
            components = []
        for comp in components:
            try:
                mesh = comp.get_editor_property("static_mesh")
            except Exception:
                mesh = None
            if not mesh or "Floor" not in mesh.get_name():
                continue
            min_z, max_z, mesh_name = mesh_z_extent(mesh, cache)
            class_name = comp.get_class().get_name()
            if "Instanced" in class_name:
                try:
                    count = comp.get_instance_count()
                except Exception:
                    count = 0
                for index in range(count):
                    transform = comp.get_instance_transform(index, True)
                    loc = transform.translation
                    if abs(loc.x - SAMPLE.x) > 180.0 or abs(loc.y - SAMPLE.y) > 180.0:
                        continue
                    scale_z = abs(transform.scale3d.z)
                    top = loc.z + max_z * scale_z
                    bottom = loc.z + min_z * scale_z
                    surfaces.append(top)
                    log(
                        f"floor {mesh_name} actor={actor.get_actor_label()} "
                        f"loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) bottom={bottom:.1f} top={top:.1f}"
                    )
            else:
                loc = comp.get_world_location()
                if abs(loc.x - SAMPLE.x) > 180.0 or abs(loc.y - SAMPLE.y) > 180.0:
                    continue
                scale_z = abs(comp.get_world_scale().z)
                top = loc.z + max_z * scale_z
                bottom = loc.z + min_z * scale_z
                surfaces.append(top)
                log(
                    f"floor {mesh_name} actor={actor.get_actor_label()} "
                    f"loc=({loc.x:.1f},{loc.y:.1f},{loc.z:.1f}) bottom={bottom:.1f} top={top:.1f}"
                )
    band = [z for z in surfaces if 500.0 <= z <= 1000.0]
    log(f"surfaces={len(surfaces)} band={sorted(round(z, 1) for z in band)}")
    if not band:
        return None
    return max(band)


def apply_height(floor_z):
    log("LOAD SHOWCASE")
    unreal.EditorLoadingAndSavingUtils.load_map("/Game/Asylum/Maps/Showcase")
    base2 = find_labeled("LI_Asylum_Base2")
    if not base2:
        raise RuntimeError("LI_Asylum_Base2 missing")
    base2_location = base2.get_actor_location()
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    moved = 0
    for actor in subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        if label != "Monster_Character":
            continue
        capsule = actor.get_component_by_class(unreal.CapsuleComponent)
        half = 96.0
        if capsule:
            try:
                half = float(capsule.get_scaled_capsule_half_height())
            except Exception:
                pass
        half += 2.0
        mesh = actor.get_component_by_class(unreal.SkeletalMeshComponent)
        if mesh:
            log(f"mesh_relative={mesh.get_editor_property('relative_location')}")
        location = actor.get_actor_location()
        location.z = base2_location.z + floor_z + half
        actor.set_actor_location(location, False, False)
        moved += 1
        log(f"moved {label} half={half:.1f} world_z={location.z:.1f} local_z={floor_z + half:.1f}")
    saved = unreal.EditorLevelLibrary.save_current_level()
    log(f"moved={moved} saved_level={saved} floor_z={floor_z:.1f}")


def run():
    log("SPAWN HEIGHT START")
    # Measured from SM_Floor02 at the entrance: walk surface local Z = 647.3.
    # Capsule half-height is 96, plus 2 units so the feet clear the slab.
    apply_height(647.3)
    log("SPAWN HEIGHT DONE")


try:
    run()
except Exception:
    log(traceback.format_exc())
finally:
    flush_log()
    unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
