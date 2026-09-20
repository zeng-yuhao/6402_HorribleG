import unreal as u,json,math,shutil,datetime
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6');D=P/'Scripts/ThirdFloorTransfer'
A=u.get_editor_subsystem(u.EditorActorSubsystem); L=u.get_editor_subsystem(u.LevelEditorSubsystem);E=u.EditorAssetLibrary;M=u.MaterialEditingLibrary
MAP='/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex'; ROOT='/Game/HorrorWhitebox/ThirdFloor'
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name()=='L_Horror_Floorplan_codex'
backup=P/'Saved/Backups/ThirdFloorTransfer'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S');backup.mkdir(parents=True,exist_ok=True)
shutil.copy2(P/'Content/HorrorWhitebox/Maps/L_Horror_Floorplan_codex.umap',backup/'L_Horror_Floorplan_codex.umap')
report={'backup':str(backup),'walls':[],'floor':[],'source_mapping':{1:'Room01',2:'Room04',3:'Room05 upper',4:'Room07',5:'Room02',6:'Room06',7:'Room05 lower',8:'Room08',9:'Room09'},'layout_changes':['Remove Room 2 enclosure','Shift central rooms 3 and 7 100 cm east','Raise shell ceiling to source height 400 cm']}
orig=json.loads((D/'target.json').read_text());cube=u.load_asset('/Engine/BasicShapes/Cube');cache={}
master=u.load_asset('/Game/HorrorWhitebox/Materials/Room1Finish/M_Room1_WorldScaled')
def mat(name,cm=400):
 if name in cache:return cache[name]
 src='/Game/Asylum/Materials/Building/'+name
 dest=ROOT+'/Materials/'+name+'_World'
 q=E.load_asset(dest) if E.does_asset_exist(dest) else E.duplicate_asset(src,dest)
 assert q,src
 # All world instances in this pass derive from the matching one-layer Asylum master.
 if q.parent.get_name()=='M_ProceduralDirtShader_1_1':
  M.set_material_instance_parent(q,master)
  M.set_material_instance_vector_parameter_value(q,'Tiling_Offset',u.LinearColor(1,1,0,0))
  M.set_material_instance_scalar_parameter_value(q,'Texture_Size_cm',cm)
  M.set_material_instance_scalar_parameter_value(q,'Minimum_Roughness',0.0)
  M.set_material_instance_scalar_parameter_value(q,'Normal_Strength',1.0)
  M.update_material_instance(q)
 E.save_loaded_asset(q);cache[name]=q;return q
wallmats={0:mat('MI_Wall02_6'),1:mat('MI_Wall01_2'),2:mat('MI_Wall02_2'),3:mat('MI_Wall02_5'),4:mat('MI_Wall01_1'),5:mat('MI_Wall02_6'),6:mat('MI_Wall02_5'),7:mat('MI_Wall02_5'),8:mat('MI_Wall02_7'),9:mat('MI_Wall02_5')}
floormats={0:mat('MI_Floor02_1'),1:mat('MI_Floor01_1'),2:mat('MI_Floor02_1'),3:mat('MI_Floor03_4'),4:mat('MI_Floor02_1'),5:mat('MI_FloorConcrete01'),6:mat('MI_Floor03_5'),7:mat('MI_Floor03_4'),8:mat('MI_Floor01_1'),9:mat('MI_Floor01_1')}
rooms={1:(-1815,-631,-891,-217),2:(-698,-631,-36,-26),3:(257,-401,893,13),4:(997,-579,1635,-167),5:(-1527,-13,-891,401),6:(-685,165,-49,579),7:(257,39,893,451),8:(997,39,1635,451)}
def roomat(x,y):
 for n,(x1,y1,x2,y2) in rooms.items():
  if x1-.1<=x<=x2+.1 and y1-.1<=y<=y2+.1:return n
 if -23<=x<=971 and -631<=y<=579:return 9
 return 0
created=[]
def box(label,rect,z0,z1,m,folder,collision=True):
 x0,y0,x1,y1=rect
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
 a.set_actor_label(label);a.set_folder_path('TF_Architecture/'+folder);c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,m)
 a.set_actor_scale3d(u.Vector((x1-x0)/100,(y1-y0)/100,(z1-z0)/100));c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if collision else u.CollisionEnabled.NO_COLLISION)
 if collision:c.set_collision_profile_name('BlockAll')
 created.append(a);return a
# Extract current plan and fix deliberately short west wall. Two height layers keep all doorway voids.
rects=[];lintels=[]
for a in orig:
 if a['folder']!='01_Walls' or a['label'].startswith('R2_') or a['label']=='Plan_Circular_Column':continue
 if not a['components'] or not a['components'][0]['mesh'].startswith('/Engine/BasicShapes/Cube'):continue
 x,y,z=a['t']['p'];dx,dy,dz=[v*100 for v in a['t']['s']]
 if a['label'].startswith(('R3_','R7_')):x+=100
 if a['label']=='R8_West':dy=464
 r=[round(x-dx/2,3),round(y-dy/2,3),round(x+dx/2,3),round(y+dy/2,3)]
 (lintels if 'Lintel' in a['label'] else rects).append(r)
