
## 1. 服务器数据是怎么来的（协议是什么意思）

### 1.1 "协议" = 服务端和客户端约定的通信格式

```
服务端（C++）  ←——协议——→  客户端（Lua）
```

**协议就是一种约定**：
- 服务端说："我推一坨二进制数据给你，按 `CsAllPlayerActivityInfo` 格式解读"
- 客户端说："好的，我用 `pb.decode("com.tencent.wea.protocol.CsAllPlayerActivityInfo", 数据)` 解码"

### 1.2 协议的两种方向

| 方向 | 名称 | 含义 | 举例 |
|------|------|------|------|
| **C → S** | C2S（Client to Server） | 客户端发给服务端 | "我要领奖"、"请给我活动数据" |
| **S → C** | Ntf（Notify 通知） | 服务端推给客户端 | "你的任务完成了"、"活动开始了" |

### 1.3 协议的数据传输过程

```
服务端
  │ 原始数据: { activityId=10017, score=30, taskList=[...] }
  │ ↓ Protobuf 编码（压缩成二进制字节流）
  │ 网络传输: [0x08, 0xA9, 0x4E, 0x12, ...]  ← 二进制字节流
  ↓
客户端 ActivityModel_Protocol.lua
  │ 接收: rawDataBytes = [0x08, 0xA9, 0x4E, 0x12, ...]
  │ 解码: pb.decode("com.tencent.wea.protocol.CsAllPlayerActivityInfo", rawDataBytes)
  │ ↓ 解码后变成 Lua 表
  │ msgData = { activityId=10017, score=30, taskList={...} }
  ↓
存储到 Model 中
```

**源码对应**（`ActivityModel_Protocol.lua` 第539-560行）：
```lua
function ActivityModel_Protocol.DecodeData(activityModel, rawDataBytes, rspPbName)
    -- rawDataBytes: 服务端发来的二进制字节流
    -- rspPbName: 协议格式名（如 "CsAllPlayerActivityInfo"）

    -- 用 Protobuf 解码
    local decodeParams = pb.decode(
        "com.tencent.wea.protocol." .. rspPbName,  -- 完整协议名
        rawDataBytes                                  -- 原始字节流
    )

    -- 返回 Lua 表
    return decodeParams  -- { activityId=10017, score=30, ... }
end
```

---

## 2. Model 读取的数据包含配置表数据吗？

**答案：不包含。Model 有两套独立的数据来源。**

### 数据来源对比

```
┌──────────────────────────────────────────────────────┐
│               活动数据的两个来源                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  来源1: 配置表（静态数据，导表生成）                     │
│  ┌─────────────────────────────────────────┐         │
│  │ ActivityMainConfigForLetsGo_common.txt   │         │
│  │  ↓ 导表后变为                              │         │
│  │ _MOE.Config.ActivityMainConfig            │         │
│  │  包含: activityName, activityUIDetail,   │         │
│  │       tagId, jumpId, backgroundUrl,       │         │
│  │       timeInfo, activityShopType, ...     │         │
│  └─────────────────────────────────────────┘         │
│  特点: 固定不变, 导表后就不会改                          │
│  读取: _MOE.Config.ActivityMainConfig:GetDataByKey(id)│
│                                                      │
│  来源2: 服务端推送（动态数据，运行时下发）                │
│  ┌─────────────────────────────────────────┐         │
│  │ ActivityInfoUpdateNtf (服务端推送)        │         │
│  │  ↓ 解码后变为                              │         │
│  │ _newActivityInfoMap[activityId]           │         │
│  │  包含: 任务完成状态, 当前积分, 奖励领取进度, │         │
│  │       红点状态, 玩法进度数据 ...            │         │
│  └─────────────────────────────────────────┘         │
│  特点: 实时变化, 玩家操作后服务端推送更新                │
│  读取: ActivityModel:GetActivityInfo(tagId, activityId)│
│                                                      │
└──────────────────────────────────────────────────────┘
```

### 源码证据

`ActivityModel_DataQuery.lua` 第72-81行 — 有一个函数会**优先读服务端数据，找不到再回退读配置表**：
```lua
function ActivityModel_DataQuery.GetActInfoOrCfgByActId(activityModel, activityId)
    -- 1. 先从服务端数据中找
    local actInfo = ActivityModel_DataQuery.GetInfoByActivityId(activityModel, activityId)
    if not actInfo then
        -- 2. 找不到 → 从配置表读
        actInfo = _MOE.Config.ActivityMainConfig:GetDataByKey(activityId)
    end
    return actInfo
end
```

