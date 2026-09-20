import unreal as u, json, math, shutil, time
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6')
MAP='/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox1'
src=P/'Content/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox1.umap'
bak=P/'Saved/Backups/AsylumRestyle'/time.strftime('%Y%m%d_%H%M%S');bak.mkdir(parents=True,exist_ok=True);shutil.copy2(src,bak/src.name)
A=u.EditorAssetLibrary;S=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
assert L.load_level(MAP)
original=list(S.get_all_level_actors())
assert not any(a.get_actor_label().startswith('AS_') for a in original),'Already styled: refusing duplicate pass'
meshdata=json.loads(Path('/tmp/asylum_meshes.json').read_text());index={x['path'].split('.')[-1]:x['path'] for x in meshdata}
cache={};used=set();placed=[]
def asset(path):
 if path not in cache:cache[path]=A.load_asset(path)
 assert cache[path],path
 used.add(path);return cache[path]
def mat(name):return asset('/Game/Asylum/Materials/Building/'+name)
def spawn(name,m,loc,scale=(1,1,1),yaw=0,folder='Asylum/Props',collision=True):
 a=S.spawn_actor_from_class(u.StaticMeshActor,u.Vector(*loc),u.Rotator(0,yaw,0));a.set_actor_label('AS_'+name);a.set_folder_path(folder)
 a.static_mesh_component.set_static_mesh(asset(index[m]));a.set_actor_scale3d(u.Vector(*scale));a.static_mesh_component.set_collision_profile_name('BlockAll' if collision else 'NoCollision');placed.append(a);return a
# Mesh bounds fitting preserves footprint while correctly compensating imported mesh pivots.
def fit(name,m,center,size,yaw=0,folder='Asylum/Architecture',collision=True):
 md=next(x for x in meshdata if x['path']==index[m]);mn=md['min'];mx=md['max'];dims=[mx[i]-mn[i] for i in range(3)]
 target=list(size)
 if yaw%180:target[0],target[1]=target[1],target[0]
 scale=[target[i]/dims[i] if dims[i]>0.01 else 1 for i in range(3)]
 off=[(mn[i]+mx[i])/2*scale[i] for i in range(3)];ang=math.radians(yaw);ox=off[0]*math.cos(ang)-off[1]*math.sin(ang);oy=off[0]*math.sin(ang)+off[1]*math.cos(ang)
 return spawn(name,m,(center[0]-ox,center[1]-oy,center[2]-off[2]),scale,yaw,folder,collision)
def xyz(x,y,z=4):return ((x-1030)*2,(y-480)*2,z)
def prop(name,m,x,y,z=4,yaw=0,scale=1,room='Corridors',collision=True):
 md=next(v for v in meshdata if v['path']==index[m]);mn=md['min'];mx=md['max'];cx=(mn[0]+mx[0])/2*scale;cy=(mn[1]+mx[1])/2*scale;t=math.radians(yaw);X,Y,Z=xyz(x,y,z)
 return spawn(name,m,(X-cx*math.cos(t)+cy*math.sin(t),Y-cx*math.sin(t)-cy*math.cos(t),Z-mn[2]*scale),(scale,scale,scale),yaw,'Asylum/Rooms/'+room,collision)
