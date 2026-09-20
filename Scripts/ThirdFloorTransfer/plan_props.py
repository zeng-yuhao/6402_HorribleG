"""Place Showcase third-floor props without changing any instance scale.

The user drawing is a floorplan, not an instruction source. Source identities are
retained so the editor transfer can reproduce original component materials. Large
furniture is fitted as rigid groups; books/instruments/shelf contents follow their
support rather than the compressed room coordinates.
"""
from pathlib import Path
import json, math, collections, copy
BASE=Path(__file__).resolve().parent
SOURCE=json.loads((BASE/'source.json').read_text())
TARGET=json.loads((BASE/'target.json').read_text())
# Inner faces measured from target.json, with the approved +100 cm central block shift.
ROOMS={1:(-1815,-631,-891,-217),2:(-698,-631,-36,-26),3:(257,-401,893,13),4:(997,-579,1635,-167),5:(-1527,-13,-891,401),6:(-685,165,-49,579),7:(257,39,893,451)}
DOORS={1:[(-1678,-317,-1538,-217)],3:[(664,-401,804,-300),(488,-88,628,13)],4:[(1106,-277,1246,-167)],5:[(-1412,291,-1272,401)],6:[(-685,258,-580,398)],7:[(488,39,628,145)]}
SOURCE_ROOM={1:'01',2:'04',3:'05',4:'07',5:'02',6:'06',7:'05'}
# Coordinate mappings are only used for centers of rigid furniture groups.
FRAME={1:((-500,600),(-1353,-424),-90,(.74,1)),2:((-100,-1400),(-367,-350),-90,(1,1)),3:((300,-2600),(550,-194),-90,(.70,.67)),4:((600,1300),(1316,-373),0,(.65,.66)),5:((-561,-400),(-1209,194),-90,(.76,1)),6:((0,0),(-940,-428),0,(1,1)),7:((-100,-2600),(550,260),-90,(.69,1))}

def rot(p,yaw):
 c,s=math.cos(math.radians(yaw)),math.sin(math.radians(yaw));return [c*p[0]-s*p[1],s*p[0]+c*p[1]]
def box(t, bb):
 # UE Rotator convention. Columns are local X/Y/Z axes in world space.
 p,y,r=map(math.radians,t['r']);sp,cp=math.sin(p),math.cos(p);sy,cy=math.sin(y),math.cos(y);sr,cr=math.sin(r),math.cos(r)
 M=((cp*cy, sr*sp*cy-cr*sy, -(cr*sp*cy+sr*sy)),(cp*sy,sr*sp*sy+cr*cy,cy*sr-cr*sp*sy),(sp,-sr*cp,cr*cp))
 cen=[(bb[0][i]+bb[1][i])*.5*t['s'][i] for i in range(3)];ext=[abs(bb[1][i]-bb[0][i])*.5*abs(t['s'][i]) for i in range(3)]
 C=[t['p'][i]+sum(M[i][j]*cen[j] for j in range(3)) for i in range(3)];E=[sum(abs(M[i][j])*ext[j] for j in range(3)) for i in range(3)]
 return [C[i]-E[i] for i in range(3)]+[C[i]+E[i] for i in range(3)]
def center(b):return [(b[i]+b[i+3])/2 for i in range(3)]
def name(e):return e['mesh'].split('.')[-1]
def flat():
 out=[]
 for a in SOURCE:
  for c in a['components']:
   if not ('/Props/' in c['mesh'] or '/Decals/SM_' in c['mesh']):continue
   for i,t in enumerate(c.get('instances',[c['t']])):
    out.append(dict(source={'actor':a['name'],'component':c['name'],'instance':i if 'instances' in c else None},mesh=c['mesh'],mats=c['mats'],source_t=t,mesh_bounds=c['bounds'],folder=a['folder'],b=box(t,c['bounds'])))
 return out
ALL=flat()
def key(e):return (e['source']['actor'],e['source']['instance'])
def hero(e):
 n=name(e)
 return (any(k in n for k in ['AutopsyTable','MedicalBed','MedicalTable','LeatherSofa','LeatherChair','Chair02','Chair01','Sink01','ToiletBowl','ToiletBooth']) or '/Furniture/SM_Desk01_' in e['mesh'] and n not in ['SM_Desk01_7','SM_Desk01_8'] or '/Furniture/SM_Locker01_' in e['mesh'])
def mapcenter(room,p):
 sc,dc,yaw,s=FRAME[room];q=rot([p[0]-sc[0],p[1]-sc[1]],yaw);return [dc[0]+q[0]*s[0],dc[1]+q[1]*s[1]]
