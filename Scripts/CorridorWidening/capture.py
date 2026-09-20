import unreal as u
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/CorridorWidening');D.joinpath('Review').mkdir(exist_ok=True)
L=u.get_editor_subsystem(u.LevelEditorSubsystem)
L.eject_pilot_level_actor();L.editor_set_viewport_realtime(True);L.editor_set_game_view(True)
L.editor_invalidate_viewports()
u._corridor_screenshot_task=u.AutomationLibrary.take_high_res_screenshot(1920,1080,str(D/'Review/Overview.png'),delay=0.0)
(D/'capsule_api.txt').write_text(u.SystemLibrary.capsule_trace_single_by_profile.__doc__)
