import unreal as u,json
from pathlib import Path
D=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer');L=u.get_editor_subsystem(u.LevelEditorSubsystem);A=u.get_editor_subsystem(u.EditorActorSubsystem)
assert L.load_level('/Game/Asylum/Maps/Showcase')
o=[]
for a in A.get_all_level_actors():
 if not str(a.get_folder_path()).startswith('03_ThirdFloor'):continue
 if isinstance(a,u.DecalActor):
  c=a.decal;v=c.get_editor_property('decal_size');o.append({'name':a.get_name(),'material':c.get_editor_property('decal_material').get_path_name(),'decal_size':[v.x,v.y,v.z],'sort_order':c.get_editor_property('sort_order'),'fade_screen_size':c.get_editor_property('fade_screen_size')})
(D/'source_decals.json').write_text(json.dumps(o,indent=2))
assert L.load_level('/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex')
for a in A.get_all_level_actors():
 if a.get_actor_label().startswith('TF_Ceiling_'):a.set_is_temporarily_hidden_in_editor(True)
