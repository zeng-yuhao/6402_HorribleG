import unreal as u,json
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6');D=P/'Scripts/CorridorWidening'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name()=='L_Horror_Floorplan_codex'
assert L.save_current_level()
L.load_level('/Game/FirstPerson/Lvl_FirstPerson')
assert L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex')
def v(p):return [p.x,p.y,p.z]
rows=[]
for a in A.get_all_level_actors():
 r=a.get_actor_rotation();c,e=a.get_actor_bounds(False)
 row={'name':a.get_name(),'label':a.get_actor_label(),'folder':str(a.get_folder_path()),'class':a.get_class().get_name(),'p':v(a.get_actor_location()),'r':[r.pitch,r.yaw,r.roll],'s':v(a.get_actor_scale3d()),'bounds':[v(c-e),v(c+e)],'components':[]}
 for c in a.get_components_by_class(u.StaticMeshComponent):
  if not c.static_mesh:continue
  t=c.get_world_transform();q=t.rotation.rotator()
  row['components'].append({'mesh':c.static_mesh.get_path_name(),'p':v(t.translation),'r':[q.pitch,q.yaw,q.roll],'s':v(t.scale3d),'mats':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],'collision':str(c.get_collision_enabled())})
 rows.append(row)
(D/'after.json').write_text(json.dumps(rows,indent=2))
for a in A.get_all_level_actors():
 if str(a.get_folder_path())=='TF_Architecture/Ceilings':a.set_is_temporarily_hidden_in_editor(True)
L.editor_set_viewport_realtime(True);L.editor_set_game_view(True);L.eject_pilot_level_actor()
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(85,-37,2550),u.Rotator(pitch=-90,yaw=-90,roll=0))
L.editor_invalidate_viewports()