# Drop prior finish and plain fixtures after the backed-up target has been inspected.
for a in list(A.get_all_level_actors()):
 label=a.get_actor_label();f=str(a.get_folder_path())
 if f in ['01_Walls','02_Floors','03_Ceilings (hidden in editor)','04_Doorways','05_Room_Numbers'] or f.startswith('08_Room1_Finish') or label.startswith(('SM_Wall','Fixture_')):
  A.destroy_actor(a)
 elif label.startswith('Practical_'):
  a.set_actor_location(u.Vector(a.get_actor_location().x,a.get_actor_location().y,330),False,False)
  c=a.point_light_component;c.set_intensity(430);c.set_attenuation_radius(700);c.set_light_color(u.LinearColor(.75,.83,.77,1))
# Raster CSG at the exact existing edge coordinates, then merge cells into disjoint solid rectangles.
def grid_union(rs):
 xs=sorted(set(v for r in rs for v in [r[0],r[2]]));ys=sorted(set(v for r in rs for v in [r[1],r[3]]))
 g={(i,j) for i in range(len(xs)-1) for j in range(len(ys)-1) if any(r[0]<(xs[i]+xs[i+1])/2<r[2] and r[1]<(ys[j]+ys[j+1])/2<r[3] for r in rs)}
 return xs,ys,g
def merged_cells(xs,ys,g):
 todo=set(g);out=[]
 while todo:
  i,j=min(todo);k=i+1
  while(k,j) in todo:k+=1
  l=j+1
  while all((q,l) in todo for q in range(i,k)):l+=1
  out.append([xs[i],ys[j],xs[k],ys[l]])
  for q in range(i,k):
   for w in range(j,l):todo.remove((q,w))
 return out
layers=[]
for rs,z0,z1 in [(rects,0,220),(rects+lintels,220,400)]:
 xs,ys,g=grid_union(rs);layers.append((xs,ys,g,z0,z1))
 for i,r in enumerate(merged_cells(xs,ys,g)):
  box('TF_WallSolid_%s_%03d'%(z0,i),r,z0,z1,wallmats[0],'Walls');report['walls'].append([*r,z0,z1])
# Visible boundary skins receive room-specific continuous world-scale materials. No coincident visible planes.
segments=[]
for xs,ys,g,z0,z1 in layers:
 edges={}
 for i,j in g:
  for di,dj,n,axis,c,lo,hi in [(-1,0,(-1,0),'V',xs[i],ys[j],ys[j+1]),(1,0,(1,0),'V',xs[i+1],ys[j],ys[j+1]),(0,-1,(0,-1),'H',ys[j],xs[i],xs[i+1]),(0,1,(0,1),'H',ys[j+1],xs[i],xs[i+1])]:
   if(i+di,j+dj) in g:continue
   xx=c if axis=='V' else (lo+hi)/2;yy=(lo+hi)/2 if axis=='V' else c
   rn=roomat(xx+n[0]*2,yy+n[1]*2);key=(axis,c,n,rn)
   edges.setdefault(key,[]).append((lo,hi))
 for (axis,c,n,rn),segs in edges.items():
  joins=[]
  for lo,hi in sorted(segs):
   if joins and abs(joins[-1][1]-lo)<.01:joins[-1][1]=hi
   else:joins.append([lo,hi])
  for lo,hi in joins:
   if axis=='V':r=(c+min(0,n[0]*.6),lo,c+max(0,n[0]*.6),hi)
   else:r=(lo,c+min(0,n[1]*.6),hi,c+max(0,n[1]*.6))
   box('TF_WallFace_%02d_%03d_%d'%(rn,len(segments),z0),r,z0,z1,wallmats[rn],'WallFinishes',False)
   if z0==0:segments.append({'axis':axis,'c':c,'n':n,'room':rn,'lo':lo,'hi':hi})