# Explicit layout of the principal furniture. x,y are instance pivots; yaw is
# absolute final yaw. A fourth value vertically grounds source terrace furniture.
MANUAL={
1:{('SM_Chair01HISMA_1249',0):(-1655,-408,112),('SM_Desk01_6HISMA_1255',0):(-1215,-375,-94),('SM_LeatherChair01HISMA_1283',0):(-1450,-319,17),('SM_LeatherSofa01HISMA',0):(-1330,-529.6,-175)},
2:{('SM_AutopsyTable01HISMA_1047',0):(-367,-350,-180),('SM_Desk01_6HISMA_1075',0):(-135,-100,-9),('SM_Desk01_5HISMA_1077',0):(-245,-195,-180),('SM_Desk01_5HISMA_1077',1):(-620,-140,-90,-99),('SM_Desk01_5HISMA_1077',2):(-180,-555,0,-99),('SM_MedicalTable01HISMA_1100',0):(-460,-220,-159),('SM_MedicalTable02HISMA_1102',0):(-135,-350,123),('SM_MedicalTable02HISMA_1102',1):(-645,-350,63),('SM_MedicalTable02HISMA_1102',2):(-345,-475,62)},
3:{('SM_AutopsyTable01HISMA',0):(510,-194,0),('SM_MedicalBed01HISMA_990',1):(320,-184,-90),('SM_Desk01_5HISMA_961',0):(825,-195,-90),('SM_Locker01_4HISMA_980',0):(455,-355,-180),('SM_MedicalTable02HISMA',0):(430,-56,-48),('SM_MedicalTable01HISMA',1):(820,-50,14),('SM_Sink01HISMA_932',2):(891,-348,0),('SM_Sink01HISMA_932',3):(865,-80,0)},
4:{('SM_Desk01_2HISMA',0):(1095,-395,-90),('SM_LeatherChair01HISMA_855',0):(1223,-395,90),('SM_Desk01_5HISMA_817',0):(1305,-518,0),('SM_Desk01_5HISMA_817',2):(1515,-518,0),('SM_Desk01_5HISMA_817',1):(1388,-347,-90),('SM_Desk01_5HISMA_817',3):(1487,-347,-90),('SM_Locker01_3HISMA',0):(1068,-545,0),('SM_Locker01_3HISMA',1):(1340,-209,0),('SM_Locker01_3HISMA',2):(1540,-209,0),('SM_Locker01_2HISMA_858',0):(1295,-347,90),('SM_Sink01HISMA',0):(1620,-355,0),('SM_Chair02_1HISMA_811',3):(1580,-277,63)},
5:{('SM_Chair02_1HISMA_1189',0):(-1008,325,-210),('SM_Locker01_4HISMA_1195',0):(-1485,169,90),('SM_Locker01_4HISMA_1195',2):(-1340,169,-90),('SM_Locker01_4HISMA_1195',1):(-1283,169,90),('SM_Locker01_4HISMA_1195',5):(-1138,169,-90),('SM_Locker01_4HISMA_1195',4):(-1081,169,90),('SM_Locker01_4HISMA_1195',3):(-936,169,-90)},
6:{('SM_ToiletBooth01HISMA',0):(-567,197.7,90)},
7:{('SM_AutopsyTable01HISMA',1):(550,260,0),('SM_Desk01_5HISMA_961',1):(825,220,-90),('SM_Chair01HISMA_955',0):(735,300,-107),('SM_MedicalTable02HISMA',1):(740,390,-167),('SM_MedicalTable01HISMA',0):(350,165,-45)}
}
# Extra spectator chairs are selectively retained; their source platform is omitted
# because the requested surgery area is open and has a continuous walking floor.
for i,p in enumerate([(-645,-575),(-575,-575),(-505,-575),(-435,-575),(-505,-80),(-435,-80),(-365,-80),(-295,-80)]):MANUAL[2][('SM_Chair02_1HISMA_1073',i)]=(*p,0 if i<4 else 180,-101 if i<7 else -100)
DROP={2:{('SM_Chair02_1HISMA_1073',i) for i in range(8,28)},3:{('SM_Sink01HISMA_932',3),('SM_Chair02_1HISMA_953',3),('SM_Chair02_1HISMA_953',4)},4:{('SM_Locker01_2HISMA_858',1),*{('SM_Chair02_1HISMA_811',i) for i in range(3)}}}

def rect_inter(a,b,margin=0):return min(a[3],b[2])-max(a[0],b[0])>margin and min(a[4],b[3])-max(a[1],b[1])>margin
def dist_box(p,b):return math.hypot(max(b[0]-p[0],0,p[0]-b[3]),max(b[1]-p[1],0,p[1]-b[4]))
def is_wall(e):return any(q in name(e) for q in ['MedicalPoster','InformationTable','Battery','ToiletMirror'])
def is_debris(e):return '/Decals/' in e['mesh'] or any(q in name(e) for q in ['FolderPaper']) and e['source_t']['p'][2]<805

