# BP_NPCDialogueTrigger_Ready 使用说明

## 功能

玩家进入空的 NPC 对话 Trigger 后：

1. 玩家状态切换为 `Dialogue / 对话`。
2. 屏幕底部显示 NPC 名称和对话文字。
3. 玩家离开 Trigger 后关闭对话UI。
4. 玩家状态恢复为 `Normal / 正常`。

## 手动设置

1. 把 `/Game/CodexDelivery/NPC/BP_NPCDialogueTrigger_Ready` 拖进关卡。
   - 目的：在NPC附近建立对话触发范围；它是空 Actor，不需要模型。
2. 选中关卡里的 Trigger，在 `Details / 细节` 中展开 `NPC Dialogue > Content / NPC对话 > 内容`。
3. 在 `Speaker Name / NPC名称` 填写显示名称。
   - 目的：设置UI中的说话者标题。
4. 在 `Dialogue Text / 对话内容` 填写对话，可输入多行文字。
   - 目的：设置玩家进入范围后看到的正文。
5. 选中 `DialogueZone`，调整 `Box Extent / 盒体范围`，或者直接缩放场景中的 Actor。
   - 目的：决定玩家距离NPC多近时显示对话。

`Dialogue Widget Class / 对话UI类` 已经设置为内置UI，正常情况下不需要修改。它保留为可编辑属性，方便未来替换成美术制作的 Widget Blueprint。

## 测试结果应该是

`进入 Trigger -> Dialogue 状态 -> 显示UI -> 离开 Trigger -> 关闭UI -> Normal 状态`

如果 Trigger 放在玩家出生点上，游戏开始便会立刻显示UI，这是正确的重叠触发行为。
