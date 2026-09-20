import unreal as u,json,inspect
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
L.eject_pilot_level_actor();L.editor_set_game_view(False)
u._thirdfloor_screenshot_task=None
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True)
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,2550),u.Rotator(pitch=-90,yaw=-90,roll=0))
L.editor_invalidate_viewports();assert L.save_current_level()
g=inspect.currentframe().f_back.f_globals;stopped=False
if '_transfer_handle' in g:u.unregister_slate_post_tick_callback(g['_transfer_handle']);stopped=True
(D/'session_closed.json').write_text(json.dumps({'local_job_dispatch_stopped':stopped,'map_saved':True,'final_overview':'Review/Overview_Final.png','surgery_review':'Review/Surgery_Final.png'}))
(D/'job.json').unlink(missing_ok=True)
