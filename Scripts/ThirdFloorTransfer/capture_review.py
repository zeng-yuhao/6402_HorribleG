import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');A=u.get_editor_subsystem(u.EditorActorSubsystem)
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
L.eject_pilot_level_actor();L.editor_set_viewport_realtime(True);L.editor_set_game_view(True);L.editor_invalidate_viewports()
name=(D/'view.txt').read_text().strip();cam=next(a for a in A.get_all_level_actors() if a.get_actor_label()=='TF_View_'+name)
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(name=='Overview')
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(cam.get_actor_location(),cam.get_actor_rotation())
(D/'Review').mkdir(exist_ok=True)
u._thirdfloor_screenshot_task=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(D/'Review'/(name+'_Final'))+'.png',delay=0.0)
L.editor_invalidate_viewports()
