"""Read-only navigation QA for the proposed furniture and disjoint wall plan.
10 cm grid, 35 cm character radius, obstacle cross-section at Z=30..190.
Uses source mesh corners for entries without precomputed world bounds.
Run with ordinary Python; never connects to Unreal or modifies the plans.
"""
import json,math,itertools,collections,sys
from pathlib import Path
P=Path(__file__).parent
STEP=10.0;RADIUS=35.0
SOLID_PREFIXES=('SM_Bed','SM_Desk','SM_Chair','SM_LeatherChair','SM_LeatherSofa','SM_Locker','SM_MedicalTable','SM_MedicalBed','SM_AutopsyTable','SM_OperatingTable','SM_ToiletBowl','SM_ToiletBooth','SM_Cribs','SM_Reception','SM_WheelChair','SM_TripodDropper','SM_Sink')
def load(name):return json.loads((P/name).read_text())
def bounds(e,source):
 if 'world_bounds' in e:return e['world_bounds']
 b=e.get('mesh_bounds')
 if not b:
  a=source[e['source']['actor']];ci=e['source'].get('component_index');c=a['components'][ci] if ci is not None else next(c for c in a['components'] if c['name']==e['source']['component'])
  b=c['bounds']
 t=e['t'];pitch,yaw,roll=[math.radians(v) for v in t['r']];cp,sp=math.cos(pitch),math.sin(pitch);cy,sy=math.cos(yaw),math.sin(yaw);cr,sr=math.cos(roll),math.sin(roll)
 def rot(q):
  x,y,z=[q[i]*t['s'][i] for i in range(3)];y,z=cr*y+sr*z,-sr*y+cr*z;x,z=cp*x-sp*z,sp*x+cp*z
  return [t['p'][0]+cy*x-sy*y,t['p'][1]+sy*x+cy*y,t['p'][2]+z]
 pts=[rot(q) for q in itertools.product(*zip(*b))]
 return [min(q[i] for q in pts) for i in range(3)]+[max(q[i] for q in pts) for i in range(3)]
