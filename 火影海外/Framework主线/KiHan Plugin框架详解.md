---
title: KiHan Plugin 框架详解（Plugin / Operation / Model / View）
tags: [KiHan, 架构, Plugin, C#, 业务框架]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/plugin-framework.md + Plugin/Infrastructure 源码核验
---

# KiHan Plugin 框架详解

> KiHan **144 个 C# 业务模块**（商城/公会/忍具/充值…）的统一写法。源码：`Assets/Scripts/Plugin/Infrastructure/`
> 在架构中的位置：被状态机拉起 → `KHGameFlow.BuildGame()` → `KHPluginManager.Instance.initializePlugins()`

---

## 0. 一句话总览：部门类比

| 类 | 类比 | 职责 |
|---|---|---|
| `Plugin` | **部门经理** | 模块入口 / 开窗 / 资源 / 消息派发（Controller） |
| `Operation` | **办事员** | 按"事项名"接单干活（行为单元） |
| `Model` | **档案柜** | 存数据，网络回包自动归档 |
| `View`(UIWindow) | **对外柜台** | 界面展示 |
| `KHPluginManager` | **公司总机** | 按名字找部门、转接消息 |

> **核心约定**：Plugin 是 Controller，Model 是数据，Operation 是行为。**三者靠「消息字符串」解耦，不直接互调。**

---

## 1. 核心概念

| 基类 | 数量关系 | 生命周期 | 关键约束 |
|---|---|---|---|
| Plugin | 一模块一个 | ConstructPlugin → Initialize(懒) → ShowView/HideView | abstract，经 KHPluginManager 注册 |
| Operation | 一 Plugin 多个（按业务分组） | 构造时反射扫描 `[Operation]` | abstract，方法打标签 |
| Model | 一 Plugin 一个 | 构造时反射扫描 `[UpdateProcessor]` | 继承 BindingSource |
| View | 一 Plugin 多个 | OnInitWindow → OnInitData → OnOpen → OnClose | 挂 prefab 根节点的 MonoBehaviour |

### PluginSetting（配置单，必须先懂）

```csharp
public class PluginSetting
{
    public string PluginName;             // 注册名（总机的 key）
    public bool LoadWhenShowView;         // true=开窗时才加载资源
    public string[] Views;                // ★ 注册的 View 列表（反查钥匙）
    public string DefaultView;            // ShowView() 不传参时默认开哪个
    public bool WaitForNetMsg;            // 开窗前是否等回包
}
```

---

## 2. 两条核心链路

### 链路 A：Plugin 生命周期

```
new XxxPlugin()
  → ConstructPlugin()                    ← KHPluginManager 触发
      ├─ CreateInitSetting()             填 PluginSetting（Views[] 等）
      ├─ CreateModel()                   model = new XxxModel(this)
      └─ RegisterOperations()            ★ 必须调 base（注入 ViewOperation）
  → Initialize()                         首次收到消息才触发（懒初始化）
  → ShowView(ShowViewArgument)           开窗（LoadWhenShowView 决定加载时机）
  → HideView(title) / CloseAllViews()
```

### 链路 B：消息流水线（核心数据流）

```
业务方 SendMessage("Plugin名", "消息名", data)
  → KHPluginManager 找到 Plugin → 遍历 Operations → Route()
      → 有 Lua hook？ → 有：Lua 前置处理（可改数据/可终止）
      → 无/继续 → DoRoute → 反射 Invoke [Operation("消息名")] 方法
  → Operation 改 Model → Model.Dispatcher.dispatchEvent
  → View 收事件刷新

【旁路】NetworkManager 回包 → [UpdateProcessor] 直接进 Model（不经过 Operation）
```

---

## 3. 三个"魔法"（反射机制，搜代码必知）

| 魔法 | 机制 | 排查影响 |
|---|---|---|
| `[Operation("MsgName")]` | Operation 构造时反射扫描方法登记字典 | **搜"谁调用了 OnXxx"搜不到**，要搜消息名字符串 |
| `[UpdateProcessor(cmdId)]` | Model 构造时自动注册到 NetworkManager | 搜"回包谁处理"要搜 cmdId，不是方法名 |
| `base.RegisterOperations()` | 注入 ViewOperation，自动响应 `ShowView/HideView/HideAllViews/EnqueueMessage` | 忘调 base → **界面打不开** |

**Lua Hook 扩展点**：Lua 可在 C# 方法执行前截获消息——返回 `(true, newData)` 替换数据继续；返回 `(false, ...)` **终止路由**。→ 某消息"没反应"可能是被 Lua 拦了。

---

## 4. 子类标准模板（6 步）

```csharp
public class XxxPlugin : Plugin
{
    public const string pluginName = "XxxPlugin";           // 1. 注册名
    private readonly string[] views = { UIDef.XXX_MAIN_VIEW };  // 2. View 列表
    public override string[] GetViews() => views.ToArray();  // 3. 暴露

    protected override void CreateInitSetting() {           // 4. 配置
        m_setting = new PluginSetting { PluginName = pluginName, Views = views };
        InitSetting(m_setting);
    }
    protected override void CreateModel()                   // 5. 建 Model
        => model = new XxxModel(this);
    protected override void RegisterOperations() {          // 6. 注册 Operation
        base.RegisterOperations();                          // ★ 忘了开不了窗
        Operations.Add(new XxxOp { ParentPlugin = this });
    }
}
```

---

## 5. 必知重点与坑

1. **`Views[]` 是反查钥匙**：Plugin 名 → `Views[]` 里 UIDef 常量 → `Data/UIDef.cs` 查 prefab 路径 → 定位 View 脚本
2. **View 嵌套 `ViewArg`**：Model 提供 `InitXxxViewArg()` 打包状态 → View 的 `OnInitData` 接收渲染（准 ViewModel 模式）
3. **8 种架构形态**：先学 MVC 标准型（NinjaBattleField）；Shopping/Arena 是 Lua 主导型（C# 薄壳，别照抄）；GuildHegemony 等纯 Lua 型**不走本框架**
4. **战斗类**：继承链 `Plugin → BattlePlugin → IFWBattlePlugin`，BattlePlugin 多了战斗忍者请求/超时重试/Loading/跨场景资源等
5. **View 的 `OnCloseWindow` 必须清 Dispatcher 监听**（关闭是 Hide 复用，不清会残留）

---

## 6. Plugin vs Act（怎么选）

| | Plugin | Act |
|---|---|---|
| 基类 | `Plugin`(C#) 或 `LuaBehaviour` | 仅 Lua |
| 注册 | KHPluginManager 全局 | ActCenterPlugin 子注册 |
| 生命周期 | 持续（部分常驻） | 活动期内（有限） |
| 适用 | **长期系统功能**（商城/公会/好友/充值） | **限时运营活动**（春节/签到/抽奖） |

---

## 7. 排查速查

| 现象 | 先查 |
|---|---|
| 界面打不开 | 漏调 `base.RegisterOperations()`；`Views[]` 没注册该 UIDef |
| 发消息没反应 | 消息名拼错（反射静默失败）；被 Lua Hook 拦截 |
| 收不到回包 | Model 方法没打 `[UpdateProcessor]`；cmdId 不对 |
| View 不刷新 | 没订阅 `Model.Dispatcher`；Model 改完没 `dispatchEvent` |
| 找不到界面文件 | `Views[]` → `UIDef.cs` → prefab 路径 |

---

## 8. 记忆口诀

> **Plugin 经理开窗门，Operation 办事靠标签，Model 档案收回包，View 柜台看消息。**
> 三把钥匙：**`Views[]` 反查界面、`[Operation]` 找行为、`[UpdateProcessor]` 找数据源。**

## 相关笔记

- [[KiHan状态机架构详解]]（调度者）
- [[KiHan ActFramework详解]]（Lua 侧对照）
- [[KiHan UI框架详解]]（View 层深入）
