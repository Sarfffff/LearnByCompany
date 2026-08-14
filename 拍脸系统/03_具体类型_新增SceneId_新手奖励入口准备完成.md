# 具体类型：新增 SceneId——新手奖励入口准备完成

> 本文参照 iWiki《如何新增一个拍脸活动》的步骤式结构，记录“新手奖励入口首次准备完成”这一具体实例。
>
> **当前状态（已按本地文件核验）**
>
> - `PushFaceModel.lua`：已实现 `_isNoviceRewardEntryReady`、`_hasTriggeredNoviceRewardEntryReady`、`_isNoviceRewardEntryTriggering`、`_pushFaceSceneGeneration` 四项状态，以及 `OnNoviceRewardEntryReady()`、`CheckNoviceRewardReady()`；generation 在 `OnInit()` 基于旧值加一，跨 `OnReset()` 保持单调递增。
> - `GetSceneIdByKey()`：缓存命中时直接返回；未命中时会强制重建一次 Scene 配置缓存并再查一次。
> - `TriggerPushFaceListBySceneId()`：已支持可选 `CompletionCallback(success, hasSceneConfig)`，并用 generation 阻止切换场景或 Reset 后的过期异步回写；新手奖励入口只有在加载及收集流程有效、且目标 Scene 存在原始拍脸配置时才消费一次触发。原始配置即使全部被 `NeedShow=false` 过滤，也仍算完成收集并消费。
> - `UI_ActivityIcon_NoviceReward.lua`：`RefreshNoviceRewardBtn()` 创建或刷新入口后，只要 `newbieRightUpView` 有效就通知 Model，由 Model 统一去重。
> - `PushFace_NoviceRewardEntryReadyLocalTest.lua`：本地教学 Item 已存在。
> - `PushFaceData_Total_pbin_check.py`：已适配 Scene 19 / `CheckNoviceRewardReady`，固定 id→sceneKey、id→checkFunc；`REQUIRED_SCENE_IDS` 强制 id 15 空占位行必须存在，并要求其 `sceneKey`、`checkFunc` 均为空。
> - `P_拍脸.xlsx`：当前仍没有 SceneId `19`、`NoviceRewardEntryReady`、`CheckNoviceRewardReady` 或拍脸内容 `1000129`。
> - 当前导出产物 `PushFaceSceneData`、`PushFaceData_Total` 也没有上述新配置，因此现状下虽然 Lua、View、Item 和校验器已经落地，**运行仍不能命中新拍脸**。
> - 当前剩余工作是人工基于最新 Excel 全表查重并填入 Scene 19 / 内容 1000129，再执行 `Compile → Pbin`。
>
> 本文只同步当前实际实现与未完成项；不在本文档修改过程中改动 Lua、XLSX、TXT、Pbin 或校验脚本。

---

## 0. 先判断属于哪种新增

新增拍脸前，先判断需求属于以下哪一类：

```text
新增拍脸内容
├─ 触发时机可由已有 Scene 精确表达
│  └─ 复用旧 SceneId，只新增“拍脸内容”与对应 Item
└─ 触发时机是新的、不可由已有 Scene 精确表达
   └─ 新增 SceneData + 新增拍脸内容 + 接入新的触发点/检查函数
```

### 0.1 为什么本例不能用旧 SceneId 精确表达

现有 Scene 主要表达登录完成、回到大厅、停留大厅、进入玩法、手动触发等通用时机。例如：

- `LoginDone`：登录后的大厅拍脸；
- `BackToLobby`：回到大厅；
- `WaitInLobby`：停留在大厅；
- `Manual`：手动场景；
- `DsConnect`：大厅 DS 首次连接成功。

这些 Scene 最多只能说明“玩家位于某个大厅阶段”，不能证明：

1. `UI_ActivityIcon_NoviceReward` 当前可见；
2. `UI_Lobby_RightUp_NewBieReward` 已经通过 `AddView(...)` 创建出有效实例；
3. 新手奖励入口已经具备被用户看到和使用的条件；
4. 这是该 Model 生命周期中的**首次入口准备完成**。

如果把本例挂到 `LoginDone` 或 `WaitInLobby`，拍脸收集可能早于入口子 View 创建；如果挂到点击函数，则触发语义变成“用户点击入口”，已经不是“入口首次准备完成”。因此本例属于**新增具体触发场景**，需要独立的 SceneData：

```text
sceneKey = NoviceRewardEntryReady
checkFunc = CheckNoviceRewardReady
```

### 0.2 何时应该复用旧 Scene

满足下列条件时应优先复用旧 Scene，而不是继续增加 SceneId：

- 业务只要求“登录完成后”“回到大厅后”“进入某玩法后”等已有时机；
- 新拍脸与旧 Scene 的触发源、可展示环境和重试语义一致；
- 差异仅是活动资格、时间、等级、平台或业务开关，可由拍脸内容配置及 Item 的 `NeedShow` 判断完成；
- 不需要等待某个具体 UI 实例、数据请求或资源节点准备完成。

判断原则是：**Scene 表达触发时机和展示环境，Item 表达具体活动是否应该展示。** 不要仅因为新增了一个活动就新增 Scene，也不要为了省一个 SceneId 而把精确的 UI 生命周期事件塞进宽泛旧 Scene。

---

## 1. 本实例目标与变更清单

### 1.1 目标

当新手奖励入口的子 View 创建或刷新后，只要实例有效就通知 `PushFaceModel`；Model 负责并发去重，并在新 Scene 异步收集成功后消费一次触发机会，最终由本地教学拍脸打开：

```lua
_MOE.WindowName.UI_NoviceReward_MainView
```

### 1.2 变更清单与当前落地状态

