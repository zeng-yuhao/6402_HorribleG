import json
import sys
import time

sys.path.insert(0, r"C:\Program Files\Epic Games\UE_5.6\Engine\Plugins\Experimental\PythonScriptPlugin\Content\Python")
import remote_execution

COMMAND = r'''
import unreal

out_path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3 5.6 - 4\Saved\live_spawn_apply.txt"
rows = []

player_z = None
for world in unreal.EditorLevelLibrary.get_pie_worlds(False):
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        if actor.get_class().get_name() == "BP_FirstPersonCharacter_C":
            player_z = actor.get_actor_location().z
rows.append("player_z=%s" % player_z)

world = unreal.load_object(None, "/Game/Asylum/Maps/Showcase.Showcase")
rows.append("loaded=%s" % (world.get_path_name() if world else None))
actors = []
if world:
    try:
        actors = list(unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor))
    except Exception as exc:
        rows.append("actors_error=%s" % exc)
rows.append("actor_count=%s" % len(actors))

moved = 0
if player_z is not None:
    for actor in actors:
        try:
            label = actor.get_actor_label()
        except Exception:
            continue
        if label == "Monster_Character" or label.startswith("MonsterAI_Patrol_F1"):
            loc = actor.get_actor_location()
            before = loc.z
            loc.z = player_z
            actor.set_actor_location(loc, False, False)
            moved += 1
            rows.append("moved %s %.2f -> %.2f" % (label, before, player_z))
rows.append("moved=%s" % moved)

saved = None
if world and moved:
    try:
        saved = unreal.EditorLoadingAndSavingUtils.save_map(world, "/Game/Asylum/Maps/Showcase")
    except Exception as exc:
        rows.append("save_error=%s" % exc)
rows.append("saved=%s" % saved)

with open(out_path, "w", encoding="utf-8") as handle:
    handle.write("\n".join(rows))
unreal.log("APPLY2 DONE")
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
    if not nodes:
        raise SystemExit("no editor node")
    remote.open_command_connection(nodes[0]["node_id"])
    result = remote.run_command(COMMAND, exec_mode=remote_execution.MODE_EXEC_FILE)
    print("SUCCESS", result.get("success"))
    output = result.get("output") or []
    for item in output:
        print(item.get("type"), item.get("output"))
    if not result.get("success"):
        print(result.get("result"))
finally:
    remote.stop()