# Read actual saved geometry; preserve altered coordinates and door openings.
for a in original:
 label=a.get_actor_label();folder=str(a.get_folder_path())
 if folder=='01_Walls' and isinstance(a,u.StaticMeshActor):
  o,e=a.get_actor_bounds(False);size=[e.x*2,e.y*2,e.z*2]
  if label=='Plan_Circular_Column':a.static_mesh_component.set_material(0,mat('MI_Wall02_3'));continue
  along=0 if size[0]>size[1] else 1;n=max(1,math.ceil(size[along]/300))
  for i in range(n):
   center=[o.x,o.y,o.z];center[along]=center[along]-size[along]/2+size[along]*(i+.5)/n;sz=size.copy();sz[along]/=n
   w=fit(label+'_%02d'%i,'SM_Wall01',center,sz,90 if along==0 else 0,'01_Walls')
   # Authentic plaster variations taken from Asylum interior rooms.
   wallmat='MI_WallTile02_1' if label.startswith(('R3','R8')) else ('MI_Wall02_1' if label.startswith('R4') else 'MI_Wall02_3')
   w.static_mesh_component.set_material(0,mat(wallmat))
   if o.z-e.z<5 and size[2]>200:
    for sign in (-1,1):
     cc=center.copy();perp=1-along;cc[perp]+=sign*(size[perp]/2+3);cc[2]=56
     ss=sz.copy();ss[perp]=6;ss[2]=110
     b=fit(label+'_Wainscot_%02d_%d'%(i,sign),'SM_Border01_2',cc,ss,90 if along==0 else 0,'Asylum/Architecture/Wainscoting',False)
  S.destroy_actor(a)
 elif folder=='02_Floors':a.static_mesh_component.set_material(0,mat('MI_FloorConcrete01'))
 elif folder.startswith('03_Ceilings'):
  a.static_mesh_component.set_material(0,mat('MI_Wall02_3'))
 elif folder=='04_Doorways':a.static_mesh_component.set_material(0,mat('MI_Border01'))
 elif label.startswith('Room_') and isinstance(a,u.TextRenderActor):
  a.set_actor_hidden_in_game(True);a.set_is_temporarily_hidden_in_editor(True)
 elif label.startswith('Fixture_'):S.destroy_actor(a)
 elif isinstance(a,u.PointLight):
  c=a.point_light_component;c.set_intensity(550);c.set_attenuation_radius(620);c.set_light_color(u.LinearColor(1,.73,.43,1))
  p=a.get_actor_location();spawn(label+'_Pendant','SM_Lamp01_1',(p.x,p.y,298),(.46,.46,.46),0,'Asylum/Lighting',False)
# Tile surfaces avoid stretching an entire building-sized cube UV.
for a in list(S.get_all_level_actors()):
 if str(a.get_folder_path())!='02_Floors':continue
 o,e=a.get_actor_bounds(False);nx=math.ceil(e.x*2/300);ny=math.ceil(e.y*2/300)
 for i in range(nx):
  for j in range(ny):
   xx=o.x-e.x+(i+.5)*e.x*2/nx;yy=o.y-e.y+(j+.5)*e.y*2/ny
   f=fit('Floor_%s_%d_%d'%(a.get_actor_label(),i,j),'SM_Floor01_1',(xx,yy,1.8),(e.x*2/nx,e.y*2/ny,3.6),folder='Asylum/Architecture/Floors',collision=False)
   px=xx/2+1030;py=yy/2+480
   if (1108<px<1426 and 279<py<706) or (1529<px<1847 and 499<py<706):f.static_mesh_component.set_material(1,mat('MI_Floor03_2'))
# Room 1: reception and waiting benches, leaving south-west entrance clear.
prop('R1_Reception','SM_ReceptionDesk01_1',490,225,yaw=90,room='01_Reception')
prop('R1_Desk','SM_Desk01_1',505,302,room='01_Reception',scale=.85)
for i,x in enumerate([310,355,400]):prop('R1_WaitingChair%d'%i,'SM_Chair01',x,206,yaw=180,room='01_Reception')
prop('R1_Records','SM_Locker01_1',155,225,yaw=90,scale=.85,room='01_Reception')
prop('R1_Book','SM_Book01_1',495,300,z=85,room='01_Reception',collision=False)
# Room 2: two beds and bedside medical equipment.
for i,y in enumerate([294,416]):
 prop('R2_Bed%d'%i,'SM_Bed01_1',875,y,room='02_Ward')
 prop('R2_Mattress%d'%i,'SM_Mattress01_1',875,y,z=52,room='02_Ward',collision=False)