| 层级 | 文件/对象 | 目标改动 | 当前状态 |
|---|---|---|---|
| Scene 配置 | `letsgo_common/excel/xls/P_拍脸.xlsx` → `拍脸SceneId` | 暂定新增 `id=19` | **未填表** |
| 拍脸内容 | 同一 Excel → `拍脸内容` | 暂定新增 `id=1000129` | **未填表** |
| Model | `LetsGo/Content/LetsGo/Script/PushFace/PushFaceModel.lua` | 四项状态、通知/检查函数、完成回调与 generation 保护 | **已实现** |
| View | `LetsGo/Content/Feature/System/Script/System/Lobby/LobbyRightUp/ActivityIcon/UI_ActivityIcon_NoviceReward.lua` | 创建或刷新后，实例有效即通知 Model | **已实现** |
| Item | `LetsGo/Content/LetsGo/Script/PushFace/Items/PushFace_NoviceRewardEntryReadyLocalTest.lua` | 本地教学 `NeedShow/HandleShow` | **已实现，仅限本地教学** |
| Pbin 校验 | `letsgo_common/excel/pb_checker/PushFaceData_Total_pbin_check.py` | 允许新检查函数并锁定 Scene 语义映射 | **已实现** |
| 导表产物 | `PushFaceSceneData`、`PushFaceData_Total` | 生成包含新配置的 TXT/Pbin | **未生成** |

> 注意：代码与校验器存在不等于配置已经生效。当前 `PushFaceModel:GetSceneIdByKey("NoviceRewardEntryReady")` 首次从缓存未命中后会强制重建一次 Scene 配置缓存，但由于 XLSX 与导出产物仍无该行，第二次查询仍查不到 SceneId，通知函数会记录 warning 后返回；本次不消费触发机会，View 后续刷新仍可再次通知。

---

## 2. Step 1：在 `拍脸SceneId` 新增 SceneData

目标工作表：

```text
letsgo_common/excel/xls/P_拍脸.xlsx
└─ 拍脸SceneId
```

本地暂定值：

| 字段 | 暂定值 | 含义 |
|---|---:|---|
| `id` | `19` | Scene 数字 ID |
| `sceneKey` | `NoviceRewardEntryReady` | Lua 侧按语义查找 SceneId 的 Key |
| `checkFunc` | `CheckNoviceRewardReady` | `PushFaceModel` 上实际存在的检查函数名 |
| 说明备注 | 建议写“新手奖励入口首次准备完成” | 仅用于维护者理解 |

### 2.1 必须先做 Excel 全表查重

`19` 只是当前工作副本中的本地暂定值，不可因为现有导出 TXT 最大为 `18` 就直接认定可用。填表前必须基于最新 Excel 做全表查重：

- `id=19` 不得重复；
- `sceneKey=NoviceRewardEntryReady` 不得重复；
- `checkFunc=CheckNoviceRewardReady` 应与真实 Lua 函数完全同名；
- 不得复用历史保留空缺 `id=15`；
- 同步或合并他人近期配置后必须再次查重。

当前本地文件的只读核验结果是：

```text
拍脸SceneId：已有有效语义配置到 id=18，id=15 为历史保留空缺；未发现 id=19。
```

这只说明当前工作副本没有冲突，**不能替代正式填表时对最新 Excel 的人工全表查重**。

### 2.2 校验器已适配 Scene 19

`PushFaceData_Total_pbin_check.py` 已完成本例所需适配：

```text
SceneId 19
├─ EXPECTED_SCENE_KEY_BY_ID[19]
│  └─ "NoviceRewardEntryReady"
├─ EXPECTED_CHECK_FUNC_BY_ID[19]
│  └─ "CheckNoviceRewardReady"
└─ VALID_CHECK_FUNCS
   └─ 包含 "CheckNoviceRewardReady"
```

校验器会同时固定两组历史语义映射：

1. `id → sceneKey`：Scene 19 只能对应 `NoviceRewardEntryReady`；
2. `id → checkFunc`：Scene 19 只能对应 `CheckNoviceRewardReady`。

id 15 的规则也已明确收紧。最终代码不只是“出现时必须为空”，还通过必需 ID 集合强制该占位行必须存在：

```python
# 必须保留所有受保护 SceneId，包括历史空占位 15
REQUIRED_SCENE_IDS = set(EXPECTED_SCENE_KEY_BY_ID) | {15}
```

```text
id = 15
├─ 必须作为一行存在，否则命中 missing_scene_ids 报错
├─ sceneKey 为空
├─ checkFunc 为空
└─ 仅允许作为完全空的历史占位，不允许复用
```

遍历结束后校验器执行 `REQUIRED_SCENE_IDS - scene_id_set`；因此删除 id 15 空行和复用 id 15 都会失败。校验器适配已经完成，不构成当前阻塞。当前真正未完成的是 XLSX 填入 Scene 19 / 内容 1000129，以及随后执行 `Compile → Pbin`。

---

## 3. Step 2：在 `拍脸内容` 新增配置

目标工作表：

```text
letsgo_common/excel/xls/P_拍脸.xlsx
└─ 拍脸内容
```

本地暂定配置：

| 字段 | 暂定值 | 说明 |
|---|---:|---|
| `id` | `1000129` | 新配置 ID；必须全表查重 |
| `sortId` | `0` | 本地教学排序值 |
| `codeName` | `NoviceRewardEntryReadyLocalTest` | 对应 Item 文件名后缀 |
| `fequency` | `1` | 总是；仅用于当前本地教学 |
| `open` | `true` | 开启 |
| `needLevel` | `1` | 最低等级 1 |
| `sceneIds` | `19` | 只绑定新 Scene |
| `featureName` | 空 | 使用主玩法默认 Item 路径 |

`featureName` 为空时，`PushFaceModel:_getConfigBasePath()` 使用：

```lua
local DefaultConfigPath = "LetsGo.Script.PushFace.Items"
```

最终动态加载路径为：

```text
LetsGo.Script.PushFace.Items.PushFace_NoviceRewardEntryReadyLocalTest
```

