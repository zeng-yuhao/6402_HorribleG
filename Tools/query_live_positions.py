import json
import sys
import time

sys.path.insert(0, r"C:\Program Files\Epic Games\UE_5.6\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

COMMAND = r'''
import unreal

out_path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3 5.6 - 4\Saved\live_positions.txt"
rows = []
worlds = []
try:
    worlds.append(("editor", unreal.EditorLevelLibrary.get_editor_world()))
except Exception as exc:
    rows.append("editor_world_error=%s" % exc)
try:
    for world in unreal.EditorLevelLibrary.get_pie_worlds(False):
        worlds.append(("pie", world))
except Exception as exc:
    rows.append("pie_error=%s" % exc)

def brief(actor):
    loc = actor.get_actor_location()
    label = ""
    try:
        label = actor.get_actor_label()
    except Exception:
        label = actor.get_name()
    cls = actor.get_class().get_name()
    half = ""
    try:
        capsule = actor.get_component_by_class(unreal.CapsuleComponent)
        if capsule:
            half = " half=%.1f" % float(capsule.get_scaled_capsule_half_height())
    except Exception:
        pass
    return "%s class=%s loc=(%.1f, %.1f, %.1f)%s" % (label, cls, loc.x, loc.y, loc.z, half)

for kind, world in worlds:
    if not world:
        rows.append("WORLD %s missing" % kind)
        continue
    try:
        map_name = world.get_path_name()
    except Exception:
        map_name = world.get_name()
    rows.append("WORLD %s %s" % (kind, map_name))
    try:
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    except Exception as exc:
        rows.append("actors_error=%s" % exc)
        continue
    rows.append("actor_count=%s" % len(actors))
    for actor in actors:
        try:
            label = actor.get_actor_label()
        except Exception:
            label = actor.get_name()
        cls = actor.get_class().get_name()
        text = label + " " + cls
        if any(key in text for key in ("Monster", "Player", "LI_Asylum", "FirstPerson", "Character", "Pawn", "BP_Player")):
            rows.append(brief(actor))

with open(out_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(rows))
unreal.log("WROTE live positions %s" % len(rows))
'''

remote = remote_execution.RemoteExecution()
remote.start()
try:
    deadline = time.time() + 8
    nodes = []
    while time.time() < deadline:
        nodes = remote.remote_nodes
        if nodes:
            break
        time.sleep(0.4)
    print("NODES", json.dumps(nodes, ensure_ascii=False, default=str))
    if not nodes:
        raise SystemExit("no editor node")
    remote.open_command_connection(nodes[0]["node_id"])
    result = remote.run_command(COMMAND, exec_mode=remote_execution.MODE_EXEC_FILE)
    print("SUCCESS", result.get("success"))
    print("RESULT")
    print(result.get("result"))
    print("OUTPUT")
    print(result.get("output"))
finally:
    remote.stop()
