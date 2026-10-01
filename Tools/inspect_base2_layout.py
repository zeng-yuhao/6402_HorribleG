import json
import unreal

out_path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\base2_layout.json"

unreal.EditorLoadingAndSavingUtils.load_map("/Game/Asylum/Maps/Showcase")
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)

instances = []
rows = []
for actor in actors:
    label = actor.get_actor_label()
    cls = actor.get_class().get_name()
    loc = actor.get_actor_location()
    origin, extent = actor.get_actor_bounds(False)
    rec = {
        "label": label,
        "class": cls,
        "x": round(loc.x, 1),
        "y": round(loc.y, 1),
        "z": round(loc.z, 1),
        "ox": round(origin.x, 1),
        "oy": round(origin.y, 1),
        "oz": round(origin.z, 1),
        "ex": round(extent.x, 1),
        "ey": round(extent.y, 1),
        "ez": round(extent.z, 1),
    }
    if cls == "LevelInstance":
        instances.append(rec)
    keep = any(key in label for key in (
        "FirtsFloor", "FirstFloor", "SecondFloor", "ThirdFloor",
        "Attic", "OutDoor", "BP_Doors", "Stairs", "LI_Asylum"
    ))
    if keep:
        rows.append(rec)

payload = {"instances": instances, "actors": rows}
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, indent=2)

unreal.log(f"WROTE {out_path} instances={len(instances)} rows={len(rows)}")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
