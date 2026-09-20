import unreal as u,json
from pathlib import Path
out={}
a=u.EditorAssetLibrary
s=u.get_editor_subsystem(u.EditorActorSubsystem)
l=u.get_editor_subsystem(u.LevelEditorSubsystem)
def vec(v):return [v.x,v.y,v.z]
for name,path in [('target','/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox1'),('reference','/Game/Asylum/Maps/Showcase')]:
 l.load_level(path)
 rows=[]
 for x in s.get_all_level_actors():
  r={'label':x.get_actor_label(),'class':x.get_class().get_name(),'pos':vec(x.get_actor_location()),'rot':str(x.get_actor_rotation()),'scale':vec(x.get_actor_scale3d()),'folder':str(x.get_folder_path())}
  if isinstance(x,u.StaticMeshActor):
   c=x.static_mesh_component;m=c.static_mesh
   if m:r.update(mesh=m.get_path_name(),materials=[str(c.get_material(i).get_path_name()) if c.get_material(i) else '' for i in range(c.get_num_materials())])
  rows.append(r)
 out[name]=rows
Path('/tmp/asylum_inspect.json').write_text(json.dumps(out,indent=2))
meshes=[]
for p in a.list_assets('/Game/Asylum/Meshes',True,False):
 m=a.load_asset(p)
 if isinstance(m,u.StaticMesh):
  b=m.get_bounding_box();meshes.append({'path':p,'min':vec(b.min),'max':vec(b.max),'mats':[str(z.material_interface.get_path_name()) if z.material_interface else '' for z in m.static_materials]})
Path('/tmp/asylum_meshes.json').write_text(json.dumps(meshes,indent=2))
u.log('ASYLUM_INSPECT_DONE')
