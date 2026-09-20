"""Offline unit-scale furniture/desktop cluster plan; never controls Unreal."""
import json,math,collections,random
from pathlib import Path
ROOT=Path(__file__).parent
source=json.loads((ROOT/'source.json').read_text())
flat=[]
for a in source:
    room=next((r for r in (8,9) if f'ThirdFloor01Room{r:02d}' in a['folder']),None)
    if room is None:continue
    for ci,c in enumerate(a['components']):
        if '/Props/' not in c['mesh'] and not c['mesh'].endswith('SM_Debris01.SM_Debris01'):continue
        for ii,t in enumerate(c.get('instances',[c['t']])):
            flat.append(dict(room=room,actor=a['name'],component=c['name'],component_index=ci,instance=ii if 'instances' in c else None,mesh=c['mesh'],mats=c['mats'],t=t,bounds=c['bounds'],short=c['mesh'].split('.')[-1]))
def dist(a,b):return math.hypot(a[0]-b[0],a[1]-b[1])
def find(r,m,x,y):return min((v for v in flat if v['room']==r and v['short']==m),key=lambda v:dist(v['t']['p'],[x,y]))
def key(v):return (v['actor'],v['component_index'],v['instance'])
plans=[];used=set(); groups=[]
def cluster(group,anchor,dest,yaw,extra=()):
    members=[anchor]+list(extra);unique=[]
    for v in members:
        if key(v) not in used:unique.append(v);used.add(key(v))
    ox,oy,_=anchor['t']['p']; ca=math.cos(math.radians(yaw));sa=math.sin(math.radians(yaw))
    for v in unique:
        t=v['t'];dx=t['p'][0]-ox;dy=t['p'][1]-oy
        p=[dest[0]+ca*dx-sa*dy,dest[1]+sa*dx+ca*dy,t['p'][2]-800]
        rr=list(t['r']);rr[1]+=yaw
        out={'room':v['room'],'group':group,'source':{k:v[k] for k in ('actor','component','component_index','instance')},'mesh':v['mesh'],'mats':v['mats'],'t':{'p':p,'r':rr,'s':list(t['s'])}}
        plans.append(out)
    groups.append({'name':group,'members':len(unique),'destination':dest,'yaw_delta':yaw,'source_anchor':key(anchor)})
def bed(r,m,x,y,dest,yaw,label):
    a=find(r,m,x,y);beds=[v for v in flat if v['room']==r and v['short'].startswith('SM_Bed01')]
    extras=[]
    for v in flat:
        if v['room']!=r or v==a:continue
        if v['short'].startswith('SM_Mattress') and min(beds,key=lambda b:dist(b['t']['p'],v['t']['p']))==a and dist(v['t']['p'],a['t']['p'])<170:extras.append(v)
        if v['short'].startswith(('SM_Basin','SM_Bucket','SM_WoodenTub','SM_Cloth')) and v['t']['p'][2]<845 and dist(v['t']['p'],a['t']['p'])<90:extras.append(v)
    cluster(label,a,dest,yaw,extras)
def desk(r,m,x,y,dest,yaw,label):
    a=find(r,m,x,y)
    extras=[v for v in flat if v['room']==r and v!=a and 850<v['t']['p'][2]<925 and dist(v['t']['p'],a['t']['p'])<130 and not v['short'].startswith(('SM_Bed','SM_Mattress','SM_Battery','SM_Lamp03'))]
    cluster(label,a,dest,yaw,extras)
def iv(r,x,y,dest,yaw,label):
    a=find(r,'SM_TripodDropper01',x,y)
    extras=[v for v in flat if v['room']==r and 'DropperBloodBag' in v['short'] and v['t']['p'][2]>940 and dist(v['t']['p'],a['t']['p'])<65]
    cluster(label,a,dest,yaw,extras)