对应真实文件：

```text
LetsGo/Content/LetsGo/Script/PushFace/Items/
└─ PushFace_NoviceRewardEntryReadyLocalTest.lua
```

### 3.1 不可复用已有 `1000128`

当前 Excel 与已导出的 `PushFaceData_Total.txt` 中已经存在：

```text
id        = 1000128
sortId    = 0
codeName  = NoviceRewardLocalTest
fequency  = 1
open      = true
needLevel = 1
sceneIds  = 1
```

它绑定的是旧的 `LoginDone` 场景（SceneId 1），并加载：

```text
PushFace_NoviceRewardLocalTest.lua
```

若直接把 `1000128` 改为本例配置，会覆盖已有本地测试项的身份与语义，也会让旧配置、缓存记录和排查结果混在一起。因此本例使用独立暂定 ID `1000129`，**不可复用或覆盖 1000128**。

同样，`1000129` 也必须在最新 Excel 中全表查重，不能只根据“1000128 是当前末尾值”推断它一定可用。

### 3.2 未导表就不算生效

把值写进说明文档、Lua 注释，甚至只写进 Excel，都不代表运行时已经加载。只有人工填表并完成 `Compile → Pbin`，且运行环境加载了新的 `PushFaceSceneData.pbin` 与 `PushFaceData_Total.pbin` 后，这些值才可视为配置生效。

当前本地实际状态仍是：

```text
SceneData 19：不存在
拍脸内容 1000129：不存在
新 Item Lua：存在
```

---

## 4. Step 3：`PushFaceModel` 已实际实现

文件：

```text
LetsGo/Content/LetsGo/Script/PushFace/PushFaceModel.lua
```

### 4.1 `OnInit()` 中的四项状态

真实代码：

```lua
self._isNoviceRewardEntryReady = false
self._hasTriggeredNoviceRewardEntryReady = false
self._isNoviceRewardEntryTriggering = false
self._pushFaceSceneGeneration = (self._pushFaceSceneGeneration or 0) + 1
```

职责不同：

- `_isNoviceRewardEntryReady`：Scene 检查条件，表示入口实例已经准备完成；
- `_hasTriggeredNoviceRewardEntryReady`：完成闸门，只在回调满足 `success and hasSceneConfig` 后置为 `true`；
- `_isNoviceRewardEntryTriggering`：并发闸门，异步收集期间阻止 View 多次刷新造成重复请求；
- `_pushFaceSceneGeneration`：场景世代号，用于识别并拒绝场景切换或 Reset 前发起的过期异步回调。

`OnInit()` 不把 generation 重置为 `0`，而是读取旧值后加一。首次初始化时旧值为空，因此从 `1` 开始；`OnReset()` 重新执行 `OnInit()` 时继续在旧值上加一，generation 跨 Reset 单调递增。这样 Reset 前发起但尚未返回的异步请求也会失效，不会因 generation 回退或复用而误写回。

`OnReset()` 同时会把 ready、triggering、hasTriggered 三项业务状态重置，因此“一次触发”的业务闸门仍以当前 Reset 周期为边界，而不是永久账号状态。`OnPreSwitchScene()` 也会递增 `_pushFaceSceneGeneration`，使旧场景中尚未返回的异步请求失效。

### 4.2 通知入口 `OnNoviceRewardEntryReady()`

真实代码：

```lua
---新手奖励入口准备完成时触发本地教学拍脸
function PushFaceModel:OnNoviceRewardEntryReady()
    local sceneId = self:GetSceneIdByKey("NoviceRewardEntryReady")
    if not sceneId then
        _MOE.Logger.LogWarning("PushFaceModel:OnNoviceRewardEntryReady scene config not found, sceneKey=NoviceRewardEntryReady")
        return
    end
    if self._hasTriggeredNoviceRewardEntryReady or self._isNoviceRewardEntryTriggering then
        return
    end

    self._isNoviceRewardEntryReady = true
    self._isNoviceRewardEntryTriggering = true
    self:TriggerPushFaceListBySceneId(sceneId, false, function(success, hasSceneConfig)
        if success and hasSceneConfig then
            self._hasTriggeredNoviceRewardEntryReady = true
        end
        self._isNoviceRewardEntryTriggering = false
    end)
end
```

关键分析：

1. 通过 `GetSceneIdByKey()` 从 `PushFaceSceneData` 动态取得数字 ID，没有在 Lua 中硬编码 `19`；
2. `GetSceneIdByKey()` 在缓存未命中时会调用一次 `InitSceneIdConfig()` 重建 Scene 配置缓存，再查询一次；只有刷新后仍未命中才返回 `nil`；
3. Scene 配置最终仍不存在时 warning 并返回，既不会误触发其他 Scene，也不会消费一次触发机会；
4. 已完成触发或当前正在触发时直接返回，由 Model 统一承接 View 的重复通知；
5. 调用期间先设置 ready 与 triggering，但 `_hasTriggeredNoviceRewardEntryReady` 只在 `success and hasSceneConfig` 时置为 `true`；
6. `success` 表示配置加载回调有效、generation 未过期且收集流程已经执行；`hasSceneConfig` 表示目标 Scene 的原始拍脸配置列表非空；
7. `(false, false)` 或 `(true, false)` 都会清除 triggering 而不消费完成闸门，因此 View 后续刷新可以重试；
8. 若原始列表非空，即使其中全部条目被前置条件或 `NeedShow=false` 过滤、最终队列为空，回调仍为 `(true, true)`，并消费一次触发；这是“完成收集”而不是“保证展示”；
9. `TriggerPushFaceListBySceneId(sceneId, false, CompletionCallback)` 不清空其他 Scene 队列，并把双维度异步收集结果回传给通知入口。

### 4.3 `TriggerPushFaceListBySceneId()` 的完成回调与 generation 保护

函数签名已扩展为：

