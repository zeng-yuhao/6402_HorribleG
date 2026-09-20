import unreal as u, json
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer')
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
def v(x):return [x.x,x.y,x.z]
def t(x):
 r=x.rotation.rotator()
 return {'p':v(x.translation),'r':[r.pitch,r.yaw,r.roll],'s':v(x.scale3d)}
def dump(path,name):
 assert L.load_level(path)
 rows=[]
 for a in A.get_all_level_actors():
  folder=str(a.get_folder_path())
  if name=='source' and not folder.startswith('03_ThirdFloor'):continue
  b,e=a.get_actor_bounds(False)
  row={'name':a.get_name(),'label':a.get_actor_label(),'class':a.get_class().get_path_name(),'folder':folder,'t':t(a.get_actor_transform()),'bounds':[v(b),v(e)],'hidden':a.is_hidden_ed(),'components':[]}
  for c in a.get_components_by_class(u.StaticMeshComponent):
   m=c.static_mesh
   if not m:continue
   mb=m.get_bounding_box()
   cr={'name':c.get_name(),'mesh':m.get_path_name(),'mats':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],'bounds':[v(mb.min),v(mb.max)],'t':t(c.get_world_transform())}
   if isinstance(c,u.InstancedStaticMeshComponent):
    cr['instances']=[t(c.get_instance_transform(i,True)) for i in range(c.get_instance_count())]
   row['components'].append(cr)
  rows.append(row)
 (P/(name+'.json')).write_text(json.dumps(rows,indent=2))
 u.log('TRANSFER_DUMP_'+name+' '+str(len(rows)))
dump('/Game/Asylum/Maps/Showcase','source')
dump('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex','target')
