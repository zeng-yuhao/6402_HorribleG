import unreal as u,json
from pathlib import Path
p=Path('/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Scripts/ThirdFloorTransfer')
o={}
for n in ['GeometryScript_AssetUtils','GeometryScript_Primitives','DynamicMesh','GeometryScript_MeshTransforms','EditorAssetLibrary','AssetImportTask','FbxImportUI']:
 c=getattr(u,n,None);o[n]=[x for x in dir(c) if not x.startswith('_')] if c else None
for n in ['MI_Floor01_1','MI_Floor02_1','MI_Floor03_4','MI_FloorConcrete01','MI_Wall02_5','MI_WallTile01_4']:
 m=u.load_asset('/Game/Asylum/Materials/Building/'+n);o[n]={'parent':m.parent.get_path_name(),'scalars':str(m.get_editor_property('scalar_parameter_values')),'vectors':str(m.get_editor_property('vector_parameter_values'))}
(p/'api.json').write_text(json.dumps(o,indent=2))