```lua
function PushFaceModel:TriggerPushFaceListBySceneId(SceneId, ClearOtherList, CompletionCallback)
```

`CompletionCallback` 是可选参数，现有调用方不传时保持原行为；传入时接收两个布尔值：

```lua
---@param CompletionCallback fun(success:boolean, hasSceneConfig:boolean)|nil
```

- `success`：配置加载回调有效、generation 未过期，并已执行收集流程；它不表示最终队列非空，也不表示窗口实际展示；
- `hasSceneConfig`：在过滤前直接读取目标 Scene 的原始拍脸配置列表，判断该列表是否非空。

失败与完成路径如下：

```text
TriggerPushFaceListBySceneId(...)
├─ Scene 配置未初始化 -> CompletionCallback(false, false)
├─ SceneId 非法 -> CompletionCallback(false, false)
└─ LoadWebConfig 异步回调
   ├─ generation 已变化
   │  ├─ 不写回 m_PushFaceListMap
   │  └─ CompletionCallback(false, false)
   └─ generation 未变化
      ├─ 读取 RawConfigList
      ├─ hasSceneConfig = RawConfigList 非空
      ├─ CollectPushFaceListBySceneId(...)
      ├─ 写入队列并 TryShowNextAutoShowWindow()
      └─ CompletionCallback(true, hasSceneConfig)
```

发起异步加载时会捕获当前 generation，并在收集前检查：

```lua
local sceneGeneration = self._pushFaceSceneGeneration
_MOE.Tables.PushFaceTable.LoadWebConfig(function()
    if self._pushFaceSceneGeneration ~= sceneGeneration then
        if CompletionCallback then
            CompletionCallback(false, false)
        end
        return
    end

    local RawConfigList = _MOE.Tables.PushFaceTable.GetPushfaceConfigBySceneId(SceneId)
    local hasSceneConfig = RawConfigList and next(RawConfigList) ~= nil or false
    local PushFaceList = self:CollectPushFaceListBySceneId(SceneId, ClearOtherList)
    self.m_PushFaceListMap[SceneId] = PushFaceList
    self:TryShowNextAutoShowWindow()
    if CompletionCallback then
        CompletionCallback(true, hasSceneConfig)
    end
end)
```

这里的完成语义以“原始配置存在且收集流程有效”为边界。`NeedShow=false`、前置条件不通过或频率限制会让某条配置不入最终队列，但不会把已经存在的 `RawConfigList` 变为空；因此目标 Scene 有原始配置时，即使最终 `PushFaceList` 为空，也会回调 `(true, true)`。新手奖励入口据此消费一次触发，避免把“业务判断不展示”误当成可无限重试的技术失败。

`OnInit()`（包括由 `OnReset()` 调用）与 `OnPreSwitchScene()` 都会递增 generation。这样 Reset 前或旧场景的迟到回调无法把队列重新写回；对新手奖励入口而言，该路径返回 `(false, false)`，清除 triggering，并保留后续刷新重试机会。

### 4.4 Scene 检查函数 `CheckNoviceRewardReady()`

真实代码：

```lua
---检查新手奖励入口准备完成拍脸场景
---@return boolean 是否满足展示条件
function PushFaceModel:CheckNoviceRewardReady()
    if not self._isNoviceRewardEntryReady then
        _MOE.Logger.Log("PushFaceModel:CheckNoviceRewardReady", "Entry is not ready")
        return false
    end
    if not _MOE.SceneManager:IsInShowLobbyPushScene() then
        _MOE.Logger.Log("PushFaceModel:CheckNoviceRewardReady", "Not in lobby")
        return false
    end
    return _MOE.UIManager:IsOnLobbyViewWithNoDefaultWindowVisible()
end
```

它同时约束三件事：

```text
入口已准备完成
AND 当前属于允许大厅拍脸的场景
AND 大厅没有不允许的默认层界面遮挡
```

SceneData 的 `checkFunc` 必须精确填写 `CheckNoviceRewardReady`。初始化 Scene 配置时，`PushFaceModel:_isValidSceneConfigRow()` 还会检查 `self[checkFunc]` 是否确实是函数；拼写错误会导致该 Scene 行不进入缓存。

---

## 5. Step 4：View 触发点已实际接入

文件：

```text
LetsGo/Content/Feature/System/Script/System/Lobby/LobbyRightUp/ActivityIcon/
└─ UI_ActivityIcon_NoviceReward.lua
```

真实代码：

```lua
function UI_ActivityIcon_NoviceReward:RefreshNoviceRewardBtn()
    if not self.bp:IsVisible() then
        return
    end
    if not self.newbieRightUpView  then
        self.newbieRightUpView = self:AddView( self.bp.UI_Lobby_RightUp_NewBieReward, {})
    else
        self.newbieRightUpView:RefreshUI()
    end

    if self.newbieRightUpView then
        _MOE.Models.PushFaceModel:OnNoviceRewardEntryReady()
    end
end
```

### 5.1 为什么在创建或刷新后统一判断有效实例

刷新过程先确保入口子 View 处于可用状态：

```text
RefreshNoviceRewardBtn()
├─ newbieRightUpView 不存在 -> AddView(...)
└─ newbieRightUpView 已存在 -> RefreshUI()
```

随后统一判断：

```lua
if self.newbieRightUpView then
    _MOE.Models.PushFaceModel:OnNoviceRewardEntryReady()
end
```

这样既能避免入口对象不存在时误报 ready，也允许以下失败恢复链路成立：

```text
首次创建或刷新
└─ SceneData 未命中 / generation 过期 / 目标 Scene 无原始拍脸配置
   └─ 不消费 Model 的完成闸门
      └─ View 后续刷新再次通知
         └─ 配置可用后重新尝试
```

