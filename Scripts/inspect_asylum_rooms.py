import unreal as u,json
from pathlib import Path
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/Asylum/Maps/Showcase')
r=[]
for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
 f=str(a.get_folder_path())
 for c in a.get_components_by_class(u.StaticMeshComponent):
  if c.static_mesh:r.append({'folder':f,'label':a.get_actor_label(),'mesh':c.static_mesh.get_path_name(),'mats':[c.get_material(i).get_path_name() if c.get_material(i) else '' for i in range(c.get_num_materials())]})
Path('/tmp/asylum_rooms.json').write_text(json.dumps(r))
