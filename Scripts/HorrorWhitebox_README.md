# 平面图恐怖场景白盒

关卡：`/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_Whitebox`

在内容浏览器中打开 Content → HorrorWhitebox → Maps，双击关卡，点击 Play 使用现有第一人称模板。

按参考平面图搭建 8 个编号房间、8 个门洞、外墙、走廊及圆柱。7 号房仅经 3 号房进入。无标注尺寸，使用图像像素约 2 cm 的比例：整体约 36.8 × 13.1 m，墙高 300 cm、墙厚 26 cm、门洞净宽 140 cm、净高 220 cm。门洞保留开放通行，未制作交互门、敌人、剧情或音效。

天花板归入 `03_Ceilings (hidden in editor)`，编辑器中临时隐藏，游戏中可见。所有构件可分别选择、移动和调整；墙体、地面、天花板启用 BlockAll 碰撞。出生点在 1 号房南侧走廊，使用原工程 BP_FirstPersonGameMode。加入 19 处点光源和简化灯具。

已保存并重新加载 .umap；基于实际保存墙体边界、10 cm 网格与直径 70 cm 玩家占用空间，检查出生点到 8 个房间中心均连通。此检查不等同于完整 PIE 实机走图；尚未完成实机照明和移动手感验证。

资源全部位于 Content/HorrorWhitebox，原关卡及默认启动地图未改变。build_horror_whitebox.py 是构建记录，再运行时会拒绝覆盖现有地图。whitebox_build_report.json 与 whitebox_validation.json 记录生成和检查结果。
