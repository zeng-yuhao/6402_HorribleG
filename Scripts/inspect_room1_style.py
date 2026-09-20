import unreal as u,json
from pathlib import Path
A=u.get_editor_subsystem(u.EditorActorSubsystem)
w=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
r={'world':w.get_path_name(),'actors':[],'materials':{}}
for a in A.get_all_level_actors():
 d={'label':a.get_actor_label(),'class':a.get_class().get_name(),'folder':str(a.get_folder_path()),'location':list(a.get_actor_location().to_tuple()),'rotation':str(a.get_actor_rotation()),'scale':list(a.get_actor_scale3d().to_tuple()),'components':[]}
 for c in a.get_components_by_class(u.StaticMeshComponent):
  ms=[c.get_material(i) for i in range(c.get_num_materials())]
  d['components'].append({'name':c.get_name(),'mesh':c.static_mesh.get_path_name() if c.static_mesh else None,'materials':[m.get_path_name() if m else None for m in ms]})
  for m in ms:
   if not m or m.get_path_name() in r['materials']:continue
   md={'class':m.get_class().get_name()}
   if isinstance(m,u.MaterialInstanceConstant):
    md['parent']=m.get_editor_property('parent').get_path_name()
    for p in ['scalar_parameter_values','vector_parameter_values','texture_parameter_values','static_parameters']:
     try:md[p]=str(m.get_editor_property(p))
     except:pass
   r['materials'][m.get_path_name()]=md
 r['actors'].append(d)
Path('/tmp/room1_inspection.json').write_text(json.dumps(r,indent=2))
u.log('ROOM1_INSPECTION_DONE')