**但基类 `UI_Activity_BaseView:InitData()` 用的是另一个函数**（第31行）：
```lua
function UI_Activity_BaseView:InitData()
    -- 这里读的是服务端推送的活动列表数据
    self.ActivityInfo = _MOE.Models.ActivityModel:GetActivityInfo(self.Data.tagId, self.Data.id)
    -- 找不到才用另一个接口（也是服务端数据）
    if self.ActivityInfo == nil then
        self.ActivityInfo = _MOE.Models.ActivityModel:GetActivityInfoById(self.Data.id)
    end
end
```

### 两个数据源的具体内容

| 字段 | 配置表数据 | 服务端推送数据 |
|------|-----------|-------------|
| `activityName` | ✅ "春日兑换" | ✅ 同配置表（服务端也会下发） |
| `activityUIDetail` | ✅ "UI_ActivityTemplate_..." | ✅ |
| `tagId` | ✅ 1 | ✅ |
| `activityShopType` | ✅ 142 | ✅ |
| `backgroundUrl` | ✅ "spring_bg.astc" | ✅ |
| `timeInfo` | ✅ begin/end | ✅ |
| **任务完成状态** | ❌ | ✅ {570011=已完成, 570021=未完成} |
| **当前积分** | ❌ | ✅ score=30 |
| **奖励领取进度** | ❌ | ✅ {reward1=已领, reward2=未领} |
| **红点状态** | ❌ | ✅ is_new=true |
| **玩法进度数据** | ❌ | ✅ 各活动自定义数据 |

> 💡 **总结**：服务端推送的数据**包含了配置表的静态数据 + 玩家的动态进度数据**。所以 View 读到的 `ActivityInfo` 是两份合并后的完整数据。

---

## 3. 传入 View 的 Data 到底是什么

View 的 `Data` 来自**两个地方**，在 `OnOpen` 时传入：

### 3.1 Data 的来源

```
UI_Events_Main.lua 第 808-819行:
    local activityUIDetail = v.activityUIDetail  -- ← 来自服务端推送的活动数据
    tabInfo.UIName = activityUIDetail
    tabInfo.id = v.id                             -- ← 活动ID
    tabInfo.tagId = v.tagId                       -- ← 标签ID

第 1081行:
    self.SubView = self:AddWidget(tabInfo.UIName, slot, info)
    -- info 就是 Data, 包含:
    -- info.id = 活动ID
    -- info.tagId = 标签ID
    -- info.activityUIDetail = UMG名
    -- info + 其他活动配置字段
```

### 3.2 Data 包含的内容

```lua
Data = {
    -- 来自服务端推送的活动数据（包含配置表同步过来的字段）
    id = 10017,                    -- 活动ID
    tagId = 1,                     -- 标签ID
    activityName = "春日兑换",      -- 活动名
    activityType = "ATLinearRedeem", -- 玩法类型
    activityUIDetail = "UI_ActivityTemplate_ExchangeLinearView", -- UMG名
    activityShopType = {142},       -- 商城类型
    activityTaskGroup = {570011, 570021}, -- 任务组
    backgroundUrl = {"spring_bg.astc", "spring_title.astc"}, -- 背景图+标题图
    timeInfo = { beginTime={...}, endTime={...} }, -- 时间
    clientParams = {"每日任务", "兑换商店"}, -- Tab名
    activityParam = {5, 1300001},   -- 追赶机制参数
    platforms = {1, 2, 3, 4},
    lowVersion = "1.5.61.25",
    suspend = 0,
    -- ... 其他配置表字段

    -- 来自玩家动态数据（服务端推送）
    -- 注意: 这些动态数据不在 Data 里!
    -- 它们在 ActivityInfo 中, 需要单独获取
}
```

### 3.3 Data vs ActivityInfo 的区别

```
┌──────────────────────────────────────────────────────────┐
│              View 拿到的数据有两个                         │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. self.Data ← OnOpen 时传入                            │
│     来源: UI_Events_Main 从活动列表数据中取出               │
│     内容: 活动的基础信息 (id, tagId, activityName, ...)   │
│     用途: 知道"这是哪个活动"                               │
│                                                          │
│  2. self.ActivityInfo ← InitData 中获取                   │
│     来源: ActivityModel:GetActivityInfo(tagId, activityId)│
│     内容: 活动的完整数据 (基础信息 + 玩家进度 + 奖励状态)    │
│     用途: 知道"活动当前是什么状态"                          │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**源码对应**（`UI_Activity_BaseView.lua` 第16-36行）：
```lua
function UI_Activity_BaseView:Init(child, Data)
    self.child = child
    self.Data = Data         -- ← 第1份数据: 活动基础信息
    self.bp = self.child.bp
