"""Project original room floor, tabletop, and wall stains onto the fitted level."""
import json,copy,math
import plan_props as P
PROPS=json.loads((P.BASE/'props_plan.json').read_text())['entries']
DEC={a['name']:a for a in json.loads((P.BASE/'source_decals.json').read_text())}
entries=[]
for room in range(1,8):
 rows=[a for a in P.SOURCE if 'Room'+P.SOURCE_ROOM[room] in a['folder'] and 'DecalActor' in a['class']]
 if room in(3,7):rows=[a for a in rows if -300<=a['t']['p'][0]<=700 and a['t']['p'][1]<-2150 and (a['t']['p'][0]>=100)==(room==3)]
 for a in rows:
  t=copy.deepcopy(a['t']);orig=copy.deepcopy(t);t['p']=P.mapcenter(room,t['p'])+[t['p'][2]-800];t['r'][1]+=P.FRAME[room][2]
  role='wall_decal' if abs(t['r'][0])<45 else 'table_decal' if orig['p'][2]>840 else 'floor_decal'
  if role=='table_decal':
   # These three stains belong to the autopsy table / attached sink. Apply the
   # same rigid transform as that furniture, including any later path correction.
   heroes=[e for e in PROPS if e['room']==room and 'AutopsyTable' in e['mesh']]
   if heroes:
    h=heroes[0];src=next(e for e in P.ALL if e['source']==h['source']);ang=h['t']['r'][1]-src['source_t']['r'][1]
    q=P.rot([orig['p'][0]-src['source_t']['p'][0],orig['p'][1]-src['source_t']['p'][1]],ang)
    t['p']=[h['t']['p'][0]+q[0],h['t']['p'][1]+q[1],orig['p'][2]-800];t['r'][1]=orig['r'][1]+ang
  elif role=='floor_decal':
   t['p'][2]=2.0
   bb=DEC[a['name']]['decal_size'];yaw=math.radians(t['r'][1]);ex=abs(math.sin(yaw))*bb[1]*abs(t['s'][1])+abs(math.cos(yaw))*bb[2]*abs(t['s'][2]);ey=abs(math.cos(yaw))*bb[1]*abs(t['s'][1])+abs(math.sin(yaw))*bb[2]*abs(t['s'][2]);l,top,r,bottom=P.ROOMS[room]
   # Projection footprints remain inside each floor region at their source scale.
   if 2*ex<=r-l-8:t['p'][0]=max(l+4+ex,min(r-4-ex,t['p'][0]))
   if 2*ey<=bottom-top-8:t['p'][1]=max(top+4+ey,min(bottom-4-ey,t['p'][1]))
  else:
   if room==3:t['p']=[891,-220,t['p'][2]];t['r'][1]=0
   if room==7:t['p']=[550 if a['name']=='MI_BloodDecal7_75' else 665,449,t['p'][2]];t['r'][1]=90
  entries.append({'room':room,'source':{'actor':a['name']},'t':t,'role':role,'material':DEC[a['name']]['material'],'projection_depth_cm':8,'preserve_source_plane_scale':True})
(P.BASE/'decals_plan.json').write_text(json.dumps({'entries':entries},indent=2))
print(json.dumps({'decals':len(entries),'roles':{r:sum(e['role']==r for e in entries) for r in ['floor_decal','table_decal','wall_decal']}},indent=2))
