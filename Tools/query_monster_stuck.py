import sys
import time

sys.path.insert(0, r"C:\Program Files\Epic Games\UE_5.6\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

COMMAND = r'''
import unreal
from monster_ai.controller import MonsterController

out_path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3 5.6\Saved\monster_stuck.txt"
rows = []

def add(text):
    rows.append(str(text))

worlds = []
try:
    for world in unreal.EditorLevelLibrary.get_pie_worlds(False):
        worlds.append(world)
except Exception as exc:
    add("pie_error=%s" % exc)
add("pie_worlds=%s" % len(worlds))
world = worlds[0] if worlds else None
if world is None:
    try:
        world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    except Exception as exc:
        add("game_world_error=%s" % exc)
add("world=%s" % (world.get_path_name() if world else None))

if world:
    monsters = unreal.GameplayStatics.get_all_actors_with_tag(world, "Monster_Character")
    add("monsters=%s" % len(monsters))
    for monster in monsters:
        loc = monster.get_actor_location()
        vel = monster.get_velocity()
        add("monster loc=(%.1f, %.1f, %.1f) vel=%.1f hidden=%s collision=%s" % (
            loc.x, loc.y, loc.z, vel.size(), monster.is_hidden(), monster.get_actor_enable_collision()
        ))
        movement = monster.get_component_by_class(unreal.CharacterMovementComponent)
        if movement:
            try:
                add("movement_mode=%s speed=%.1f" % (movement.movement_mode, movement.max_walk_speed))
            except Exception as exc:
                add("movement_error=%s" % exc)
        controller = monster.get_controller()
        add("controller=%s" % (controller.get_class().get_name() if controller else None))
        if controller:
            try:
                add("move_status=%s" % controller.get_move_status())
            except Exception as exc:
                add("move_status_error=%s" % exc)
            for name in ("b_has_target", "b_is_chasing", "patrol_index", "lost_timer"):
                try:
                    add("%s=%s" % (name, controller.get_editor_property(name)))
                except Exception:
                    pass
            path = controller.get_path_following_component()
            if path:
                try:
                    add("path_status=%s" % path.get_status())
                except Exception as exc:
                    add("path_error=%s" % exc)
        nav = unreal.NavigationSystemV1.get_navigation_system(world)
        add("nav=%s" % (nav.get_name() if nav else None))
        if nav:
            try:
                projected = nav.project_point_to_navigation(monster.get_actor_location(), None, None, unreal.Vector(200, 200, 400))
                add("project=%s" % projected)
            except Exception as exc:
                add("project_error=%s" % exc)
    points = unreal.GameplayStatics.get_all_actors_with_tag(world, "MonsterPatrol")
    add("patrol_points=%s" % len(points))
    for point in points:
        loc = point.get_actor_location()
        add("  %s z=%.1f" % (point.get_actor_label(), loc.z))

if world:
    for monster in unreal.GameplayStatics.get_all_actors_with_tag(world, "Monster_Character"):
        controller = monster.get_controller()
        if not isinstance(controller, MonsterController):
            monster.set_editor_property("ai_controller_class", MonsterController.static_class())
            monster.spawn_default_controller()
            controller = monster.get_controller()
        add("possessed=%s" % (controller.get_class().get_name() if controller else None))
        if controller:
            try:
                add("move_status_after=%s" % controller.get_move_status())
            except Exception as exc:
                add("move_after_error=%s" % exc)

with open(out_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(rows))
unreal.log("STUCK DUMP DONE")
'''

remote = remote_execution.RemoteExecution()
remote.start()
try:
    deadline = time.time() + 12
    nodes = []
    while time.time() < deadline:
        nodes = remote.remote_nodes
        if nodes:
            break
        time.sleep(0.4)
    if not nodes:
        raise SystemExit("no editor node")
    print("PROJECT", nodes[0].get("project_root"))
    remote.open_command_connection(nodes[0]["node_id"])
    result = remote.run_command(COMMAND, exec_mode=remote_execution.MODE_EXEC_FILE)
    print("SUCCESS", result.get("success"))
    for item in result.get("output") or []:
        text = item.get("output") or ""
        if "Error" in item.get("type", "") or "STUCK" in text or "Traceback" in text:
            print(item.get("type"), text[:2000])
finally:
    remote.stop()
