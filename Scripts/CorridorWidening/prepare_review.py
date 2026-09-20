import unreal as u
from pathlib import Path
A=u.get_editor_subsystem(u.EditorActorSubsystem);L=u.get_editor_subsystem(u.LevelEditorSubsystem)
# Temporarily suppress the user's existing screen-distortion blendable for geometry QA only.
u._corridor_review_pp=[]
for a in A.get_all_level_actors():
 if isinstance(a,u.PostProcessVolume) and a.get_name()=='PostProcessVolume_0':
  u._corridor_review_pp.append((a,a.get_editor_property('enabled')));a.set_editor_property('enabled',False)
L.editor_set_game_view(True);L.editor_invalidate_viewports()