# Original Asylum moulded wood panels and cornices tiled to each exposed inner wall segment.
for si,s in enumerate(segments):
 axis,c,n,rn,lo,hi=[s[k] for k in ['axis','c','n','room','lo','hi']]
 # Skip exterior facing surface by testing whether the point is within the floor footprint.
 x=c+n[0]*5 if axis=='V' else (lo+hi)/2;y=c+n[1]*5 if axis=='H' else (lo+hi)/2
 inside=((-1841<=x<=997 and -657<=y<=-605) or(-1841<=x<=1839 and -605<=y<=-13) or(-1731<=x<=1839 and -13<=y<=605) or(735<=x<=1839 and 605<=y<=655))
 if not inside:continue
 panel=rn in [0,1,4,8,9];matname='MI_Border03' if rn in[0,8] else ('MI_Border02' if rn==6 else 'MI_Border01')
 l=hi-lo
 if l<35:continue
 count=max(1,round(l/200));length=l/count
 yaw={(1,0):180,(-1,0):0,(0,1):-90,(0,-1):90}[tuple(n)]
 for i in range(count):
  mid=lo+(i+.5)*length
  for kind,z in [('base',1.2),('crown',383.3)]:
   name='SM_Border02_1' if panel and kind=='base' else 'SM_Border02_3'
   mesh=u.load_asset('/Game/Asylum/Meshes/Building/Borders/'+name)
   if not mesh:continue
   pp=u.Vector((c if axis=='V' else mid)-n[0]*18.6,(mid if axis=='V' else c)-n[1]*18.6,z)
   a=A.spawn_actor_from_class(u.StaticMeshActor,pp,u.Rotator(pitch=0,yaw=yaw,roll=0));a.set_actor_label('TF_R%02d_%s_%03d_%02d'%(rn,kind,si,i));a.set_folder_path('TF_Architecture/Mouldings')
   a.static_mesh_component.set_static_mesh(mesh);a.static_mesh_component.set_material(0,u.load_asset('/Game/Asylum/Materials/Building/'+matname));a.static_mesh_component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);a.set_actor_scale3d(u.Vector(1,length/200,1));created.append(a)
# Tile the floor footprint into disjoint rectangles using region boundaries; continuous UVs never stretch.
foot=[(-1841,-657,997,-605),(-1841,-605,1839,-13),(-1731,-13,1839,605),(735,605,1839,655)]
xs=sorted(set(v for r in list(rooms.values())+foot for v in[r[0],r[2]]));ys=sorted(set(v for r in list(rooms.values())+foot for v in[r[1],r[3]]))
groups={}
for i in range(len(xs)-1):
 for j in range(len(ys)-1):
  x=(xs[i]+xs[i+1])/2;y=(ys[j]+ys[j+1])/2
  if not any(r[0]<=x<=r[2] and r[1]<=y<=r[3] for r in foot):continue
  groups.setdefault(roomat(x,y),set()).add((i,j))
for rn,g in groups.items():
 for i,r in enumerate(merged_cells(xs,ys,g)):
  box('TF_Floor_R%02d_%02d'%(rn,i),r,-20,0,floormats[rn],'Floors');report['floor'].append({'room':rn,'rect':r,'z':0,'material':floormats[rn].get_path_name()})
for i,r in enumerate(foot):
 a=box('TF_Ceiling_%02d'%i,r,400,414,mat('MI_Wall02_3'),'Ceilings');a.set_is_temporarily_hidden_in_editor(True)
# Door frames built to the retained 140 cm by 220 cm clear openings; surrounding trims do not encroach.
for a in orig:
 if not a['label'].endswith('_Threshold') or a['label'].startswith('R2_'):continue
 x,y,z=a['t']['p'];dx,dy,_=[v*100 for v in a['t']['s']]
 if a['label'].startswith('R3_'):x+=100
 for side in[-1,1]:
  if dx>dy:r=(x+side*(dx/2+2.5)-2.5,y-15,x+side*(dx/2+2.5)+2.5,y+15)
  else:r=(x-15,y+side*(dy/2+2.5)-2.5,x+15,y+side*(dy/2+2.5)+2.5)
  box('TF_DoorJamb_'+a['label']+str(side),r,0,220,mat('MI_WoodBeam01_2',200),'Doorframes',False)
 if dx>dy:r=(x-dx/2-5,y-15,x+dx/2+5,y+15)
 else:r=(x-15,y-dy/2-5,x+15,y+dy/2+5)
 box('TF_DoorHeader_'+a['label'],r,220,226,mat('MI_WoodBeam01_2',200),'Doorframes',False)
# Restore round plan column at its original footprint.
for a in orig:
 if a['label']=='Plan_Circular_Column':
  c=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*a['t']['p']));c.set_actor_label('TF_Plan_Circular_Column');c.set_folder_path('TF_Architecture/Walls');c.static_mesh_component.set_static_mesh(u.load_asset('/Engine/BasicShapes/Cylinder'));c.static_mesh_component.set_material(0,wallmats[9]);c.set_actor_location(u.Vector(a['t']['p'][0],a['t']['p'][1],200),False,False);c.set_actor_scale3d(u.Vector(.8,.8,4))
# Balanced review exposure and atmosphere, without changing source assets.
pp=A.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_actor_label('TF_Interior_Exposure');pp.set_folder_path('TF_Lighting');pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
settings.set_editor_property('override_auto_exposure_min_brightness',True);settings.set_editor_property('override_auto_exposure_max_brightness',True)
settings.set_editor_property('auto_exposure_min_brightness',0);settings.set_editor_property('auto_exposure_max_brightness',0)
pp.set_editor_property('settings',settings)
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,3800),u.Rotator(pitch=-90,yaw=-90,roll=0))
assert L.save_current_level();report['saved']=True;report['created']=len(created)
(D/'architecture_report.json').write_text(json.dumps(report,indent=2));(D/'rooms.json').write_text(json.dumps(rooms))
u.log('THIRDFLOOR_ARCHITECTURE_DONE')
