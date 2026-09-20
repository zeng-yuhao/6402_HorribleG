# Whitebox1 — Asylum 场景改造

关卡：/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox1

已直接引用工程内 Asylum 资产：旧墙体、瓷砖、护墙板、破损地面、吊灯、接待台、桌椅柜、铁架病床、床垫、输液架、医疗推车、手术台、解剖台及污渍贴花。房间用途依次为候诊接待、病房、诊疗室、办公室、储藏室、隔离病房、恢复观察室和解剖清洗室。

保留原平面布局和门洞；7 号房仍经 3 号房进入。使用已有第一人称 GameMode 和出生点。门保持开放，未添加新的门交互、AI、音效或剧情。场景由可编辑的独立构件组成，Asylum 内容包中的原始资源和示例地图未修改。

验证：重新加载保存后的地图；按墙体及阻挡家具的实际边界，以 10 cm 网格和直径 70 cm 的玩家空间检查，8 个房间中心均可从出生点到达。此为几何检查，不等同于完整实机试玩。已配置 4 个 AS_View_ 摄像机供检查。

修改前地图备份：/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Saved/Backups/AsylumRestyle/20260913_172825/L_Horror_Floorplan_Whitebox1.umap

引用资产：

- /Game/Asylum/Materials/Building/MI_Border01
- /Game/Asylum/Materials/Building/MI_Floor03_2
- /Game/Asylum/Materials/Building/MI_FloorConcrete01
- /Game/Asylum/Materials/Building/MI_Wall02_1
- /Game/Asylum/Materials/Building/MI_Wall02_3
- /Game/Asylum/Materials/Building/MI_WallTile02_1
- /Game/Asylum/Materials/Decals/MI_Dirt01_1
- /Game/Asylum/Meshes/Building/Borders/SM_Border01_2.SM_Border01_2
- /Game/Asylum/Meshes/Building/Floors/SM_Floor01_1.SM_Floor01_1
- /Game/Asylum/Meshes/Building/Walls/SM_Wall01.SM_Wall01
- /Game/Asylum/Meshes/Props/Furniture/SM_Desk01_1.SM_Desk01_1
- /Game/Asylum/Meshes/Props/Furniture/SM_Locker01_1.SM_Locker01_1
- /Game/Asylum/Meshes/Props/Furniture/SM_ReceptionDesk01_1.SM_ReceptionDesk01_1
- /Game/Asylum/Meshes/Props/SM_AutopsyTable01.SM_AutopsyTable01
- /Game/Asylum/Meshes/Props/SM_Basin01.SM_Basin01
- /Game/Asylum/Meshes/Props/SM_Bed01_1.SM_Bed01_1
- /Game/Asylum/Meshes/Props/SM_Bed01_3.SM_Bed01_3
- /Game/Asylum/Meshes/Props/SM_Book01_1.SM_Book01_1
- /Game/Asylum/Meshes/Props/SM_Book01_3.SM_Book01_3
- /Game/Asylum/Meshes/Props/SM_Box01_1.SM_Box01_1
- /Game/Asylum/Meshes/Props/SM_Chair01.SM_Chair01
- /Game/Asylum/Meshes/Props/SM_Lamp01_1.SM_Lamp01_1
- /Game/Asylum/Meshes/Props/SM_Mattress01_1.SM_Mattress01_1
- /Game/Asylum/Meshes/Props/SM_MedicalInstrument01_1.SM_MedicalInstrument01_1
- /Game/Asylum/Meshes/Props/SM_MedicalTable01.SM_MedicalTable01
- /Game/Asylum/Meshes/Props/SM_OperatingTable01.SM_OperatingTable01
- /Game/Asylum/Meshes/Props/SM_TableClock01.SM_TableClock01
- /Game/Asylum/Meshes/Props/SM_TripodDropper01.SM_TripodDropper01