def run():
 entries=[];report={};omitted=[]
 for room in range(1,8):
  candidates=[copy.deepcopy(e) for e in ALL if 'Room'+SOURCE_ROOM[room] in e['folder']]
  if room in (3,7):candidates=[e for e in candidates if -300<=e['source_t']['p'][0]<=700 and e['source_t']['p'][1]<-2150 and (e['source_t']['p'][0]>=100)==(room==3)]
  anchors=[e for e in candidates if hero(e)]
  # Sink meshes at the end of the autopsy table are a part of that assembly.
  linked={}
  for e in list(anchors):
   if 'Sink01' in name(e):
    near=[h for h in anchors if 'AutopsyTable' in name(h) and math.dist(h['source_t']['p'][:2],e['source_t']['p'][:2])<150]
    if near:linked[key(e)]=near[0];anchors.remove(e)
  for e in anchors:
   p=mapcenter(room,e['source_t']['p']);yaw=e['source_t']['r'][1]+FRAME[room][2];z=0
   if key(e) in MANUAL.get(room,{}):
    m=MANUAL[room][key(e)];p=list(m[:2]);yaw=m[2];z=m[3] if len(m)>3 else 0
   if room==6 and 'Sink01' in name(e):p[1]=577
   e['delta_yaw']=yaw-e['source_t']['r'][1];e['dest_center']=p;e['zdelta']=z;e['excluded']=key(e) in DROP.get(room,set())
  # Assign supports using footprint distance and height, retaining drawer/door parts
  # and tabletop props as one rigid source-coordinate group.
  groups={key(a):[a] for a in anchors}
  free=[]
  for e in candidates:
   if e in anchors:continue
   p=e['source_t']['p'];n=name(e)
   if key(e) in linked:
    groups[key(linked[key(e)])].append(e);continue
   scores=[]
   for a in anchors:
    ab=a['b'];gap=dist_box(p,ab);within=(ab[0]-8<=p[0]<=ab[3]+8 and ab[1]-8<=p[1]<=ab[4]+8)
    # Height term is deliberately small: shelves contain objects at many heights.
    score=gap+0.12*max(0,p[2]-ab[5],ab[2]-p[2])
    if 'Locker01Door' in n or 'Locker01Drawer' in n:
     score+=0 if 'Locker' in name(a) else 1000
    if n in ['SM_Desk01_7','SM_Desk01_8']:score=math.dist(p[:2],a['source_t']['p'][:2])+(0 if 'Desk' in name(a) else 1000)
    if is_wall(e):score+=300
    if p[2]<815 and is_debris(e):score+=300
    if 'Lamp03' in n:score+=300
    if '/Pipe' in e['mesh']:score+=300
    scores.append((score,a))
   if scores and min(scores,key=lambda q:q[0])[0]<90:
    a=min(scores,key=lambda q:q[0])[1];groups[key(a)].append(e)
   else:free.append(e)
  def transform(e,a=None):
   t=copy.deepcopy(e['source_t'])
   if a:
    q=rot([t['p'][0]-a['source_t']['p'][0],t['p'][1]-a['source_t']['p'][1]],a['delta_yaw']);t['p']=[a['dest_center'][0]+q[0],a['dest_center'][1]+q[1],t['p'][2]-800+a['zdelta']];t['r'][1]+=a['delta_yaw']
   else:t['p']=mapcenter(room,t['p'])+[t['p'][2]-800];t['r'][1]+=FRAME[room][2]
   return t
  def clamp_group(items):
   # Move the group together to fit; never rescale its geometry or separate its props.
   bb=[box(e['t'],e['mesh_bounds']) for e in items];B=[min(b[i] for b in bb) for i in range(3)]+[max(b[i+3] for b in bb) for i in range(3)]
   loX,loY,hiX,hiY=ROOMS[room];pad=(2 if 'Sink01' in name(items[0]) else 12) if items[0]['role']=='furniture' else 1
   if B[3]-B[0]>hiX-loX-2*pad or B[4]-B[1]>hiY-loY-2*pad:return False
   dx=max(loX+pad-B[0],min(0,hiX-pad-B[3]));dy=max(loY+pad-B[1],min(0,hiY-pad-B[4]))
   for e in items:e['t']['p'][0]+=dx;e['t']['p'][1]+=dy
   return True
  placed=[]
  for a in anchors:
   gg=groups[key(a)]
   if a['excluded']:
    for e in gg:omitted.append({'room':room,'source':e['source'],'mesh':e['mesh'],'reason':'Surplus furniture/support contents omitted to maintain usable room and door clearances.'})
    continue
   out=[]
   for e in gg:
    q={k:copy.deepcopy(e[k]) for k in ['source','mesh','mats','mesh_bounds']};q.update(room=room,t=transform(e,a),group=f"R{room}_{a['source']['actor']}_{a['source']['instance']}",role='furniture' if e==a else 'attached_detail');out.append(q)
   # Only furniture defines fit; original clothing or scattered detail can extend
   # beyond that footprint but is independently pruned at the perimeter below.
   core=[out[0]]
   before=out[0]['t']['p'][:2]
   clamp_group(core);shift=[core[0]['t']['p'][i]-before[i] for i in range(2)]
   for q in out[1:]:
    q['t']['p'][0]+=shift[0];q['t']['p'][1]+=shift[1]
   placed.extend(out)
  for e in free:
   if room==2 and name(e)=='SM_Lamp03_1' and e['source']['instance'] in(2,3):
    omitted.append({'room':room,'source':e['source'],'mesh':e['mesh'],'reason':'Second crossed chandelier bar omitted to prevent duplicate fixture intersection.'});continue
   if 'Battery' in name(e) and (room in (3,4) or room==1 and e['source']['instance']==1):
    omitted.append({'room':room,'source':e['source'],'mesh':e['mesh'],'reason':'Surplus radiator omitted because source wall position conflicts with relocated furniture or a doorway.'});continue
   q={k:copy.deepcopy(e[k]) for k in ['source','mesh','mats','mesh_bounds']};q.update(room=room,t=transform(e),group=f"R{room}_loose_{len(placed)}",role='loose_detail')
   if room==2 and name(e)=='SM_Debris01' and e['source_t']['p'][2]>850:q['t']['p'][2]-=100
   if room==1 and 'Battery' in name(e):q['t']['p'][:2]=[-1610,-574];q['t']['r'][1]=90
   if room==7 and 'Battery' in name(e):q['t']['p'][:2]=[250,335];q['t']['r'][1]=180
   if room==6 and 'Battery' in name(e):q['t']['p'][0]=-42
   if room==1 and 'InformationTable' in name(e):
    # Original wall collage spacing stays rigid, rather than scaled toward overlap.
    q['t']['p'][0]=-1230+(e['source_t']['p'][1]-600);q['t']['p'][1]=-629
   if room==3 and 'MedicalPoster' in name(e):
    q['t']['p'][:2]=[891,-300 if '_5' in name(e) else -160];q['t']['r'][1]=-90
   if room==4 and 'MedicalPoster' in name(e):
    idx=int(name(e).split('_')[-1]);q['t']['p'][:2]=[{1:1395,2:1510,3:1280,4:1165}[idx],-577]
   if room==4 and 'InformationTable' in name(e):q['t']['p']=[1065+90*e['source']['instance'],-577,330]
   if room==6 and 'ToiletMirror' in name(e):q['t']['p'][1]=577
   if room==6 and 'Pipe' in name(e):
    # Preserve plumbing as a rigid network and trim the two original wall returns
    # that extend beyond the narrower target wall.
    b=box(q['t'],q['mesh_bounds']);loX,loY,hiX,hiY=ROOMS[room]
    if b[0]<loX+2 or b[3]>hiX-2:omitted.append({'room':room,'source':e['source'],'mesh':e['mesh'],'reason':'Plumbing return extends beyond target wall; remaining network retained at source scale.'});continue
   else:clamp_group([q])
   placed.append(q)
  # Reject loose/attached debris that exceeds the shell; floor clutter stays on the
  # new floor with the same source elevation, thus no doubled floor surfaces.
  keep=[]
  for q in placed:
   b=box(q['t'],q['mesh_bounds']);l,t,r,bo=ROOMS[room]
   if q['role']!='furniture' and (b[0]<l-.5 or b[3]>r+.5 or b[1]<t-.5 or b[4]>bo+.5):
    omitted.append({'room':room,'source':q['source'],'mesh':q['mesh'],'reason':'Detail exceeded the room shell after rigid group placement.'});continue
   q['world_bounds']=b;keep.append(q)
  entries.extend(keep)
  report[str(room)]={'source_room':SOURCE_ROOM[room],'target_inner_bounds':ROOMS[room],'source_candidates':len(candidates),'placed':len(keep),'furniture':[{'mesh':name(q),'source':q['source'],'p':q['t']['p'],'yaw':q['t']['r'][1]} for q in keep if q['role']=='furniture'],'unique_meshes':len(set(q['mesh'] for q in keep))}
 (BASE/'props_plan.json').write_text(json.dumps({'entries':entries,'rooms':report,'omitted':omitted},indent=2))
 (BASE/'props_report.json').write_text(json.dumps({'rooms':report,'omitted':omitted},indent=2))
 print(json.dumps({'entries':len(entries),'rooms':{k:{'placed':v['placed'],'source_candidates':v['source_candidates'],'furniture':len(v['furniture'])} for k,v in report.items()},'omitted':len(omitted)},indent=2))
if __name__=='__main__':run()
