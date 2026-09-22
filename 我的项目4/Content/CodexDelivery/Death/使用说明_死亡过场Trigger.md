# BP_DeathCutsceneTrigger_Ready 使用说明

## 功能

玩家进入触发区域后，依次执行：

1. 玩家状态切换为 `Cutscene / 过场`。
2. 播放指定的 `Level Sequence Actor / 关卡序列Actor`。
3. 序列播放结束后，玩家状态切换为 `Dead / 死亡`。
4. 调用 `BP_FirstPersonPlayerController` 中的 `RequestRespawn请求重生`。
5. 玩家在当前 Checkpoint 重生，并由 PlayerController 恢复为 `Normal / 正常` 状态。

## 手动设置

1. 把 `/Game/CodexDelivery/Death/BP_DeathCutsceneTrigger_Ready` 拖入关卡。
   - 目的：在场景中放置死亡区域。
2. 在关卡中放置或选中用于死亡演出的 `Level Sequence Actor / 关卡序列Actor`，关闭 `Auto Play / 自动播放`。
   - 目的：让死亡 Trigger 决定何时开始播放，而不是进入关卡时自动播放。
3. 选中关卡里的 `BP_DeathCutsceneTrigger_Ready`，在 `Details / 细节` 面板找到 `Death Trigger > Cutscene / 死亡触发器 > 过场`。
4. 把关卡里的 Level Sequence Actor 指定给 `Death Sequence Actor / 死亡过场序列Actor`。
   - 目的：告诉 Trigger 播放哪一段死亡过场。
5. 调整 `DeathZone` 的 Box Extent，或直接缩放关卡中的 Trigger Actor。
   - 目的：设置玩家进入多大范围时触发死亡。

如果没有指定 Sequence Actor，Trigger 会等待 `Fallback Duration / 备用时长`（默认 3 秒）后继续死亡与重生流程，方便先测试逻辑。

## 导入其他 UE 5.3 Windows 项目

蓝图依赖本项目插件中的已编译父类。迁移时必须同时复制：

- `Plugins/HorrorTriggerPack`
- `Content/CodexDelivery/Death/BP_DeathCutsceneTrigger_Ready.uasset`

复制时关闭两个 UE 编辑器；在目标项目中启用 `HorrorTriggerPack` 后再打开蓝图。
