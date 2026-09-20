import unreal as u,json,math,re
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6');D=P/'Scripts/CorridorWidening';OLD=P/'Scripts/ThirdFloorTransfer'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name()=='L_Horror_Floorplan_codex'
assert not (D/'applied.json').exists(),'Corridor update already applied'
before=json.loads((D/'before.json').read_text()); actors={a.get_name():a for a in A.get_all_level_actors()}
assert len(actors)==len(before)
# Refuse to rebuild if the live architecture was edited after the snapshot.
for b in before:
 a=actors[b['name']];p=a.get_actor_location()
 assert max(abs(p.x-b['p'][0]),abs(p.y-b['p'][1]),abs(p.z-b['p'][2]))<.001,b['label']
room_delta={1:(0,-72),4:(172,0),8:(172,0)}
report={'changes':{'room1_north_cm':72,'rooms4_8_east_cm':172},'moved':[],'walls':[],'floor':[]}
orig=json.loads((OLD/'target.json').read_text());cube=u.load_asset('/Engine/BasicShapes/Cube')
def mat(name,cm=400):
 q=u.load_asset('/Game/HorrorWhitebox/ThirdFloor/Materials/'+name+'_World');assert q,name;return q
wallmats={0:mat('MI_Wall02_6'),1:mat('MI_Wall01_2'),2:mat('MI_Wall02_2'),3:mat('MI_Wall02_5'),4:mat('MI_Wall01_1'),5:mat('MI_Wall02_6'),6:mat('MI_Wall02_5'),7:mat('MI_Wall02_5'),8:mat('MI_Wall02_7'),9:mat('MI_Wall02_5')}
floormats={0:mat('MI_Floor02_1'),1:mat('MI_Floor01_1'),2:mat('MI_Floor02_1'),3:mat('MI_Floor03_4'),4:mat('MI_Floor02_1'),5:mat('MI_FloorConcrete01'),6:mat('MI_Floor03_5'),7:mat('MI_Floor03_4'),8:mat('MI_Floor01_1'),9:mat('MI_Floor01_1')}
rooms={1:(-1815,-703,-891,-289),2:(-698,-631,-36,-26),3:(257,-401,893,13),4:(1169,-579,1807,-167),5:(-1527,-13,-891,401),6:(-685,165,-49,579),7:(257,39,893,451),8:(1169,39,1807,451)}
def roomat(x,y):
 for n,(x1,y1,x2,y2) in rooms.items():
  if x1-.1<=x<=x2+.1 and y1-.1<=y<=y2+.1:return n
 if -23<=x<=1143 and -703<=y<=579:return 9
 return 0
created=[]
def box(label,rect,z0,z1,m,folder,collision=True):
 x0,y0,x1,y1=rect
 a=A.spawn_actor_from_class(u.StaticMeshActor,u.Vector((x0+x1)/2,(y0+y1)/2,(z0+z1)/2))
 a.set_actor_label(label);a.set_folder_path('TF_Architecture/'+folder);c=a.static_mesh_component;c.set_static_mesh(cube);c.set_material(0,m)
 a.set_actor_scale3d(u.Vector((x1-x0)/100,(y1-y0)/100,(z1-z0)/100));c.set_collision_enabled(u.CollisionEnabled.QUERY_AND_PHYSICS if collision else u.CollisionEnabled.NO_COLLISION)
 if collision:c.set_collision_profile_name('BlockAll')
 created.append(a);return a

# Preserve all room props, damaged floor modules, tiles and room floors as existing actors.
# Only rigid translations are applied; materials, rotation and scale are untouched.
for b in before:
 a=actors[b['name']];f=b['folder'];label=b['label'];rn=None
 if f.startswith('TF_Rooms/'):rn=int(f.split('/')[1])
 elif f.startswith('TF_TransferredDecals/'):rn=int(f.split('/')[1])
 elif f=='TF_Lighting/RoomPracticals':rn=int(re.match(r'TF_R(\d+)_',label)[1])
 elif f in ['TF_Architecture/Floors','TF_Architecture/OriginalDamagedFloors']:
  rn=int(re.search(r'_R(\d+)_',label)[1])
 elif f=='TF_Architecture/Doorframes':rn=int(re.search(r'_R(\d+)_',label)[1])
 elif label in ['Practical_00','Practical_03','Practical_07']:rn={'Practical_00':1,'Practical_03':4,'Practical_07':8}[label]
 elif label=='TF_View_Ward08':rn=8
 delta=room_delta.get(rn,(0,0))
 if label in ['Practical_17','Practical_18']:delta=(172,0)
 if label=='Practical_08':delta=(0,-36)
 if label=='Practical_16':delta=(131,0)
 if delta!=(0,0):
  a.set_actor_location(u.Vector(b['p'][0]+delta[0],b['p'][1]+delta[1],b['p'][2]),False,False)
  report['moved'].append({'label':label,'name':b['name'],'delta':[*delta,0]})
 destroy=f in ['TF_Architecture/Walls','TF_Architecture/WallFinishes','TF_Architecture/Mouldings','TF_Architecture/Ceilings']
 if f=='TF_Architecture/Floors' and rn in [0,2,9]:destroy=True
 if destroy:A.destroy_actor(a)
