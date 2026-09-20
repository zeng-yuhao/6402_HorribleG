"""Room1 material finish pass. Run inside UE 5.6; source Asylum assets stay intact."""
import unreal as u, json, math
from pathlib import Path
ROOT='/Game/HorrorWhitebox/Materials/Room1Finish'
MAP='/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox'
PROJECT=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6')
E=u.EditorAssetLibrary; M=u.MaterialEditingLibrary; A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
assert world.get_name()=='L_Horror_Floorplan_Whitebox'
actors=list(A.get_all_level_actors())
report={'map':MAP,'source_wall':'MI_Wall02_3','source_floor':'MI_FloorConcrete01','before_actor_count':len(actors),'assigned':[],'created':[]}
masterpath=ROOT+'/M_Room1_WorldScaled'
assert not E.does_asset_exist(masterpath), 'Finish pass already exists; inspect rather than overwrite'
master=E.duplicate_asset('/Game/Asylum/Materials/BaseMaterials/M_ProceduralDirtShader_1_1',masterpath)
assert master
expr={e.get_name():e for e in u.ObjectIterator(u.MaterialExpression) if e.get_outer()==master}
def node(cls,x,y,**props):
 n=M.create_material_expression(master,cls,x,y)
 for p,v in props.items():n.set_editor_property(p,v)
 return n
def connect(a,out,b,pin):
 assert M.connect_material_expressions(a,out,b,pin),(a.get_name(),b.get_name(),pin)
def custom_input(name):
 c=u.CustomInput();c.set_editor_property('input_name',name);return c
def scalar(name,val,x,y):return node(u.MaterialExpressionScalarParameter,x,y,parameter_name=name,default_value=val,group='Texture Mapping')
wp=node(u.MaterialExpressionWorldPosition,-2400,-2000)
vn=node(u.MaterialExpressionVertexNormalWS,-2400,-1800)
size=scalar('Texture_Size_cm',300,-2400,-1600)
scale=node(u.MaterialExpressionVectorParameter,-2400,-1400,parameter_name='Tiling_Offset',default_value=u.LinearColor(1,1,0,0),group='Texture Mapping')
angle=expr['MaterialExpressionScalarParameter_4'];angle.set_editor_property('group','Texture Mapping')
maskrg=node(u.MaterialExpressionComponentMask,-2120,-1400,r=True,g=True,b=False,a=False)
maskba=node(u.MaterialExpressionAppendVector,-2120,-1200)
connect(scale,'',maskrg,'');connect(scale,'B',maskba,'A');connect(scale,'A',maskba,'B')
basis='''float3 N=normalize(GeomNormal); float3 U,V;
if(abs(N.z)>0.707){U=float3(1,0,0);V=float3(0,sign(N.z),0);}
else if(abs(N.x)>abs(N.y)){U=float3(0,-sign(N.x),0);V=float3(0,0,-1);}
else {U=float3(sign(N.y),0,0);V=float3(0,0,-1);}
'''
uv=node(u.MaterialExpressionCustom,-1700,-1850,description='World scale UVs - centimetres, shared across adjacent walls',output_type=u.CustomMaterialOutputType.CMOT_FLOAT2,
 inputs=[custom_input(n) for n in ['WorldPos','GeomNormal','SizeCm','Tiling','Offset','Angle']],
 code=basis+'''float2 q=float2(dot(WorldPos,U),dot(WorldPos,V))/max(SizeCm,1.0);
q*=max(Tiling,float2(0.001,0.001));
float a=Angle*6.28318530718; float c=cos(a),s=sin(a);
return float2(c*q.x-s*q.y,s*q.x+c*q.y)+Offset;''')
for n,o,key in [(wp,'','WorldPos'),(vn,'','GeomNormal'),(size,'','SizeCm'),(maskrg,'','Tiling'),(maskba,'','Offset'),(angle,'','Angle')]:connect(n,o,uv,key)
for e in expr.values():
 if isinstance(e,u.MaterialExpressionTextureSampleParameter2D) and str(e.get_editor_property('parameter_name')) in ['Diffuse1','Normal','SRM']:
  connect(uv,'',e,'UVs')