end

function UI_Activity_BaseView:InitData()
    -- 第2份数据: 从 Model 获取完整活动信息
    self.ActivityInfo = _MOE.Models.ActivityModel:GetActivityInfo(self.Data.tagId, self.Data.id)
    -- ↑ 这里读到的 ActivityInfo 包含:
    --   - 配置表的字段 (activityName, backgroundUrl, timeInfo...)
    --   - 服务端推送的动态数据 (任务状态, 积分, 奖励进度...)
end
```

---

## 4. 完整数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                  完整数据流: 从服务端到玩家看到的UI                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐                                                   │
│  │  配置表   │ ActivityMainConfigForLetsGo_*.txt (导表后)        │
│  │ (静态)   │ → _MOE.Config.ActivityMainConfig                  │
│  └────┬─────┘   包含: activityName, UMG名, tagId, 商城, 时间... │
│       │                                                         │
│       │    ┌──────────┐                                         │
│       │    │  服务端   │ ActivityInfoUpdateNtf (Protobuf字节流)   │
│       │    │ (动态)   │ → pb.decode 解码                        │
│       │    └────┬─────┘                                         │
│       │         │    包含: 任务状态, 积分, 奖励进度, 红点...      │
│       │         │                                               │
│       ↓         ↓                                               │
│  ┌─────────────────────┐                                        │
│  │      Model 层       │                                        │
│  │                     │                                        │
│  │  Activity_Persistent │ ← 接收服务端 Ntf (门卫)                 │
│  │       ↓             │                                        │
│  │  ActivityModel_     │ ← 解码 Protobuf (拆包裹)                │
│  │  Protocol            │                                        │
│  │       ↓             │                                        │
│  │  ActivityModel_     │ ← 存储 (入库)                           │
│  │  DataQuery           │    m_ActivityInfoMap[tagId] = 活动列表  │
│  │                     │    _newActivityInfoMap[id] = 动态数据    │
│  │       ↓             │                                        │
│  │  DispatchEvent       │ ← 广播 (通知前台)                       │
│  │  (OnActivityInfo     │    "活动10017更新了！"                   │
│  │  UpdateNtf, id)     │                                        │
│  └─────────┬───────────┘                                        │
│            │                                                    │
│            ↓                                                    │
│  ┌─────────────────────┐                                        │
│  │      View 层        │                                        │
│  │                     │                                        │
│  │  AddEventListener   │ ← 听到广播                              │
│  │       ↓             │                                        │
│  │  GetActivityInfo()   │ ← 去仓库取货                            │
│  │    返回 ActivityInfo │    (配置表字段 + 服务端动态数据 合并)     │
│  │       ↓             │                                        │
│  │  self.ActivityInfo  │ ← 存到 View                              │
│  │       ↓             │                                        │
│  │  InitUI()           │ ← 摆上货架                               │
│  │  ├─ TextSetText     │    标题 = ActivityInfo.activityName      │
│  │  ├─ ImgSetTexture   │    背景图 = ActivityInfo.backgroundUrl  │
│  │  ├─ ListSetDatas    │    任务列表 = ActivityInfo.taskList      │
│  │  └─ SetVisibility   │    按钮状态 = 根据任务状态判断            │
│  └─────────────────────┘                                        │
│            │                                                    │
│            ↓                                                    │
│  ┌─────────────────────┐                                        │
│  │     UMG 蓝图         │                                        │
│  │  玩家看到的界面       │                                        │
│  └─────────────────────┘                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 一句话总结

| 问题 | 答案 |
|------|------|
| 协议是什么？ | 服务端和客户端约定的通信格式，用 Protobuf 编解码 |
| Model 怎么读服务端数据？ | 收到二进制字节流 → `pb.decode()` 解码成 Lua 表 → 存到内存 |
| Model 数据包含配置表数据吗？ | **服务端推送的数据本身就包含了配置表字段**（服务端也会读配置表并下发） |
| 传入 View 的 Data 是什么？ | 活动的基础信息（id, tagId 等），用于"知道是哪个活动" |
| ActivityInfo 是什么？ | 从 Model 读取的完整数据（配置表字段 + 玩家动态进度 + 奖励状态） |
| View 怎么显示数据？ | `self.ActivityInfo.xxx` → 写入 `self.bp.w_xxx`（UMG Widget） |