# Recreate disjoint wall geometry from original labeled pieces with local expansion.
rects=[];lintels=[]
for a in orig:
 label=a['label']
 if a['folder']!='01_Walls' or label.startswith('R2_') or label=='Plan_Circular_Column':continue
 if not a['components'] or not a['components'][0]['mesh'].startswith('/Engine/BasicShapes/Cube'):continue
 x,y,z=a['t']['p'];dx,dy,dz=[v*100 for v in a['t']['s']]
 if label.startswith(('R3_','R7_')):x+=100
 if label=='R8_West':dy=464
 if label.startswith('R1_'):y-=72
 if label.startswith(('R4_','R8_')):x+=172
 if label=='Exterior_00':x+=86;y-=72;dx+=172
 if label=='Exterior_01':x+=172;y-=36;dy+=72
 if label in ['Exterior_02','Exterior_03']:x+=172
 if label=='Exterior_04':x+=86;dx+=172
 if label=='Exterior_09':y-=36;dy+=72
 r=[round(x-dx/2,3),round(y-dy/2,3),round(x+dx/2,3),round(y+dy/2,3)]
 (lintels if 'Lintel' in label else rects).append(r)
foot=[(-1841,-729,1169,-605),(-1841,-605,2011,-13),(-1731,-13,2011,605),(735,605,2011,655)]
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
segments=[];skin_index=0
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
   if rn not in [5,6]:
    box('TF_WallFace_%02d_%03d_%d'%(rn,skin_index,z0),r,z0,z1,wallmats[rn],'WallFinishes',False);skin_index+=1
   if z0==0:segments.append({'axis':axis,'c':c,'n':n,'room':rn,'lo':lo,'hi':hi})
# Original Asylum moulded wood panels and cornices tiled to each exposed inner wall segment.
for si,s in enumerate(segments):
 axis,c,n,rn,lo,hi=[s[k] for k in ['axis','c','n','room','lo','hi']]
 # Skip exterior facing surface by testing whether the point is within the floor footprint.
 x=c+n[0]*5 if axis=='V' else (lo+hi)/2;y=c+n[1]*5 if axis=='H' else (lo+hi)/2
 inside=any(r[0]<=x<=r[2] and r[1]<=y<=r[3] for r in foot)
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
xs=sorted(set(v for r in list(rooms.values())+foot for v in[r[0],r[2]]));ys=sorted(set(v for r in list(rooms.values())+foot for v in[r[1],r[3]]))
groups={}
for i in range(len(xs)-1):
 for j in range(len(ys)-1):
  x=(xs[i]+xs[i+1])/2;y=(ys[j]+ys[j+1])/2
  if not any(r[0]<=x<=r[2] and r[1]<=y<=r[3] for r in foot):continue
  groups.setdefault(roomat(x,y),set()).add((i,j))
for rn,g in groups.items():
 if rn not in [0,2,9]:continue
 for i,r in enumerate(merged_cells(xs,ys,g)):
  box('TF_Floor_R%02d_%02d'%(rn,i),r,-20,0,floormats[rn],'Floors');report['floor'].append({'room':rn,'rect':r,'z':0,'material':floormats[rn].get_path_name()})
for i,r in enumerate(foot):
 a=box('TF_Ceiling_%02d'%i,r,400,414,mat('MI_Wall02_3'),'Ceilings');a.set_is_temporarily_hidden_in_editor(True)

report['rooms']=rooms;report['footprint']=foot
(D/'rooms.json').write_text(json.dumps(rooms,indent=2))
A.set_selected_level_actors([])
L.editor_set_viewport_realtime(True);L.editor_set_game_view(True)
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(85,-37,2750),u.Rotator(pitch=-90,yaw=-90,roll=0))
L.editor_invalidate_viewports()
assert L.save_current_level()
report['created']=len(created);report['saved']=True
(D/'applied.json').write_text(json.dumps(report,indent=2))
u.log('CORRIDOR_WIDENED_AND_SAVED')
