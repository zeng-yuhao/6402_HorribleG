import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/CorridorWidening');A=u.get_editor_subsystem(u.EditorActorSubsystem);world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
rows=[]
for a in A.get_all_level_actors():
 if isinstance(a,u.PostProcessVolume):
  s=a.get_editor_property('settings'); wb=s.get_editor_property('weighted_blendables')
  rows.append({'name':a.get_name(),'unbound':a.get_editor_property('unbound'),'enabled':a.get_editor_property('enabled'),'blendables':str(wb)})
(D/'postprocess.json').write_text(json.dumps(rows,indent=2))
hit=u.SystemLibrary.capsule_trace_single_by_profile(world,u.Vector(850,-100,100),u.Vector(1020,-100,100),35,90,'Pawn',False,[],u.DrawDebugTrace.NONE,ignore_self=True)
(D/'collision_control.json').write_text(json.dumps({'blocked':hit is not None,'hit':str(hit)},indent=2))