def dist_rect(p,b):return math.hypot(max(b[0]-p[0],0,p[0]-b[2]),max(b[1]-p[1],0,p[1]-b[3]))
def main(simulate_group_shift=None,output_name='navigation_qa'):
 arch=load('architecture_report.json');source={a['name']:a for a in load('source.json')};p17=load('props_plan.json');props=p17.get('entries',p17) if isinstance(p17,dict) else p17;props+=load('props_plan_89.json')
 if simulate_group_shift:
  group,dx,dy=simulate_group_shift
  for e in props:
   if e.get('group')!=group:continue
   e['t']['p'][0]+=dx;e['t']['p'][1]+=dy
   if 'world_bounds' in e:
    for k in (0,3):e['world_bounds'][k]+=dx
    for k in (1,4):e['world_bounds'][k]+=dy
 floors=[f['rect'] for f in arch['floor']];wall_obs=[];prop_obs=[]
 for i,w in enumerate(arch['walls']):
  if w[4]>=190 or w[5]<=30:continue
  wall_obs.append({'id':f'wall_{i}','rect':w[:4],'z':w[4:],'kind':'wall'})
 for e in props:
  if e.get('collision') is False:continue
  short=e['mesh'].split('.')[-1]
  if not short.startswith(SOLID_PREFIXES):continue
  b=bounds(e,source)
  if b[2]>=190 or b[5]<=30:continue
  prop_obs.append({'id':e.get('group',e['source']['actor']),'source':e['source'],'mesh':short,'room':e['room'],'rect':[b[0],b[1],b[3],b[4]],'z':[b[2],b[5]],'kind':'furniture'})
 # Wall pieces and furniture are tested as radius-inflated AABBs using circular
 # Minkowski distance, not exaggerated square corner inflation.
 obs=wall_obs+prop_obs;lo=[math.floor(min(f[i] for f in floors)/STEP)*STEP for i in (0,1)];hi=[math.ceil(max(f[i+2] for f in floors)/STEP)*STEP for i in (0,1)]
 nx=int((hi[0]-lo[0])/STEP)+1;ny=int((hi[1]-lo[1])/STEP)+1
 def xy(cell):return [lo[0]+cell[0]*STEP,lo[1]+cell[1]*STEP]
 def floor(p):return any(r[0]<=p[0]<=r[2] and r[1]<=p[1]<=r[3] for r in floors)
 free=set();wallfree=set()
 for ix in range(nx):
  for iy in range(ny):
   p=xy((ix,iy))
   if not floor(p) or any(dist_rect(p,o['rect'])<RADIUS-1e-5 for o in wall_obs):continue
   wallfree.add((ix,iy))
   if not any(dist_rect(p,o['rect'])<RADIUS-1e-5 for o in prop_obs):free.add((ix,iy))
 player=next(a['t']['p'][:2] for a in load('target.json') if 'PlayerStart' in a['class']);start=min(free,key=lambda c:math.dist(xy(c),player))
 def flood(nodes,first):
  seen={first};q=collections.deque([first])
  while q:
   c=q.popleft()
   for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
    d=(c[0]+dx,c[1]+dy)
    if d in nodes and d not in seen:seen.add(d);q.append(d)
  return seen
 reached=flood(free,start);wallstart=min(wallfree,key=lambda c:math.dist(xy(c),player));wallreach=flood(wallfree,wallstart)
 rooms=load('rooms.json');checks=[]
 for name,r in rooms.items():
  candidates=[c for c in free if r[0]+RADIUS<=xy(c)[0]<=r[2]-RADIUS and r[1]+RADIUS<=xy(c)[1]<=r[3]-RADIUS]
  found=[c for c in candidates if c in reached]
  wall_candidates=[c for c in wallreach if r[0]+RADIUS<=xy(c)[0]<=r[2]-RADIUS and r[1]+RADIUS<=xy(c)[1]<=r[3]-RADIUS]
  target=min(found,key=lambda c:math.dist(xy(c),[(r[0]+r[2])/2,(r[1]+r[3])/2])) if found else None
  checks.append({'room':int(name),'reachable':bool(found),'reachable_free_cells':len(found),'total_free_cells':len(candidates),'architecture_alone_reachable':bool(wall_candidates),'sample_reachable_interior':xy(target) if target else None,'reached_bounds':([min(xy(c)[i] for c in found) for i in (0,1)]+[max(xy(c)[i] for c in found) for i in (0,1)]) if found else None})
 doors=[(1,'R1_South',[-1608,-204],[0,-1]),(3,'R3_North',[734,-414],[0,1]),(7,'R3_R7_Shared',[558,26],[0,1]),(4,'R4_South',[1176,-154],[0,-1]),(5,'R5_South',[-1342,414],[0,-1]),(6,'R6_West',[-698,328],[1,0]),(8,'R8_South',[1446,464],[0,-1])]
 door_checks=[]
 for room,label,p,normal in doors:
  target=[p[0]+normal[0]*80,p[1]+normal[1]*80]
  nearby=[c for c in free if math.dist(xy(c),target)<=55]
  targets=[c for c in nearby if c in reached]
  nearby_blockers=[o for o in prop_obs if dist_rect(p,o['rect'])<180]
  door_checks.append({'room':room,'door':label,'center':p,'interior_target':target,'reachable_through_door_area':bool(targets),'nearby_furniture':nearby_blockers})
 hall_targets=[('north_hall',[410,-455]),('west_hall',[180,0]),('south_hall',[510,535]),('east_return',[1740,520])];hall=[]
 for label,p in hall_targets:
  nodes=[c for c in reached if math.dist(xy(c),p)<65];hall.append({'label':label,'target':p,'reachable':bool(nodes)})
 r9=[f['rect'] for f in arch['floor'] if f['room']==9]
 r9free=[c for c in free if any(r[0]<=xy(c)[0]<=r[2] and r[1]<=xy(c)[1]<=r[3] for r in r9)]
 r9found=[c for c in r9free if c in reached]
 checks.append({'room':9,'reachable':all(c['reachable'] for c in hall[:3]),'reachable_free_cells':len(r9found),'total_free_cells':len(r9free),'architecture_alone_reachable':True,'sample_reachable_interior':xy(r9found[0]) if r9found else None,'reached_bounds':([min(xy(c)[i] for c in r9found) for i in (0,1)]+[max(xy(c)[i] for c in r9found) for i in (0,1)]) if r9found else None})
 report={'grid_cm':STEP,'player_radius_cm':RADIUS,'player_start':player,'grid_start':xy(start),'start_adjustment_cm':math.dist(xy(start),player),'wall_obstacles':len(wall_obs),'furniture_obstacles':len(prop_obs),'free_cells':len(free),'reachable_cells':len(reached),'rooms':checks,'doors':door_checks,'hall':hall,'all_rooms_reachable':all(c['reachable'] for c in checks),'all_door_areas_reachable':all(c['reachable_through_door_area'] for c in door_checks),'limitations':['Conservative mesh AABB navigation proxy, not Unreal cooked collision or NavMesh.','Small décor and overhead lamps intentionally ignored; collision:false excluded.','Room success means reaching an empty interior cell, not the furniture-occupied center.']}
 (P/(output_name+'_report.json')).write_text(json.dumps(report,indent=2))
 # SVG gives a compact visual audit of reachable space, walls, furniture, and doors.
 svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{lo[0]} {lo[1]} {hi[0]-lo[0]} {hi[1]-lo[1]}">','<rect x="-2000" y="-1000" width="4200" height="2000" fill="#ece9e4"/>']
 for c in reached:
  x,y=xy(c);svg.append(f'<rect x="{x-5}" y="{y-5}" width="10" height="10" fill="#98d9b3"/>')
 for o in obs:
  a,b,c,d=o['rect'];fill='#363941' if o['kind']=='wall' else '#ac826a';svg.append(f'<rect x="{a}" y="{b}" width="{c-a}" height="{d-b}" fill="{fill}"/>')
 for d in door_checks:
  x,y=d['center'];fill='#176d2d' if d['reachable_through_door_area'] else '#e02222';svg.append(f'<circle cx="{x}" cy="{y}" r="22" fill="{fill}"/><text x="{x+25}" y="{y}" font-size="25">R{d["room"]}</text>')
 svg.append('</svg>');(P/(output_name+'.svg')).write_text(''.join(svg))
 compact={k:report[k] for k in ('all_rooms_reachable','all_door_areas_reachable','start_adjustment_cm','furniture_obstacles')};compact['blocked_rooms']=[c for c in checks if not c['reachable']];compact['blocked_doors']=[c for c in door_checks if not c['reachable_through_door_area']];compact['hall']=hall
 print(json.dumps(compact,indent=2))
if __name__=='__main__':main()
