import unreal as u,json,math,collections
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex')
p=[]
for f in ['props_plan.json','props_plan_89.json']:
 q=json.loads((D/f).read_text());p.extend(q['entries'] if isinstance(q,dict) else q)
errors=[];count=collections.Counter();keys=set();actual=[]
for a in A.get_all_level_actors():
 label=a.get_actor_label()
 if not str(a.get_folder_path()).startswith('TF_Rooms/'):continue
 i=int(label.split('_')[2]);e=p[i];count[e['room']]+=1
 c=a.static_mesh_component;loc=a.get_actor_location();sc=a.get_actor_scale3d();r=a.get_actor_rotation();q=r.quaternion();er=e['t']['r'];expectedq=u.Rotator(pitch=er[0],yaw=er[1],roll=er[2]).quaternion()
 angle=2*math.acos(min(1,abs(q.x*expectedq.x+q.y*expectedq.y+q.z*expectedq.z+q.w*expectedq.w)))*180/math.pi
 delta=max(abs(x-y) for x,y in zip([loc.x,loc.y,loc.z],e['t']['p']));sd=max(abs(x-y) for x,y in zip([sc.x,sc.y,sc.z],e['t']['s']))
 if delta>.02 or sd>.00001 or angle>.02:errors.append({'label':label,'position_delta':delta,'scale_delta':sd,'rotation_delta_deg':angle})
 if c.static_mesh.get_path_name()!=e['mesh']:errors.append({'label':label,'mesh_mismatch':True})
 mats=[c.get_material(k).get_path_name() if c.get_material(k) else None for k in range(c.get_num_materials())]
 if mats!=e['mats']:errors.append({'label':label,'material_mismatch':True})
 k=(e['mesh'],tuple(round(v,3) for v in e['t']['p']),tuple(round(v,3) for v in e['t']['r']),tuple(round(v,4) for v in e['t']['s']))
 if k in keys:errors.append({'label':label,'duplicate_mesh_transform':True})
 keys.add(k);o,x=a.get_actor_bounds(False);actual.append({'label':label,'room':e['room'],'mesh':e['mesh'],'pos':[loc.x,loc.y,loc.z],'rot':[r.pitch,r.yaw,r.roll],'scale':[sc.x,sc.y,sc.z],'bounds':[[o.x-x.x,o.y-x.y,o.z-x.z],[o.x+x.x,o.y+x.y,o.z+x.z]]})
assert sum(count.values())==len(p),(sum(count.values()),len(p))
assert not errors,errors[:10]
ceilings=[]
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True);ceilings.append(a.get_actor_label())
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,2550),u.Rotator(pitch=-90,yaw=-90,roll=0))
nav=json.loads((D/'navigation_qa_report.json').read_text())
report={'map':'/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex','save_reload_verified':True,'props':len(p),'rooms':dict(count),'transform_material_errors':errors,'duplicate_mesh_transforms':0,'decals':sum(isinstance(a,u.DecalActor) and str(a.get_folder_path()).startswith('TF_TransferredDecals') for a in A.get_all_level_actors()),'ceilings_hidden_for_review':ceilings,'navigation_all_rooms':nav['all_rooms_reachable'],'navigation_all_doors':nav['all_door_areas_reachable'],'method':'Saved map reloaded; all transferred prop transforms, mesh references, material slots and scales compared with finalized source-instance plans; 10cm-grid clearance flood fill for a 70cm-diameter player. Rendered review images inspected separately.'}
(D/'saved_validation.json').write_text(json.dumps(report,indent=2));(D/'saved_actor_bounds.json').write_text(json.dumps(actual,indent=2))
u.log('THIRDFLOOR_FINAL_VERIFIED '+str(len(p)))
