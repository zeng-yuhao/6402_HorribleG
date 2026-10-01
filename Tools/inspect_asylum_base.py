import json
import unreal

out_path = r"C:\Users\Coco\Documents\Unreal Projects\我的项目3\Saved\asylum_base_layout.json"
unreal.EditorLoadingAndSavingUtils.load_map("/Game/LI_Asylum_Base")
sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = sub.get_all_level_actors()

wanted = (
    "FirtsFloor", "FirstFloor", "SecondFloor", "ThirdFloor",
    "Attic", "OutDoor", "BP_Doors", "Stairs", "Main"
)
rows = []
for actor in actors:
    label = actor.get_actor_label()
    if not any(key in label for key in wanted):
        continue
    loc = actor.get_actor_location()
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "x": round(loc.x, 1),
        "y": round(loc.y, 1),
        "z": round(loc.z, 1),
        "ox": round(origin.x, 1),
        "oy": round(origin.y, 1),
        "oz": round(origin.z, 1),
        "ex": round(extent.x, 1),
        "ey": round(extent.y, 1),
        "ez": round(extent.z, 1),
    })

rows.sort(key=lambda item: (item["z"], item["label"]))
with open(out_path, "w", encoding="utf-8") as handle:
    json.dump({"count": len(rows), "actors": rows}, handle, ensure_ascii=False, indent=2)
unreal.log(f"WROTE {out_path} count={len(rows)}")
unreal.SystemLibrary.execute_console_command(None, "QUIT_EDITOR")