for key in ['MaterialExpressionMultiply_26','MaterialExpressionMultiply_33']:connect(uv,'',expr[key],'A')
# Preserve source normal strength/green-channel switch, then orient into world projection basis.
oldnormal=M.get_material_property_input_node(master,u.MaterialProperty.MP_NORMAL)
assert oldnormal
normal=node(u.MaterialExpressionCustom,3600,1800,description='Projected normal orientation, including UV rotation',output_type=u.CustomMaterialOutputType.CMOT_FLOAT3,
 inputs=[custom_input(n) for n in ['TexNormal','GeomNormal','Angle','Strength']],
 code=basis+'''float a=Angle*6.28318530718;float c=cos(a),s=sin(a);
float2 xy=float2(c*TexNormal.x+s*TexNormal.y,-s*TexNormal.x+c*TexNormal.y)*Strength;
return normalize(U*xy.x+V*xy.y+N*max(TexNormal.z,0.05));''')
strength=scalar('Normal_Strength',.55,3200,2000)
connect(oldnormal,'',normal,'TexNormal');connect(vn,'',normal,'GeomNormal');connect(angle,'',normal,'Angle');connect(strength,'',normal,'Strength')
assert M.connect_material_property(normal,'',u.MaterialProperty.MP_NORMAL)
master.set_editor_property('tangent_space_normal',False)
# Prevent overly glossy plaster/concrete while retaining the source roughness texture chain.
oldrough=M.get_material_property_input_node(master,u.MaterialProperty.MP_ROUGHNESS)
floorrough=scalar('Minimum_Roughness',.7,3700,700)
maxrough=node(u.MaterialExpressionMax,3980,400)
connect(oldrough,'',maxrough,'A');connect(floorrough,'',maxrough,'B')
M.connect_material_property(maxrough,'',u.MaterialProperty.MP_ROUGHNESS)
M.recompile_material(master);E.save_loaded_asset(master)
report['created'].append(masterpath)
def instance(name,source,cm,rough,tint=None,normal_strength=.55):
 p=ROOT+'/'+name
 m=E.duplicate_asset(source,p);assert m
 M.set_material_instance_parent(m,master)
 M.set_material_instance_vector_parameter_value(m,'Tiling_Offset',u.LinearColor(1,1,0,0))
 M.set_material_instance_scalar_parameter_value(m,'Rotation_Angle',0)
 M.set_material_instance_scalar_parameter_value(m,'Texture_Size_cm',cm)
 M.set_material_instance_scalar_parameter_value(m,'Minimum_Roughness',rough)
 M.set_material_instance_scalar_parameter_value(m,'Normal_Strength',normal_strength)
 if tint:M.set_material_instance_vector_parameter_value(m,'diffuse color',u.LinearColor(*tint))
 M.update_material_instance(m);E.save_loaded_asset(m);report['created'].append(p)
 return m
wall=instance('MI_Room1_Plaster','/Game/Asylum/Materials/Building/MI_Wall02_3',300,.78)
floor=instance('MI_Room1_Floor','/Game/Asylum/Materials/Building/MI_FloorConcrete01',250,.7,normal_strength=.65)
ceiling=instance('MI_Room1_Ceiling','/Game/Asylum/Materials/Building/MI_Wall02_3',400,.9,(.55,.54,.51,0),.3)
trim=instance('MI_Room1_Skirting','/Game/Asylum/Materials/Building/MI_Wall02_3',180,.82,(.13,.115,.09,0),.35)
threshold=instance('MI_Room1_Threshold','/Game/Asylum/Materials/Building/MI_FloorConcrete01',250,.76,(.22,.215,.2,0),.35)
cube=E.load_asset('/Engine/BasicShapes/Cube')
trim_count=0
for a in actors:
 label=a.get_actor_label();folder=str(a.get_folder_path()); mat=None
 if folder=='01_Walls' or label in ['SM_WallDoor01','SM_Wall01']:mat=wall
 elif label.startswith('Floor_'):mat=floor
 elif label.startswith('Ceiling_'):mat=ceiling
 elif label.endswith('_Threshold'):mat=threshold
 if mat:
  for c in a.get_components_by_class(u.StaticMeshComponent):
   for i in range(c.get_num_materials()):c.set_material(i,mat)
  report['assigned'].append({'actor':label,'material':mat.get_path_name()})
 if label.startswith('Room_') and label.endswith('_Number'):
  a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
 # Thin baseboards follow existing wall segments; skip lintels and doorway openings.
 if folder=='01_Walls' and 'Lintel' not in label and a.get_components_by_class(u.StaticMeshComponent):
  c=a.get_components_by_class(u.StaticMeshComponent)[0]
  if c.static_mesh!=cube:continue
  p=a.get_actor_location();s=a.get_actor_scale3d();dx=abs(s.x)*100;dy=abs(s.y)*100
  if abs(a.get_actor_rotation().yaw)>0.01:continue
  for side in [-1,1]:
   if dx>dy: loc=u.Vector(p.x,p.y+side*(dy/2+1.0),6);sc=u.Vector(max(dx-2,1)/100,.024,.12)
   else:loc=u.Vector(p.x+side*(dx/2+1.0),p.y,6);sc=u.Vector(.024,max(dy-2,1)/100,.12)
   b=A.spawn_actor_from_class(u.StaticMeshActor,loc)
   b.set_actor_label('Finish_Skirting_'+label+('_A' if side<0 else '_B'));b.set_folder_path('08_Room1_Finish/Skirting')
   b.static_mesh_component.set_static_mesh(cube);b.static_mesh_component.set_material(0,trim)
   b.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
   b.set_actor_scale3d(sc);trim_count+=1
report['skirting_count']=trim_count
report['after_actor_count']=len(A.get_all_level_actors())
# Keep all original layout, collision and lights, plus room1's user-placed modular meshes.
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(-1650,-400,165),u.Rotator(-9,5,0))
assert L.save_current_level()
E.save_directory(ROOT)
report['saved']=True
(PROJECT/'Scripts/room1_texture_report.json').write_text(json.dumps(report,indent=2))
u.log('ROOM1_FINISH_SUCCESS '+json.dumps({'assigned':len(report['assigned']),'trim':trim_count}))
