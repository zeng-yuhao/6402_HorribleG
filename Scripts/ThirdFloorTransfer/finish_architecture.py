import unreal as u,json,math
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name()=='L_Horror_Floorplan_codex'
actors=list(A.get_all_level_actors());cube=u.load_asset('/Engine/BasicShapes/Cube');source=json.loads((D/'source.json').read_text());report={'wall_tiles':0,'damaged_floor_modules':0}
# Reintroduce the exact layered bathroom/archives tile shader on original wall modules.
for rn in [5,6]:
 skins=[a for a in actors if a.get_actor_label().startswith('TF_WallFace_%02d_'%rn)]
 for a in skins:
  p=a.get_actor_location();sc=a.get_actor_scale3d()
  if p.z<200:
   vertical=sc.x<sc.y;low=(p.y-sc.y*50) if vertical else(p.x-sc.x*50);high=(p.y+sc.y*50) if vertical else(p.x+sc.x*50)
   # Determine direction towards the receiving room from known region center.
   center=(-1209,194) if rn==5 else(-367,372)
   n=(1 if center[0]>p.x else -1,0) if vertical else(0,1 if center[1]>p.y else -1)
   yaw={(1,0):180,(-1,0):0,(0,1):-90,(0,-1):90}[n]
   count=max(1,round((high-low)/200));length=(high-low)/count
   for i in range(count):
    mid=low+(i+.5)*length
    loc=u.Vector((p.x if vertical else mid)-n[0]*19.6,(mid if vertical else p.y)-n[1]*19.6,0)
    b=A.spawn_actor_from_class(u.StaticMeshActor,loc,u.Rotator(pitch=0,yaw=yaw,roll=0));b.set_actor_label('TF_R%02d_TiledWall_%03d'%(rn,report['wall_tiles']));b.set_folder_path('TF_Architecture/WallTiles')
    c=b.static_mesh_component;c.set_static_mesh(u.load_asset('/Game/Asylum/Meshes/Building/Walls/SM_Wall02'));c.set_material(0,u.load_asset('/Game/Asylum/Materials/Building/'+('MI_WallTile02_3' if rn==5 else 'MI_WallTile01_4')));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    b.set_actor_scale3d(u.Vector(1,length/200,.9985));report['wall_tiles']+=1
  A.destroy_actor(a)
# Original broken floor geometry, surrounded by non-overlapping world-mapped infill.
rooms=json.loads((D/'rooms.json').read_text());floorinfo=json.loads((D/'architecture_report.json').read_text())['floor']
mods={1:[(-1600,-424,'SM_Floor01_3'),(-1170,-424,'SM_Floor01_1')],3:[(565,-194,'SM_Floor03_2')],6:[(-367,372,'SM_Floor03_3')],7:[(565,245,'SM_Floor03_4')],8:[(1230,245,'SM_Floor01_4')]}
for rn,modules in mods.items():
 rect=rooms[str(rn)];rs=[rect]
 for x,y,name in modules:
  cut=[x-200,y-200,x+200,y+200];out=[]
  for x0,y0,x1,y1 in rs:
   ix0=max(x0,cut[0]);ix1=min(x1,cut[2]);iy0=max(y0,cut[1]);iy1=min(y1,cut[3])
   if ix0>=ix1 or iy0>=iy1:out.append([x0,y0,x1,y1]);continue
   for r in [[x0,y0,ix0,y1],[ix1,y0,x1,y1],[ix0,y0,ix1,iy0],[ix0,iy1,ix1,y1]]:
    if r[2]-r[0]>.01 and r[3]-r[1]>.01:out.append(r)
  rs=out
  original=next(c for a in source for c in a['components'] if c['mesh'].endswith('/'+name+'.'+name))
  b=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(x,y,-.05));b.set_actor_label('TF_OriginalFloor_R%02d_%02d'%(rn,report['damaged_floor_modules']));b.set_folder_path('TF_Architecture/OriginalDamagedFloors');c=b.static_mesh_component;c.set_static_mesh(u.load_asset(original['mesh']));c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
  for mi,mp in enumerate(original['mats']):
   if mp:c.set_material(mi,u.load_asset(mp))
  report['damaged_floor_modules']+=1
 for a in actors:
  if a.get_actor_label().startswith('TF_Floor_R%02d_'%rn):A.destroy_actor(a)
 material=u.load_asset(next(x['material'] for x in floorinfo if x['room']==rn))
 # Continuous collision base sits below broken surface, so exposed concrete never coincides with it.
 for i,(x0,y0,x1,y1) in enumerate([rect]+rs):
  base=i==0;z=-8 if base else 0
  b=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector((x0+x1)/2,(y0+y1)/2,(-20+z)/2));b.set_actor_label('TF_Floor_R%02d_Infill_%02d'%(rn,i));b.set_folder_path('TF_Architecture/Floors');c=b.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,u.load_asset('/Game/HorrorWhitebox/ThirdFloor/Materials/MI_FloorConcrete01_World') if base else material);b.set_actor_scale3d(u.Vector((x1-x0)/100,(y1-y0)/100,(20+z)/100));c.set_collision_profile_name('BlockAll')
# Four centimetres of separation between floor modules and underlying subfloor avoids coplanar surfaces.
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True)
assert L.save_current_level();(D/'architecture_finish_report.json').write_text(json.dumps(report,indent=2))
