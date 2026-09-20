import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/CorridorWidening');world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
paths=[('horizontal_center',[-1600,-151,100],[-790,-151,100]),('vertical_center',[1031,-520,100],[1031,535,100]),('vertical_west_lane',[991,-520,100],[991,535,100]),('vertical_east_lane',[1071,-520,100],[1071,535,100])]
rows=[]
for label,start,end in paths:
 hit=u.SystemLibrary.capsule_trace_single_by_profile(world,u.Vector(*start),u.Vector(*end),35,90,'Pawn',False,[],u.DrawDebugTrace.NONE,ignore_self=True)
 row={'label':label,'start':start,'end':end,'radius_cm':35,'half_height_cm':90,'blocked':hit is not None}
 if hit is not None:row['hit']=str(hit)
 rows.append(row)
(D/'collision_checks.json').write_text(json.dumps(rows,indent=2))
# The reference view was captured with editor game view off; use the same mode.
L=u.get_editor_subsystem(u.LevelEditorSubsystem);L.editor_set_game_view(False);L.editor_invalidate_viewports()
