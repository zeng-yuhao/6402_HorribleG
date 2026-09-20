# L_Horror_Floorplan_codex — Showcase 三楼编号迁移

已保存地图：`/Game/HorrorWhitebox/Maps/L_Horror_Floorplan_codex`。

以本次两张编号图为准，855 个原始网格实例及 29 处原始 Decal，逐件保留源网格、材质槽和缩放，按目标空间重新排列组合。

| 用户编号 | Showcase 03_ThirdFloor 来源 |
|---|---|
| 1 | ThirdFloor01Room01 |
| 2 开放手术区 | ThirdFloor01Room04 |
| 3 | ThirdFloor01Room05 上半手术台区域 |
| 4 | ThirdFloor01Room07 |
| 5 档案室 | ThirdFloor01Room02 |
| 6 卫生间 | ThirdFloor01Room06 |
| 7 | ThirdFloor01Room05 下半手术台区域 |
| 8 | ThirdFloor01Room08 |
| 9 | ThirdFloor01Room09 |

布局调整：移除 2 区围墙；3、7 房整体向东平移 100 cm，房间尺寸不变；墙高和天花板改为源三楼的 400 cm，保留 140×220 cm 门洞。8 区安排 3 张原尺寸病床，9 区安排 5 张原尺寸病床及书桌、轮椅、输液架等。部分重复病床、旁听椅和外围楼梯/阳台不搬入，以适配目标空间。档案室保留全部 6 组柜架和 119 个纸箱；卫生间保留 4 组洗手池/镜子、3 个马桶、4 块隔板和 66 段管道。

地面引用对应的 Asylum 木地板、混凝土和地砖材质；6 个区域地板模块使用原破损网格，其下方基础地面降低，周围填充面与原网格不叠面。墙体按几何并集重新分段，墙面饰层、木护墙板、顶线、脚线和门框沿净面重建。材质副本位于 `/Game/HorrorWhitebox/ThirdFloor/Materials`，原 Asylum 材质及 Showcase 地图没有保存修改。

验证：目标地图保存后重载，855 个网格逐项对比位置、旋转、原始缩放、材质槽与网格引用，均通过；无重复网格+变换实例。10 cm 网格、35 cm 角色半径的静态通行检查通过 9 个区域、7 个门口及 4 个走廊目标。Unreal 地图重载 Map Check 为 0 Error / 0 Warning。室内渲染检查了床组、护墙板、地板、洗手池和瓷砖墙。此为编辑器渲染及静态几何检查，未完成完整 PIE 实机逐房走图，也不等于对所有视角动态闪烁的保证。

关卡中的 `TF_Rooms/01` 至 `09` 可分别展开编辑。`TF_Architecture` 为墙、地、饰面；`TF_TransferredDecals` 为贴花；`TF_ReviewCameras` 为检查机位。天花板最后在编辑器中临时隐藏，游戏中可见。

修改前备份：/Users/panjiang/Documents/Unreal Projects/Art_Tech_UE5_6/Saved/Backups/ThirdFloorTransfer/20260920_150227

最终检查数据：`saved_validation.json`、`navigation_qa_report.json`。布置清单：`props_plan.json`、`props_plan_89.json`。原数据：`source.json`、`target.json`。


Latest layout update (2026-09-20): the two marked corridors were widened to 200.6608 cm of finished clearance. Current room bounds, actor snapshots, backup and verification are in `../CorridorWidening/README.md`; this directory retains the transfer-stage source plans.
