import unreal as u,json,math
from collections import deque
from pathlib import Path
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox')
actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
obstacles=[]
for a in actors:
    if str(a.get_folder_path())=='01_Walls':
        o,e=a.get_actor_bounds(False)
        if o.z-e.z<180 and o.z+e.z>10:obstacles.append((o.x-e.x-35,o.y-e.y-35,o.x+e.x+35,o.y+e.y+35))
def p(x,y):return ((x-1030)*2,(y-480)*2)
def cell(x,y):return (round(x/10),round(y/10))
def free(c):
    x,y=c[0]*10,c[1]*10
    if not (-1800<x<1800 and -620<y<630):return False
    return not any(a<=x<=c and b<=y<=d for a,b,c,d in obstacles)
start=cell(*p(320,425));seen={start};q=deque([start])
while q:
    x,y=q.popleft()
    for c in [(x+1,y),(x-1,y),(x,y+1),(x,y-1)]:
        if c not in seen and free(c):seen.add(c);q.append(c)
rooms=[(354,268),(847,357),(1267,383),(1688,294),(425,577),(847,666),(1267,603),(1688,603)]
reachable=[cell(*p(x,y)) in seen for x,y in rooms]
assert all(reachable),reachable
assert len([a for a in actors if isinstance(a,u.PlayerStart)])==1
result={'saved_map_reloaded':True,'room_reachability_with_70cm_player_diameter':reachable,'actor_count':len(actors),'validation':'10cm navigation grid against saved wall bounds at player height; runtime movement requires PIE check.'}
Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/whitebox_validation.json').write_text(json.dumps(result,indent=2))
u.log('WHITEBOX_VERIFY_SUCCESS '+json.dumps(result))