如果 `AddView` 返回 `nil`，本次不会通知；`self.newbieRightUpView` 仍为空，后续刷新仍可再次尝试创建。若目标 Scene 已有原始配置，只是条目被 `NeedShow=false` 等业务条件过滤，则本次已经完成收集并消费闸门，不属于上述技术失败重试链路。

### 5.2 为什么不放在点击函数

点击函数表达的是“用户已经主动操作入口”，而本例要表达的是“入口首次准备完成”。若放在点击函数：

- 未点击的玩家永远不会触发；
- 拍脸会晚于入口出现，失去引导入口的意义；
- 每次点击都可能重复通知；
- 触发语义与 SceneKey 不一致。

所以通知必须绑定 View 准备完成，而不是绑定用户点击。

### 5.3 View 可重复通知，Model 只消费一次完成机会

View 侧不承担一次性判断：

```text
newbieRightUpView 为空
└─ AddView 成功 -> 通知 Model

newbieRightUpView 已存在
└─ RefreshUI() -> 通知 Model
```

Model 侧承担两层去重：

```lua
if self._hasTriggeredNoviceRewardEntryReady or self._isNoviceRewardEntryTriggering then
    return
end
```

```text
通知到达 Model
├─ 已完成触发 -> 忽略
├─ 正在异步触发 -> 忽略
└─ 可以触发
   ├─ success=true 且 hasSceneConfig=true -> 消费一次完成机会
   │  └─ 最终队列可为空；NeedShow=false 仍属于已完成收集
   └─ 其他组合 -> 不消费，允许后续刷新重试
```

因此 View 重复调用是预期行为，不会造成并发重复收集；同时，SceneData 缺失、SceneId 非法、generation 过期或目标 Scene 原始配置为空也不会永久吃掉机会。`OnClose()` 会把 View 的 `newbieRightUpView` 清空，但只要 Model 没有 Reset，完成闸门仍能阻止再次触发。

---

## 6. Step 5：Item 已实际新增

文件：

```text
LetsGo/Content/LetsGo/Script/PushFace/Items/
└─ PushFace_NoviceRewardEntryReadyLocalTest.lua
```

真实代码：

```lua
-- 仅用于本地教学验证，提交前必须删除或正式化。
return {
    NeedShow = function(SceneId, activityId, id)
        _MOE.Logger.Log(
            "[PushFace_NoviceRewardEntryReadyLocalTest] NeedShow",
            "SceneId=", SceneId,
            "activityId=", activityId,
            "id=", id
        )
        return true
    end,

    HandleShow = function(SceneId, activityId, id)
        _MOE.Logger.Log(
            "[PushFace_NoviceRewardEntryReadyLocalTest] HandleShow",
            "SceneId=", SceneId,
            "activityId=", activityId,
            "id=", id
        )

        _MOE.Models.PushFaceModel:AddPushFaceItemCount()
        _MOE.UIManager:OpenWindow(_MOE.WindowName.UI_NoviceReward_MainView)
    end
}
```

### 6.1 `NeedShow` 恒为 `true` 为什么只能用于本地教学

`NeedShow()` 当前没有检查：

- 新手奖励业务是否正式开放；
- 玩家是否真的有资格；
- 数据是否准备完成；
- 主界面是否已经打开；
- 活动时间、领取状态或其他业务条件。

它会让所有通过拍脸通用前置条件的目标玩家直接入队。配合 `fequency=1` 和 `open=true`，这适合验证链路，不适合作为正式线上判断。

需要区分 Item 展示结论与 Trigger 完成结论：未来正式化后，即使真实业务条件让 `NeedShow()` 返回 `false`，只要目标 Scene 的原始拍脸配置存在，加载与收集流程有效，Trigger 仍回调 `(true, true)`，新手奖励入口仍会消费一次完成机会。也就是说，`NeedShow=false` 表示“本次业务判断不展示”，不表示“收集失败、等待 View 无限重试”。

正式化时必须把 `NeedShow()` 改成真实业务条件，或者删除整个本地测试配置和 Item。不能仅删除文件而保留 Excel 行，否则动态 `require` 会失败；也不能仅把 `NeedShow` 恒 true 的文件改名后直接上线。

---

## 7. Step 6：`Compile → Pbin`

校验脚本已经适配；完成 Excel 人工填表后，按项目既有导表流程对 `P_拍脸.xlsx` 执行：

```text
Compile
  ↓
Pbin
```

本次必须关注两个目标：

| Excel 工作表 | Proto Message | 目标 Pbin |
|---|---|---|
| `拍脸SceneId` | `table_PushFaceSceneData` | `PushFaceSceneData.pbin` |
| `拍脸内容` | `table_PushFaceData` | `PushFaceData_Total.pbin` |

项目映射文件已明确记录：

```text
P_拍脸.xlsx / 拍脸内容    -> PushFaceData_Total.pbin
P_拍脸.xlsx / 拍脸SceneId -> PushFaceSceneData.pbin
```

需要核对的生成位置包括：

```text
letsgo_common/excel/Export/pbin/PushFaceSceneData.pbin
letsgo_common/excel/Export/pbin/PushFaceSceneData.txt
letsgo_common/excel/client/data/PushFaceSceneData.pbin
letsgo_common/excel/client/data/PushFaceSceneData.txt

letsgo_common/excel/Export/pbin/PushFaceData_Total.pbin
letsgo_common/excel/Export/pbin/PushFaceData_Total.txt
letsgo_common/excel/client/data/PushFaceData_Total.pbin
letsgo_common/excel/client/data/PushFaceData_Total.txt
```

导表后用 TXT 做可读性核对，预期至少能看到：

```text
PushFaceSceneData:
  id: 19
  sceneKey: "NoviceRewardEntryReady"
  checkFunc: "CheckNoviceRewardReady"

PushFaceData_Total:
  id: 1000129
  sortId: 0
  codeName: "NoviceRewardEntryReadyLocalTest"
  fequency: 1
  open: true
  needLevel: 1
  sceneIds: 19
  featureName: <空，不应导出成错误字符串>
```

