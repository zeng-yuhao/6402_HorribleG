import unreal as u,json
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6')
M=u.MaterialEditingLibrary;L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox')
before=json.load(open('/tmp/room1_inspection.json'))
current={a.get_actor_label():a for a in A.get_all_level_actors()}
errors=[]
for d in before['actors']:
 a=current.get(d['label'])
 if not a:errors.append('Missing original actor '+d['label']);continue
 if list(a.get_actor_location().to_tuple())!=d['location'] or list(a.get_actor_scale3d().to_tuple())!=d['scale']:errors.append('Transform changed '+d['label'])
for a in current.values():
 f=str(a.get_folder_path());n=a.get_actor_label()
 if f=='01_Walls' or n.startswith(('Floor_','Ceiling_')) or n.endswith('_Threshold') or n in ['SM_WallDoor01','SM_Wall01']:
  for c in a.get_components_by_class(u.StaticMeshComponent):
   for i in range(c.get_num_materials()):
    m=c.get_material(i)
    if not m or '/Room1Finish/' not in m.get_path_name():errors.append('Unfinished surface '+n)

report=json.load(open(P/'Scripts/room1_texture_report.json'))
assert len(current)==report['after_actor_count']
results={'original_actors_preserved':len(before['actors']),'actor_count':len(current),'surfaces_finished':len(report['assigned']),'skirting_segments':report['skirting_count'],'errors':errors,'room_numbers_hidden_in_game':all(current['Room_%02d_Number'%n].get_editor_property('hidden') for n in range(1,9))}
(P/'Scripts/room1_texture_validation.json').write_text(json.dumps(results,indent=2))
assert not errors,errors
u.log('ROOM1_VALIDATION_SUCCESS '+json.dumps(results))