# Room 8: three beds at original scale. Southern 95+ cm remains open for the door.
bed(8,'SM_Bed01_1',-132,2821,[1093,202],90,'R08_Bed_A')
bed(8,'SM_Bed01_3',337,2830,[1318,202],90,'R08_Bed_B')
bed(8,'SM_Bed01_5',334,3070,[1548,202],90,'R08_Bed_C')
desk(8,'SM_Desk01_6',-207,2648,[1210,105],90,'R08_Bedside_Bloodbags')
desk(8,'SM_Desk01_6',-231,2950,[1428,105],90,'R08_Bedside_Medicines')
desk(8,'SM_Desk01_6',426,2949,[1428,274],90,'R08_Bedside_Food')
iv(8,-110,2746,[1210,260],90,'R08_Drip_A')
iv(8,377,3012,[1428,188],90,'R08_Drip_C')
# Room 9: two beds + original detailed writing desk along the north wall.
bed(9,'SM_Bed01_3',1535,2342,[220,-573],0,'R09_North_Bed_A')
north_b=find(9,'SM_Bed01_5',1535,2864)
bed(9,'SM_Bed01_5',1535,2864,[723,-573],-north_b['t']['r'][1],'R09_North_Bed_B')
desk(9,'SM_Desk01_5',1087,2595,[464,-564],94.1,'R09_North_Records')
# Three beds run along the west side; the central room block must move +100 cm X.
bed(9,'SM_Bed01_4',653,2583,[67,-224],90,'R09_West_Bed_A')
bed(9,'SM_Bed01_2',662,2817,[67,109],90,'R09_West_Bed_B')
bed(9,'SM_Bed01_3',593,3116,[67,420],0,'R09_West_Bed_C')
# Keep the wheelchair and standing drip by the top row, outside the south aisle.
cluster('R09_Wheelchair',find(9,'SM_WheelChair01',1197,2514),[914,-563],124.4)
iv(9,1479,2938,[25,-568],0,'R09_North_Drip')
# Source hanging lamp variants, one per bed bay, remain at Z≈395 cm.
lamps8=[v for v in flat if v['room']==8 and v['short']=='SM_Lamp03_1']
lamps9=[v for v in flat if v['room']==9 and v['short']=='SM_Lamp03_1']
for i,p in enumerate(([1093,204],[1318,204],[1548,204])):cluster(f'R08_Lamp_{i+1}',lamps8[i],p,90)
for i,p in enumerate(([220,-555],[723,-555],[67,-224],[67,109],[67,420])):cluster(f'R09_Lamp_{i+1}',lamps9[i],p,0 if i<2 else 90)
# Original rubble patches: keep original mesh scale and yaw, pack distinct patches
# without overlapping projected boxes so identical mesh polygons never coincide.
rng=random.Random(908)
def extents(v):
    a,b=v['bounds'];t=v['t'];ca=math.cos(math.radians(t['r'][1]));sa=math.sin(math.radians(t['r'][1]))
    pts=[(ca*x*t['s'][0]-sa*y*t['s'][1],sa*x*t['s'][0]+ca*y*t['s'][1]) for x in (a[0],b[0]) for y in (a[1],b[1])]
    return [min(q[i] for q in pts) for i in (0,1)],[max(q[i] for q in pts) for i in (0,1)]
for r,want in ((8,9),(9,15)):
    placed=[];candidates=[v for v in flat if v['room']==r and v['short']=='SM_Debris01']
    candidates.sort(key=lambda v:(extents(v)[1][1]-extents(v)[0][1])*(extents(v)[1][0]-extents(v)[0][0]))
    rects=[(997,39,1635,451)] if r==8 else [(-23,-631,971,-427),(-23,-427,231,579)]
    for rect in rects:
        cursor_x,cursor_y=rect[0]+4,rect[1]+5;row_height=0
        for v in candidates:
            if key(v) in used or len(placed)>=want:continue
            mn,mx=extents(v);w,h=mx[0]-mn[0],mx[1]-mn[1]
            if cursor_x+w>rect[2]-3:
                cursor_x=rect[0]+4;cursor_y+=row_height+13;row_height=0
            if cursor_y+h>rect[3]-3:continue
            x,y=cursor_x-mn[0],cursor_y-mn[1]
            box=(x+mn[0],y+mn[1],x+mx[0],y+mx[1])
            cluster(f'R{r:02d}_Floor_Debris_{len(placed)+1:02d}',v,[x,y],0);plans[-1]['collision']=False;placed.append(box)
            cursor_x+=w+13;row_height=max(row_height,h)