prop('R2_Drip','SM_TripodDropper01',955,342,room='02_Ward')
prop('R2_Cart','SM_MedicalTable01',716,423,room='02_Ward')
# Room 3: treatment with clear path connecting northern entry to room 7.
prop('R3_OperatingTable','SM_OperatingTable01',1192,350,yaw=90,room='03_Treatment')
prop('R3_Cart','SM_MedicalTable01',1390,396,room='03_Treatment')
prop('R3_Instruments','SM_MedicalInstrument01_1',1390,396,z=112,room='03_Treatment',collision=False)
prop('R3_Drip','SM_TripodDropper01',1135,428,room='03_Treatment')
# Room 4: doctor office.
prop('R4_Desk','SM_Desk01_1',1740,246,room='04_Office')
prop('R4_Chair','SM_Chair01',1740,295,room='04_Office')
prop('R4_Cabinet','SM_Locker01_1',1817,337,scale=.8,room='04_Office',yaw=90)
prop('R4_Books','SM_Book01_3',1740,242,z=99,room='04_Office',collision=False)
prop('R4_Clock','SM_TableClock01',1780,246,z=99,room='04_Office',collision=False)
# Room 5: storage.
for i,x in enumerate([310,400,500]):prop('R5_Locker%d'%i,'SM_Locker01_1',x,505,room='05_Storage',scale=.85)
for i,(x,y) in enumerate([(540,620),(505,620),(540,651)]):prop('R5_Crate%d'%i,'SM_Box01_1',x,y,room='05_Storage')
# Room 6: isolation ward.
prop('R6_Bed','SM_Bed01_3',884,735,room='06_Isolation')
prop('R6_Mattress','SM_Mattress01_1',889,735,z=48,room='06_Isolation',collision=False)
prop('R6_Chair','SM_Chair01',965,595,yaw=20,room='06_Isolation')
# Room 7: observation / recovery; entry from room 3 preserved.
prop('R7_Bed','SM_Bed01_1',1305,659,room='07_Recovery')
prop('R7_Mattress','SM_Mattress01_1',1305,659,z=52,room='07_Recovery',collision=False)
prop('R7_Cart','SM_MedicalTable01',1140,650,room='07_Recovery')
prop('R7_Drip','SM_TripodDropper01',1400,590,room='07_Recovery')
# Room 8: autopsy / wash room.
prop('R8_Autopsy','SM_AutopsyTable01',1660,574,room='08_Mortuary')
prop('R8_Basin','SM_Basin01',1810,548,room='08_Mortuary')
prop('R8_Cart','SM_MedicalTable01',1560,650,room='08_Mortuary')
# Damp staining and dirt from the original pack, localized rather than covering all surfaces.
for i,(x,y) in enumerate([(460,333),(746,403),(1370,440),(1650,340),(510,572),(820,704),(1180,555),(1780,611),(624,510),(1490,680)]):
 d=S.spawn_actor_from_class(u.DecalActor,u.Vector(*xyz(x,y,8)),u.Rotator(-90,0,0));d.set_actor_label('AS_DampFloor_%02d'%i);d.set_folder_path('Asylum/Decals');d.decal.set_decal_material(asset('/Game/Asylum/Materials/Decals/MI_Dirt01_1'));d.decal.set_editor_property('decal_size',u.Vector(15,95,135))
# Fixed bounded exposure for consistently readable interior lighting.
pp=S.spawn_actor_from_class(u.PostProcessVolume,u.Vector());pp.set_actor_label('AS_Interior_Grade');pp.set_folder_path('Asylum/Lighting');pp.set_editor_property('unbound',True)
settings=pp.get_editor_property('settings')
for k,v in [('override_auto_exposure_min_brightness',True),('override_auto_exposure_max_brightness',True),('auto_exposure_min_brightness',0.0),('auto_exposure_max_brightness',2.0),('override_auto_exposure_bias',True),('auto_exposure_bias',0.4),('override_vignette_intensity',True),('vignette_intensity',.3)]:settings.set_editor_property(k,v)
pp.set_editor_property('settings',settings)
# Named review cameras.
for name,x,y,yaw in [('Reception',230,335,-20),('Ward',805,355,0),('Treatment',1350,300,135),('Corridor',620,425,0)]:
 c=S.spawn_actor_from_class(u.CameraActor,u.Vector(*xyz(x,y,165)),u.Rotator(0,yaw,0));c.set_actor_label('AS_View_'+name);c.set_folder_path('Asylum/ReviewCameras')
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(*xyz(230,335,170)),u.Rotator(-5,-20,0))
assert L.save_current_level()
report={'map':MAP,'backup':str(bak/src.name),'asylum_assets':sorted(used),'spawned_mesh_actors':len(placed),'total_actors':len(S.get_all_level_actors()),'rooms':['Reception','Ward','Treatment','Office','Storage','Isolation','Recovery','Mortuary']}
(P/'Scripts/asylum_restyle_report.json').write_text(json.dumps(report,indent=2));u.log('ASYLUM_RESTYLE_SUCCESS '+str(report['total_actors']))