### 禁止事项

- **禁止手改 `.txt`**：TXT 是导表结果，不是配置源；
- **禁止手改 `.pbin`**：Pbin 是二进制产物；
- 禁止只替换 `PushFaceData_Total` 而漏掉 `PushFaceSceneData`；
- 禁止看到 Lua 已存在就跳过导表；
- 禁止改写校验器已固定的 Scene 19 → `NoviceRewardEntryReady` / `CheckNoviceRewardReady` 映射，也禁止复用 id 15 空占位。

唯一配置源应保持为 `P_拍脸.xlsx`，产物必须由标准流程生成。

---

## 8. 完整树状调用链

```text
UI_ActivityIcon_NoviceReward:InitUI()
或 LobbyRightUp 刷新事件
└─ UI_ActivityIcon_NoviceReward:RefreshNoviceRewardBtn()
   ├─ bp 不可见 -> return
   ├─ newbieRightUpView 不存在 -> AddView(...)
   │  └─ 返回 nil -> 本次不通知，等待后续刷新重试创建
   ├─ newbieRightUpView 已存在 -> RefreshUI()
   └─ 创建或刷新后 newbieRightUpView 有效
      └─ PushFaceModel:OnNoviceRewardEntryReady()
         ├─ GetSceneIdByKey("NoviceRewardEntryReady")
         │  ├─ 缓存命中 -> 返回暂定 SceneId 19
         │  └─ 缓存未命中 -> InitSceneIdConfig() 强制刷新一次后再查
         ├─ 刷新后仍不存在 -> warning + return，不消费机会
         ├─ 已完成触发 -> return
         ├─ 正在异步触发 -> return
         ├─ _isNoviceRewardEntryReady = true
         ├─ _isNoviceRewardEntryTriggering = true
         └─ TriggerPushFaceListBySceneId(19, false, CompletionCallback)
            ├─ Scene 配置未初始化 / SceneId 非法
            │  └─ CompletionCallback(false, false)
            │     ├─ 不设置 _hasTriggeredNoviceRewardEntryReady
            │     └─ _isNoviceRewardEntryTriggering = false
            └─ 捕获跨 Reset 单调递增的 sceneGeneration
               └─ PushFaceTable.LoadWebConfig(callback)
                  ├─ generation 已变化
                  │  ├─ 不回写旧场景队列
                  │  └─ CompletionCallback(false, false)，允许后续刷新重试
                  └─ generation 未变化
                     ├─ RawConfigList = GetPushfaceConfigBySceneId(19)
                     ├─ hasSceneConfig = RawConfigList 非空
                     ├─ CollectPushFaceListBySceneId(19, false)
                     │  ├─ PushFaceTable.GetPushfaceConfigBySceneId(19)
                     │  │  └─ 从 PushFaceData_Total 找到暂定 id=1000129
                     │  ├─ _checkPreConditions(...)
                     │  │  ├─ open
                     │  │  ├─ 队列重复
                     │  │  ├─ needLevel
                     │  │  ├─ 平台
                     │  │  └─ CheckCanShow
                     │  ├─ _getConfigByCodeName(
                     │  │    "NoviceRewardEntryReadyLocalTest", ""
                     │  │  )
                     │  │  └─ require(
                     │  │       "LetsGo.Script.PushFace.Items."
                     │  │       .. "PushFace_NoviceRewardEntryReadyLocalTest"
                     │  │     )
                     │  ├─ Item.NeedShow(19, activityId, 1000129)
                     │  │  ├─ 当前本地教学恒 true -> 继续频率检查
                     │  │  └─ 正式业务若为 false -> 不入队，但不改变 hasSceneConfig
                     │  ├─ _checkFrequencyLimit(...)
                     │  └─ 条件通过时加入 Scene 19 队列
                     ├─ 写入 m_PushFaceListMap[19]（允许空列表）
                     ├─ TryShowNextAutoShowWindow()
                     │  ├─ 队列为空 -> 本次不展示
                     │  └─ 队列非空
                     │     ├─ CheckCanNextShow()
                     │     ├─ 按 SceneId ProcessOrder 遍历
                     │     ├─ GetSceneCheckFuncName(19)
                     │     │  └─ "CheckNoviceRewardReady"
                     │     ├─ PushFaceModel:CheckNoviceRewardReady()
                     │     │  ├─ 入口 ready
                     │     │  ├─ 位于允许大厅拍脸的场景
                     │     │  └─ 大厅默认层条件通过
                     │     └─ HandleShowByList(19)
                     │        └─ Item.HandleShow(19, activityId, 1000129)
                     │           ├─ AddPushFaceItemCount()
                     │           └─ OpenWindow(UI_NoviceReward_MainView)
                     └─ CompletionCallback(true, hasSceneConfig)
                        ├─ hasSceneConfig=true -> 消费一次完成机会
                        │  └─ 即使 NeedShow=false 导致队列为空也会消费
                        ├─ hasSceneConfig=false -> 不消费，允许后续刷新重试
                        └─ _isNoviceRewardEntryTriggering = false
```

补充：`CollectPushFaceListBySceneId()` 先按 `sortId` 降序排序，而 `HandleShowByList()` 从数组尾部取元素，因此同一 Scene 队列中较小的 `sortId` 会较早被处理。`sortId=0` 是当前本地教学值，正式配置前应结合该 Scene 下其他拍脸重新确认排序策略。

---

## 9. 本地断点、日志与失败排查

### 9.1 推荐断点顺序

1. `UI_ActivityIcon_NoviceReward:RefreshNoviceRewardBtn()`
   - `AddView(...)` 返回值或现有 `newbieRightUpView`；
   - 创建、刷新后是否调用 `_MOE.Models.PushFaceModel:OnNoviceRewardEntryReady()`。