def floor_item(r,m,x,y,dest,label,ground=True):
    v=find(r,m,x,y)
    if key(v) in used:return
    cluster(label,v,dest,0);plans[-1]['collision']=False
    if ground:plans[-1]['t']['p'][2]=0.15-v['bounds'][0][2]*v['t']['s'][2]
floor_item(8,'SM_Envelope01_4',-212,2091,[1080,366],'R08_Floor_Envelope_A')
floor_item(8,'SM_Envelope01_2',-617,2156,[1350,388],'R08_Floor_Envelope_B')
floor_item(8,'SM_Medications01_2',396,2514,[1245,368],'R08_Floor_Medication_A')
floor_item(8,'SM_Medications01_1',383,2500,[1527,371],'R08_Floor_Medication_B')
floor_item(9,'SM_FolderPaper01_5',963,2572,[170,-383],'R09_Floor_Records_A')
floor_item(9,'SM_FolderPaper01_4',906,3069,[162,36],'R09_Floor_Records_B')
floor_item(9,'SM_FolderPaper01_3',841,3100,[166,273],'R09_Floor_Records_C')
floor_item(9,'SM_FolderPaper01_6',840,3116,[174,510],'R09_Floor_Records_D')
floor_item(9,'SM_Book01_5',1584,2974,[544,-477],'R09_Floor_Dropped_Book')
floor_item(9,'SM_Cloth01_6',1503,3106,[105,-57],'R09_Floor_Discarded_Cloth')
# Actor decals retain source material/size/sort settings when duplicated by Unreal.
# Puddle/blood pairs retain their relative offsets, heights, rotations and scales.
decals=[]
def decal_group(r,names,dest):
    aa=[next(a for a in source if a['name']==n) for n in names];anchor=aa[0]['t']['p']
    for a in aa:
        t=a['t'];decals.append({'room':r,'source':{'actor':a['name']},'t':{'p':[dest[0]+t['p'][0]-anchor[0],dest[1]+t['p'][1]-anchor[1],t['p'][2]-800],'r':t['r'],'s':t['s']}})
decal_group(8,['MI_Puddle01_28','MI_BloodDecal02_56'],[1120,340])
decal_group(8,['MI_Puddle01_59','MI_BloodDecal02_52'],[1390,334])
decal_group(8,['MI_Puddle01_30','MI_BloodDecal02_53'],[1510,200])
decal_group(9,['MI_Puddle01_8','MI_BloodDecal02_20'],[116,-80])
decal_group(9,['MI_Puddle01_14','MI_BloodDecal02_22'],[107,262])
decal_group(9,['MI_BloodDecal02_21'],[731,-544])
(ROOT/'decals_plan89.json').write_text(json.dumps(decals,indent=2))
(ROOT/'props_plan_89.json').write_text(json.dumps(plans,indent=2))
(ROOT/'props_plan_89_groups.json').write_text(json.dumps({'central_room_shift_x':100,'scale_policy':'Original per-instance scale preserved; positions regrouped. No affine room scaling.','groups':groups,'counts':dict(collections.Counter(p['room'] for p in plans))},indent=2))
print(json.dumps({'entries':len(plans),'counts':dict(collections.Counter(p['room'] for p in plans)),'groups':len(groups)},indent=2))
