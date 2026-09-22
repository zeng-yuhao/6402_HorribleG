# YJX：使用组员的 BP_Key 作为任务钥匙

目标关卡：`/Game/FirstPerson/Lvl_FirstPerson`。现有钥匙：`/Game/YYN/Blueprint_YYN/BP_Key`。任务区域：`/Game/CodexDelivery/Task/BP_TaskTrigger_Ready`。

本阶段不再依赖 `BP_Pickup_Rifle`：当前枪无法由组员角色拾取，任务提交不查询步枪组件，也不会销毁步枪。组员的 `BP_Key` 和 `BP_Door` 蓝图未被修改。控制器上的 `HPKeyInventoryComponent / 钥匙持有记录组件` 现在直接监听 `BP_Key` 的 `Sphere / 球形碰撞` 与玩家重叠，记录 `YYN_Key`；钥匙 Actor 的销毁事件是后备识别。组件每 0.5 秒检查后来加载的钥匙 Actor，以适配 World Partition / 世界分区。记录保存在 PlayerController 上，因此角色死亡重生后仍保持，直到提交任务消耗。

任务默认设置：`Require BP Key / 需要 BP_Key 钥匙 = True`、`Consume Key On Submit / 提交时消耗钥匙 = True`、`Required Key ID / 需要的钥匙ID = YYN_Key`。已只读核对 `/Game/FirstPerson/Lvl_FirstPerson` 内现有任务实例，这三项都正确，通常无需再设置。

测试顺序：

1. 进入任务区域，在尚未碰到钥匙前按 F。目的：验证未持有分支；预期显示“尚未持有钥匙”，任务不完成。
2. 走到关卡现有 `BP_Key` 所在位置，确认世界里的钥匙消失。目的：验证组员原有拾取事件；同时新组件会在玩家与钥匙的 Sphere 重叠时记录已持有。
3. 回到任务区域按 F。目的：验证已持有分支；预期显示提交成功，钥匙持有记录被消耗。钥匙世界 Actor 在第 2 步已由组员蓝图销毁，不会在提交时再次销毁。

如果仍未成功，请打开 `Output Log / 输出日志`，依次搜索 `YJX key inventory active`、`YJX watching BP_Key actor`、`YJX key acquired`。目的：区分组件未启动、钥匙 Actor 未被发现、碰撞未授予三种问题。`Pickup Max Distance / 拾取最大距离`（默认 250 cm）只限制“销毁事件”后备识别；它不影响 Sphere 重叠识别。不要直接改 `BP_Key` 的开门蓝图。
