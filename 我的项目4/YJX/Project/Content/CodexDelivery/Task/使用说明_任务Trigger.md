# BP_TaskTrigger_Ready 使用说明

## 功能

玩家进入空的任务 Trigger 后：

1. 玩家状态切换为 `TaskInteraction / 任务交互`。
2. 屏幕右侧显示任务标题、任务说明和提交按键。
3. 玩家按默认的 `F` 键时，先检查是否持有步枪（当前暂时代替钥匙）。
4. 若未持有，UI显示 `尚未持有钥匙`；任务不完成，玩家仍可再次按F。
5. 若已持有，销毁玩家身上的枪组件并重置 `bHasRifle`，UI显示完成提示，触发 `On Task Submitted / 任务已提交` 事件。
6. 提交成功后玩家状态恢复为 `Normal / 正常`。

## 手动设置

1. 把 `/Game/CodexDelivery/Task/BP_TaskTrigger_Ready` 拖进关卡。
   - 目的：在场景中放置任务提交区域；它是空 Actor，不需要模型。
2. 选中关卡里的 Trigger，在 `Details / 细节` 中展开 `Task Trigger > Content / 任务触发器 > 内容`。
3. 设置 `Task ID / 任务ID`，例如 `FindKey_01`。
   - 目的：为每项任务提供稳定且唯一的标识，后续任务管理器可据此判断推进哪项任务。
4. 设置 `Task Title / 任务标题` 和 `Task Description / 任务说明`。
   - 目的：设置玩家进入范围后看到的任务UI文字。
5. 如有需要，修改 `Completion Text / 完成提示`。
   - 目的：设置按F成功提交后的提示文字。
6. `Submit Key / 提交按键` 默认为 `F`。
   - 目的：可以为特殊任务改成其他按键，而不需要改蓝图节点。
7. 在 `Task Trigger > Requirements / 任务触发器 > 条件` 中检查 `Require Rifle As Key / 需要步枪作为钥匙` 已勾选。
   - 目的：把当前场景的枪暂时作为任务钥匙；其他不需要枪的任务可取消勾选。
8. 检查 `Consume Rifle On Submit / 提交时销毁步枪` 已勾选。
   - 目的：提交成功后从玩家身上移除枪模型和枪组件，并清除持枪状态；未成功提交时不会移除。
9. `Missing Key Text / 未持有钥匙提示` 默认为 `尚未持有钥匙`，可自行修改。
   - 目的：设置未满足提交条件时的UI反馈。
10. 调整 `TaskZone` 的 `Box Extent / 盒体范围`，或者缩放关卡中的 Actor。
   - 目的：决定玩家进入多大范围后可以提交任务。

## 规则设置

- `One Shot / 只可完成一次`：默认开启；提交后关闭碰撞，避免重复提交。
- `Close Delay / 完成后关闭延迟`：默认 1.25 秒；让玩家有时间看到完成提示。
- `Task Widget Class / 任务UI类`：已设置为内置UI，正常测试不需要修改；未来可替换成美术制作的 Widget Blueprint。

## 后续推进剧情

选中关卡中的 Trigger，在 `Details / 细节 > Events / 事件` 中找到 `On Task Submitted / 任务已提交`，点击加号即可在关卡蓝图中生成事件。可以从该事件连接开门、播放音效、更新任务管理器或触发下一段剧情。

## 测试结果应该是

未持有枪：`进入 Trigger -> TaskInteraction 状态 -> 显示任务UI -> 按F -> 尚未持有钥匙 -> 任务仍未完成`

拾取枪后：`进入 Trigger -> 按F -> 销毁玩家枪组件并清除持枪状态 -> 完成提示 -> On Task Submitted -> Normal 状态 -> UI关闭`