2. `PushFaceModel:OnNoviceRewardEntryReady()`
   - `sceneId` 是否为暂定值 `19`；未命中时 `GetSceneIdByKey()` 是否刷新一次缓存；
   - ready、triggering、hasTriggered 三项状态的变化；
   - 只有 `success and hasSceneConfig` 时是否设置 hasTriggered，其他结果是否只清除 triggering。
3. `PushFaceModel:TriggerPushFaceListBySceneId()`
   - `IsValidSceneId(19)` 是否通过；
   - `sceneGeneration` 与 `_pushFaceSceneGeneration` 是否一致，Reset 后 generation 是否继续递增；
   - `RawConfigList` 与 `hasSceneConfig` 是否符合预期；
   - `CompletionCallback(false, false)`、`CompletionCallback(true, false)` 或 `CompletionCallback(true, true)` 进入哪条路径。
4. `PushFaceModel:CollectPushFaceListBySceneId()`
   - `ConfigList` 是否包含 `id=1000129`；
   - `_checkPreConditions()` 是否通过；
   - `_getConfigByCodeName()` 是否加载成功。
5. `PushFaceModel:CheckNoviceRewardReady()`
   - ready、大厅场景、UI 条件分别是否通过。
6. `PushFace_NoviceRewardEntryReadyLocalTest.lua`
   - `NeedShow()`；
   - `HandleShow()`。

### 9.2 预期关键日志

```text
PushFaceModel:OnNoviceRewardEntryReady scene config not found, sceneKey=NoviceRewardEntryReady
PushFaceModel:TriggerPushFaceListBySceneId 19
PushFaceModel:CollectPushFaceListBySceneId, 19 false
PushFaceModel:CollectPushFaceListBySceneId accepted codeName=NoviceRewardEntryReadyLocalTest id=1000129
[PushFace_NoviceRewardEntryReadyLocalTest] NeedShow SceneId= 19 ... id= 1000129
[PushFace_NoviceRewardEntryReadyLocalTest] HandleShow SceneId= 19 ... id= 1000129
```

第一条 warning 在当前“未填表/未导表”状态下是预期结果；完成导表并加载新配置后不应继续出现。

### 9.3 常见失败与定位

| 现象 | 优先检查 | 说明/处理 |
|---|---|---|
| View 完全没有通知 | `bp:IsVisible()`、`newbieRightUpView` | 父 View 不可见会直接返回；`AddView` 返回 nil 时本次不会通知 |
| 日志提示 `scene config not found` | `PushFaceSceneData` | `GetSceneIdByKey()` 已在首次未命中时强制刷新一次缓存；若仍失败，检查 SceneData 未填、未导表、未加载或 `sceneKey` 拼写错误。该路径不会消费机会，后续刷新可重试 |
| 导表报 Scene 19 语义不一致 | Pbin checker | Scene 19 必须固定为 `NoviceRewardEntryReady` / `CheckNoviceRewardReady`，不可改写映射 |
| 导表报 id 15 被复用或缺失 | Pbin checker | `REQUIRED_SCENE_IDS` 强制 id 15 行必须存在，且该行必须保持 `sceneKey`、`checkFunc` 都为空 |
| Scene 行被 Model 忽略 | `_isValidSceneConfigRow()` | 检查 `id`、`sceneKey`、`checkFunc` 类型/空值，以及 Model 上是否有同名函数 |
| Scene 有效但 `ConfigList` 为空 | `PushFaceData_Total` | 检查 1000129 是否已导出、`sceneIds` 是否为 19 |
| 动态加载失败 | `codeName`、`featureName`、文件路径 | `featureName` 应为空；文件名必须为 `PushFace_` + `codeName` + `.lua` |
| `NeedShow` 没执行 | 前置条件或动态加载 | 检查 `open`、等级、平台、时间与 `HandleShow` 接口是否存在 |
| `NeedShow=false` 后没有再次触发 | Completion 语义 | 若目标 Scene 原始配置存在，`(true, true)` 表示收集已完成，即使最终队列为空也会消费一次；这是预期行为，不应按技术失败无限重试 |
| Scene 检查失败 | `CheckNoviceRewardReady()` 日志 | 检查 ready 标记、大厅场景和 `IsOnLobbyViewWithNoDefaultWindowVisible()` |
| 队列有数据但不弹 | `CheckCanNextShow()` | Loading、强引导、回流屏蔽、SystemMini 资源未就绪都会阻塞 |
| `fequency=1` 仍未入队 | `IsClickedTodayNoShow(1000129)` | `Always` 分支仍会检查“今日不再显示”缓存；本地排查时确认对应缓存状态 |
| 修改 Pbin 后仍取旧 Scene 缓存 | Scene 配置初始化时机 | `GetSceneIdByKey()` 仅在 key 未命中时自动重建一次缓存；若旧缓存已命中旧值，仍需重启测试环境或沿现有 `RefreshSceneIdConfig()` 能力主动刷新 |
| 配置缺失后一直没有重试 | View 刷新事件、Model 完成闸门 | 有效 View 每次刷新都会通知；确认 `_hasTriggeredNoviceRewardEntryReady` 未被错误提前置为 true，并区分 `(true, true)` 已完成与可重试失败 |
| 异步返回后队列被丢弃 | `_pushFaceSceneGeneration` | 场景切换或 Reset 都会让旧回调过期，这是预期保护；generation 跨 Reset 单调递增，失败不消费机会，回到有效 View 后可重试 |
| 点击入口后才触发/重复触发 | 触发点接错 | 通知应保留在 `RefreshNoviceRewardBtn()` 创建/刷新后的有效实例判断中，不应迁到点击函数 |

> 不建议为了“让它先跑起来”而在 Lua 中硬编码 `sceneId=19`。这样会绕过配置校验，也会让 Excel 与运行时语义分叉。

---

## 10. 验收、正式化与删除清单

