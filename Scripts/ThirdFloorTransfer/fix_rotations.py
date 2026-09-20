import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem)
report=[]
for a in A.get_all_level_actors():
 f=str(a.get_folder_path());r=a.get_actor_rotation()
 if f in ['TF_Architecture/Mouldings','TF_Architecture/WallTiles']:
  a.set_actor_rotation(u.Rotator(pitch=0,yaw=r.pitch if abs(r.pitch)>1 else 0,roll=0),False)
  # Euler decomposition can represent 180 pitch as yaw180/roll180: rebuild from actual position and nearest wall normal below.
  p=a.get_actor_location();rows=json.loads((D/'architecture_report.json').read_text())['walls']
  # Mouldings pivot sits 18.6cm behind the facing wall, find nearest solid boundary around its centroid.
  candidates=[]
  for x0,y0,x1,y1,z0,z1 in rows:
   if z0!=0:continue
   if y0-1<=p.y<=y1+1:
    candidates.extend([(abs((x0+18.6)-p.x),0),(abs((x1-18.6)-p.x),180)])
   if x0-1<=p.x<=x1+1:
    candidates.extend([(abs((y0+18.6)-p.y),90),(abs((y1-18.6)-p.y),-90)])
  if candidates:
   _,yaw=min(candidates);a.set_actor_rotation(u.Rotator(pitch=0,yaw=yaw,roll=0),False)
  report.append(a.get_actor_label())
# Reset named review camera transforms with explicit Euler keywords.
views={'Overview':((0,0,2550),(-90,-90,0)),'Surgery':((-815,-100,175),(-6,-22,0)),'Ward08':((1446,435,170),(-6,-118,0)),'Archive':((-1342,355,165),(-4,-35,0)),'Bathroom':((-635,328,165),(-8,-5,0)),'Hall09':((10,460,175),(-3,-85,0))}
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_View_'):
  pos,r=views[a.get_actor_label()[8:]];a.set_actor_location(u.Vector(*pos),False,False);a.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1],roll=r[2]),False)
# Correct all imported props from their recorded intended source rotations.
plans=[]
for name in['props_plan.json','props_plan_89.json']:
 p=json.loads((D/name).read_text());plans.extend(p['entries'] if isinstance(p,dict) else p)
for a in A.get_all_level_actors():
 if str(a.get_folder_path()).startswith('TF_Rooms/'):
  i=int(a.get_actor_label().split('_')[2]);e=plans[i];t=e['t'];r=t['r'];a.set_actor_location(u.Vector(*t['p']),False,False);a.set_actor_rotation(u.Rotator(pitch=r[0],yaw=r[1],roll=r[2]),False)
# Limit shadowed point lights to one per room; broad fill lights remain shadow-free.
seen=set()
for a in A.get_all_level_actors():
 if isinstance(a,u.PointLight):
  c=a.point_light_component
  if a.get_actor_label().startswith('Practical_'):c.set_cast_shadows(False);c.set_intensity(180)
  elif a.get_actor_label().startswith('TF_R'):
   rn=a.get_actor_label().split('_')[1];c.set_cast_shadows(rn not in seen);seen.add(rn);c.set_attenuation_radius(420)
assert u.get_editor_subsystem(u.LevelEditorSubsystem).save_current_level()
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,2550),u.Rotator(pitch=-90,yaw=-90,roll=0))
(D/'rotation_fix.json').write_text(json.dumps({'architectural_components':len(report),'props':len(plans),'shadowed_rooms':list(seen)}))
