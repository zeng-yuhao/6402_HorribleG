import unreal as u,json,math,collections
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name()=='L_Horror_Floorplan_codex'
plans=[]
for f in ['props_plan.json','props_plan_89.json']:
 p=json.loads((D/f).read_text());plans+=p['entries'] if isinstance(p,dict) else p
# Idempotent replacement of only this pass's props, all original source assets remain unchanged.
for a in list(A.get_all_level_actors()):
 if str(a.get_folder_path()).startswith(('TF_Rooms/','TF_TransferredDecals/','TF_Lighting/')):A.destroy_actor(a)
cache={};created=[];lights=[]
def asset(path):
 if path not in cache:cache[path]=u.load_asset(path)
 return cache[path]
for i,e in enumerate(plans):
 t=e['t'];b=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*t['p']),u.Rotator(pitch=t['r'][0],yaw=t['r'][1],roll=t['r'][2]));name=e['mesh'].split('.')[-1]
 b.set_actor_label('TF_R%02d_%04d_%s'%(e['room'],i,name));b.set_folder_path('TF_Rooms/%02d/%s'%(e['room'],'Lighting' if name.startswith('SM_Lamp') else 'Details'))
 c=b.static_mesh_component;m=asset(e['mesh']);assert m,e['mesh'];c.set_static_mesh(m);b.set_actor_scale3d(u.Vector(*t['s']))
 for k,mp in enumerate(e['mats']):
  if mp:c.set_material(k,asset(mp))
 collision=e.get('collision',True) and any(k in name for k in ['Desk','Sofa','LeatherChair','Locker','Bed01','AutopsyTable','MedicalTable','OperatingTable','Sink','Toilet','Basin','Chair01','Chair02','WoodenPartition'])
 c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if collision else u.CollisionEnabled.NO_COLLISION)
 if collision:c.set_collision_profile_name('BlockAll')
 b.set_editor_property('tags',[u.Name('ThirdFloorSource'),u.Name('Source_'+e['source']['actor']),u.Name('Room_%02d'%e['room'])])
 # Source luminous ceiling fixtures receive compact movable practical light sources.
 if name in['SM_Lamp01_1','SM_Lamp03_1'] and t['p'][2]>280:
  q=A.spawn_actor_from_class(u.PointLight,u.Vector(t['p'][0],t['p'][1],min(335,t['p'][2]-55)));q.set_actor_label('TF_R%02d_Practical_%04d'%(e['room'],i));q.set_folder_path('TF_Lighting/RoomPracticals')
  lc=q.point_light_component;lc.set_mobility(u.ComponentMobility.MOVABLE);lc.set_intensity(260 if name=='SM_Lamp03_1' else 340);lc.set_attenuation_radius(500);lc.set_light_color(u.LinearColor(.91,.85,.67,1));lights.append(q)
 o,x=b.get_actor_bounds(False)
 created.append({'label':b.get_actor_label(),'room':e['room'],'source':e['source'],'mesh':e['mesh'],'t':t,'bounds':[[o.x-x.x,o.y-x.y,o.z-x.z],[o.x+x.x,o.y+x.y,o.z+x.z]],'collision':collision})
# Recreate the source decals, preserving material and shape; tightly restrict floor projection depth.
source={a['name']:a for a in json.loads((D/'source.json').read_text())};decaldata={a['name']:a for a in json.loads((D/'source_decals.json').read_text())};decalout=[]
for f in ['decals_plan.json','decals_plan89.json']:
 if not(D/f).exists():continue
 ds=json.loads((D/f).read_text());ds=ds['entries'] if isinstance(ds,dict) else ds
 for i,e in enumerate(ds):
  src=e['source'];key=src['actor'] if isinstance(src,dict) else src
  meta=decaldata[key];t=e['t'];q=A.spawn_actor_from_class(u.DecalActor,u.Vector(*t['p']),u.Rotator(pitch=t['r'][0],yaw=t['r'][1],roll=t['r'][2]));q.set_actor_label('TF_Decal_R%02d_%s'%(e['room'],key));q.set_folder_path('TF_TransferredDecals/%02d'%e['room']);q.set_actor_scale3d(u.Vector(*t['s']));c=q.decal;c.set_decal_material(asset(meta['material']))
  size=meta['decal_size'];c.set_editor_property('decal_size',u.Vector(min(size[0],16/max(abs(t['s'][0]),.001)),size[1],size[2]));c.set_editor_property('sort_order',1 if 'Blood' in meta['material'] else 0);c.set_editor_property('fade_screen_size',.001)
  decalout.append({'label':q.get_actor_label(),'source':key,'material':meta['material']})
# Remove stale blockout postprocess volume so our consistent exposure controls the scene.
for a in list(A.get_all_level_actors()):
 if isinstance(a,u.PostProcessVolume) and a.get_actor_label()!='TF_Interior_Exposure':A.destroy_actor(a)
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True)
seen_shadow_rooms=set()
for a in A.get_all_level_actors():
 if isinstance(a,u.PointLight):
  c=a.point_light_component
  if a.get_actor_label().startswith('Practical_'):c.set_cast_shadows(False);c.set_intensity(180)
  elif a.get_actor_label().startswith('TF_R'):
   rn=a.get_actor_label().split('_')[1];c.set_cast_shadows(rn not in seen_shadow_rooms);seen_shadow_rooms.add(rn);c.set_attenuation_radius(420)
for a in A.get_all_level_actors():
 if a.get_actor_label()=='TF_View_Bathroom':
  a.set_actor_location(u.Vector(-635,420,165),False,False);a.set_actor_rotation(u.Rotator(pitch=-8,yaw=22,roll=0),False)
A.set_selected_level_actors([]);assert L.save_current_level()
(D/'transfer_report.json').write_text(json.dumps({'count':len(created),'rooms':dict(collections.Counter(e['room'] for e in created)),'practical_lights':len(lights),'decals':decalout,'created':created,'all_prop_scales_preserved':True},indent=2))
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,3000),u.Rotator(pitch=-90,yaw=-90,roll=0))
u.log('THIRDFLOOR_PROPS_IMPORTED '+str(len(created)))
