import unreal as u,json,inspect,datetime
from pathlib import Path
P=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6');D=P/'Scripts/CorridorWidening';OLD=P/'Scripts/ThirdFloorTransfer'
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
restored=[]
for a,enabled in getattr(u,'_corridor_review_pp',[]):
 a.set_editor_property('enabled',enabled);restored.append({'actor':a.get_name(),'enabled':enabled})
u._corridor_review_pp=[];u._corridor_screenshot_task=None
for a in A.get_all_level_actors():
 if str(a.get_folder_path())=='TF_Architecture/Ceilings':a.set_is_temporarily_hidden_in_editor(True)
A.set_selected_level_actors([]);L.editor_set_game_view(False);L.editor_set_viewport_realtime(True);L.editor_invalidate_viewports()
assert L.save_current_level()
assert json.loads((D/'validation.json').read_text())['all_passed']
assert all(not r['blocked'] for r in json.loads((D/'collision_checks.json').read_text()))
assert json.loads((D/'collision_control.json').read_text())['blocked']
g=inspect.currentframe().f_back.f_globals
stopped=False
if '_transfer_handle' in g:
 u.unregister_slate_post_tick_callback(g['_transfer_handle']);stopped=True
(OLD/'job.json').unlink(missing_ok=True)
(D/'session_closed.json').write_text(json.dumps({'saved':True,'local_job_dispatch_stopped':stopped,'restored_postprocess':restored,'completed':datetime.datetime.now().isoformat()},indent=2))
