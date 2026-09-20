import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
u._thirdfloor_screenshot_task=None
u.SystemLibrary.collect_garbage()
L.eject_pilot_level_actor()
L.load_level('/Game/FirstPerson/Lvl_FirstPerson')
assert L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex')
L.editor_set_viewport_realtime(True);L.editor_set_game_view(False)
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True)
A.set_selected_level_actors([])
u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(u.Vector(0,0,2550),u.Rotator(pitch=-90,yaw=-90,roll=0))
L.editor_invalidate_viewports()
(D/'final_editor.json').write_text(json.dumps({'actors':len(A.get_all_level_actors()),'world':u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world().get_name(),'screenshots_available':['Ward08.png','Bathroom.png']}))