### 10.1 配置验收

- [ ] 基于最新 `P_拍脸.xlsx` 对 SceneId `19` 做全表查重；
- [ ] 对 `sceneKey=NoviceRewardEntryReady` 做全表查重；
- [ ] 对拍脸内容 ID `1000129` 做全表查重；
- [ ] 确认历史保留 SceneId `15` 的空占位行仍然存在，且未被复用；
- [ ] 确认没有覆盖现有 `1000128 / NoviceRewardLocalTest / sceneIds=1`；
- [ ] `拍脸SceneId` 的 `checkFunc` 精确为 `CheckNoviceRewardReady`；
- [x] Pbin checker 已允许 `CheckNoviceRewardReady`，固定 Scene 19 的 sceneKey/checkFunc 映射，并通过 `REQUIRED_SCENE_IDS` 强制 id 15 空占位存在；
- [ ] `拍脸内容` 的 `featureName` 为空；
- [ ] 完成 `Compile → Pbin`；
- [ ] `PushFaceSceneData` 与 `PushFaceData_Total` 两组产物都已更新；
- [ ] 生成 TXT 中可查到 Scene 19 与内容 1000129；
- [ ] 没有手工修改 TXT/Pbin。

### 10.2 运行验收

- [ ] 父 View 不可见时不通知；
- [ ] `AddView` 返回 nil 时不通知；
- [ ] `AddView` 返回有效实例后通知 Model；
- [ ] 同一 View 实例后续 `RefreshUI()` 仍会通知 Model；
- [ ] 异步触发期间重复通知会被 `_isNoviceRewardEntryTriggering` 去重；
- [ ] 只有 `CompletionCallback(true, true)` 才令 `_hasTriggeredNoviceRewardEntryReady=true`，后续通知不再触发；
- [ ] `(false, false)`、`(true, false)` 均不消费完成机会，后续刷新可以重试；
- [ ] 目标 Scene 有原始配置但 `NeedShow=false` 时，最终队列可为空，仍按 `(true, true)` 完成并消费一次；
- [ ] generation 在首次 `OnInit()`、`OnReset()` 和场景切换后持续递增，不回退复用；
- [ ] generation 过期回调不会写回旧场景队列；
- [ ] `GetSceneIdByKey("NoviceRewardEntryReady")` 缓存未命中时会刷新一次，并能取得正式确认后的 SceneId；
- [ ] `CheckNoviceRewardReady()` 三项条件均符合预期；
- [ ] 日志中出现本地 Item 的 `NeedShow` 与 `HandleShow`；
- [ ] 最终打开 `UI_NoviceReward_MainView`；
- [ ] 点击入口本身不会额外产生一次 Scene 通知；
- [ ] Model Reset 后业务完成闸门重置、generation 继续递增的语义符合产品预期。

### 10.3 正式化清单

若该能力要上线而不是仅做教学验证：

- [ ] SceneId `19` 与内容 ID `1000129` 经配置负责人正式确认，而非继续使用“本地暂定”结论；
- [x] 新 Scene 已写入校验器的历史映射保护；
- [ ] 去掉 `LocalTest` 命名，保持 Excel `codeName` 与 Item 文件名同步；
- [ ] 将 `NeedShow()` 的恒 `true` 替换为真实活动资格、数据状态与业务开关判断；
- [ ] 根据正式产品语义重新确认 `fequency`，不要默认沿用 `1`；
- [ ] 根据同 Scene 下正式拍脸重新确认 `sortId`；
- [ ] 评估 `OnReset()` 后允许再次触发是否符合需求；
- [ ] 补充正式日志、数据上报与异常兜底；
- [ ] 完成目标平台、等级、引导、回流屏蔽和资源未就绪场景回归。

### 10.4 若放弃本地教学方案，删除时必须成套处理

- [ ] 删除/回退 Excel 中新增的 SceneData 行；
- [ ] 删除/回退 Excel 中新增的拍脸内容行；
- [ ] 重新导出两个 Pbin，不能只删 Lua；
- [ ] 删除 `PushFace_NoviceRewardEntryReadyLocalTest.lua`；
- [ ] 回退 View 中的 `OnNoviceRewardEntryReady()` 通知；
- [ ] 回退 Model 中四项状态、完成回调/generation 保护、通知函数和 Scene 检查函数；
- [ ] 回退校验器中专为该 Scene 增加的允许项/历史映射；
- [ ] 全局确认不存在 `NoviceRewardEntryReady`、`CheckNoviceRewardReady`、`1000129` 的残留引用；
- [ ] **不要顺带删除或改写现有 1000128**，除非另有明确的旧测试项清理任务。

---

## 最终结论

本实例的 Lua、View、本地教学 Item 和 Pbin 校验器已经落地：View 可在创建或刷新后重复通知；`GetSceneIdByKey()` 未命中会刷新一次 Scene 配置缓存；Model 负责并发去重，只在 `success and hasSceneConfig` 时消费一次完成机会，目标 Scene 有原始配置但 `NeedShow=false` 时仍算完成收集；generation 在 `OnInit()` 基于旧值加一并跨 Reset 单调递增，可阻止 Reset 前或旧场景的过期异步回写；校验器通过 `REQUIRED_SCENE_IDS` 强制 id 15 空占位存在。但配置链路尚未闭环，当前必须完成以下动作后才能运行命中：

```text
人工全表查重
→ 在 P_拍脸.xlsx 填 SceneData 19（暂定）
→ 填拍脸内容 1000129（暂定）
→ Compile
→ Pbin
→ 核对 PushFaceSceneData 与 PushFaceData_Total
→ 重启/刷新配置后本地断点验收
```

校验器适配不再是未完成项。当前 XLSX 与导出产物仍无 Scene 19 / 内容 1000129，因此运行时仍不能命中新配置。

在完成这些步骤之前，不应把文档中的暂定值视为已生效配置。
