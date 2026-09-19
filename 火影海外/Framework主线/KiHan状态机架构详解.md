\---  
title: KiHan 状态机架构详解（Context / Workflow / Phase / Adapter）
  
tags: [KiHan, 架构, 状态机, Context, Workflow, Phase, Adapter, Boot, Duplicate]
  
created: 2026-09-18
  
confidence: high
  
source: 源码直读（GameEntry/KHGameFlow.cs、Module/KHGameLevelContext.cs、Module/Workflow/、Module/PhaseAdapter/、Module/Boot/、Module/Duplicate/）  
\---

# KiHan 状态机架构详解

> 本文基于 `Others/AIDev/context/framework/state-machine-framework.md` 与**真实源码对照**整理
>   
> 源码根目录：`Assets/Scripts/`
>   
> 适用：想理解 KiHan 客户端"主干调度骨架"的新人



---

## 0. 一句话总览：餐厅类比

把游戏想成**一家餐厅的一天营业流程**：

| 概念                   | 类比           | 本质                    |
| -------------------- | ------------ | --------------------- |
| `KHGameFlow`         | **店长**       | 唯一调度者，决定现在开哪个档口       |
| `Context`            | **档口**       | 早餐档/午餐档/夜宵档，一次只开一个    |
| `Workflow`           | **档口的操作手册**  | 规定"备料 → 制作 → 收摊"的步骤顺序 |
| `Phase`              | **手册里的一个步骤** | 比如"备料"这一步             |
| `Adapter`            | **这一步的具体做法** | 同样"备料"，堂食和外卖做法不同      |
| `Boot` / `Duplicate` | **具体的档口名**   | 开业准备档 / 包间接待档         |

**核心设计（务必记住）**：

> Context 决定"在哪个玩法"，Workflow 决定"流程怎么走"，Phase 决定"现在走到哪一步"，Adapter 决定"这一步在当前运行态下具体怎么做"。**四层职责正交，互不越权。**

---

## 1. 七个概念逐个拆解

### 1.0 `KHGameFlow` —— 店长（唯一，在四层之上）

| 项      | 内容                                                                                   |
| ------ | ------------------------------------------------------------------------------------ |
| 是什么    | **全局唯一的流程管理器**，所有玩法切换的入口                                                             |
| 代码     | `Assets/Scripts/GameEntry/KHGameFlow.cs`（497 行）                                      |
| 持有     | 14 个 Context 的强类型字段 + 当前 Context 引用                                                  |
| 核心 API | `Start()` / `SwitchLevel(name)` / `TrySwitchLevel(name)` / `GetContextByValue(name)` |
| 数量     | **1 个**（非单例，由 `KHGame` 持有）                                                           |

它不是四层之一，是**四层之上的调度器**。

```csharp
// GameEntry/KHGameFlow.cs:19-37
private List<KHGameLevelContext> m_gameContexts;

private KHBootContext m_bootContext;
private KHMainContext m_mainContext;
private KHDuplicateContext m_duplicateContext;
private KHNNAITrainContext m_nnAITrainContext;
private KHPKNSContext m_pknsContext;
private PVPRBLContext m_pvpRBLContext;
private InfinityWorldContext m_IFWContext;
private DAWContext m_dawContext;
private AutoChessContext m_autoChessContext;
private KHPerformanceContext m_performanceContext;
private KHGameLevelContext m_currentLevelContext;
private Dodomeki.DKMainContext m_dkMainContext;
private Dodomeki.DKRoomContext m_dkRoomContext;
/// <summary>3D战斗的Context</summary>
private PASContext m_pasContext;
```

**三个文档没写、但代码里很关键的细节**：

1. **分派是手写 if/else 链**，不是字典。`GetContextByValue()` 用了 14 个 `else if`（`KHGameFlow.cs:302-440`），`m_gameContexts` 只是登记用（`AddModule`）。
2. **Context 是进程级常驻单例**——创建后永不销毁：

```csharp
// GameEntry/KHGameFlow.cs:302-312
if (value.Equals(KHLevelName.BOOT))
{
    if (m_bootContext == null)
    {
        m_bootContext = new KHBootContext();
        AddModule(m_bootContext);
        m_bootContext.Init();
    }
    context = m_bootContext;
}
```

→ **切走只 `Unbuild`，不销毁；再进来走 `Init()` 里的 `m_workflow.Reset()` 复用**。这是"Context 复用后状态残留"类问题的根因。

1. `GAME_CONTEXT_CHANGE` **在 if 外面无条件派发**（`KHGameFlow.cs:275-276`），即使没真正切换也发。

---

### 1.1 `Context`（`KHGameLevelContext`）—— 档口

| 项    | 内容                                                        |
| ---- | --------------------------------------------------------- |
| 是什么  | **一种游戏玩法/模式的生命周期壳**                                       |
| 代码   | `Assets/Scripts/Module/KHGameLevelContext.cs`（**仅 50 行**） |
| 本质   | 抽象壳：持有 Workflow + 声明"能切去哪"                                |
| 数量   | **15 种**（对应 `KHLevelName` 常量），同时只有 1 个活跃                  |
| 生命周期 | `Init()` → `Build()` → `Unbuild()` → `Final()`            |

基类核心代码（全文才 50 行）：

```csharp
// Module/KHGameLevelContext.cs:26-48
public abstract void Init();
public abstract void Final();

public virtual void Build()
{
    KHUIManager.EnableOpenWindow = true;      // ★ 基类只做这一件事
}

public abstract void Unbuild();

protected Workflow m_workflow;
public Workflow Workflow { get { return m_workflow; } }

public abstract string[] SwitchTargetList { get; }   // ★ 切换白名单

public void SendSingal(string singal, object data = null)
{
    m_workflow.SendSignal(singal, data);
}
```

> **为什么 `Build()` 只放开开窗？** 因为 `Build()` 是在 **Unity 场景加载完成后**才调用的。这保证了场景没就绪时 UI 不会抢跑。

---

### 1.2 `Workflow` —— 档口的操作手册

| 项      | 内容                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------- |
| 是什么    | **某个玩法内部的阶段状态机**，管 Phase 的注册与切换                                                                   |
| 代码     | `Assets/Scripts/Module/Workflow/Workflow.cs`（101 行）                                               |
| 持有     | `Dictionary<string, Phase> m_phases` + 当前 Phase                                                   |
| 数量     | **一 Context 一个（1:1）**                                                                             |
| 核心 API | `InitializePhases()` / `Start(data)` / `SwitchPhase(name, data, execute, throwEvent)` / `Reset()` |

```csharp
// Module/Workflow/Workflow.cs:51-83
protected void SwitchPhase(string phaseString, object data, bool execute = true, bool throwEvent = true)
{
    Phase phase;
    if(m_phases.TryGetValue(phaseString, out phase))
    {
        if (m_currentPhase != null)
            m_currentPhase.Unbuild();          // ① 旧阶段收尾

        m_currentPhaseName = phaseString;
        m_currentPhase = phase;                 // ② 设为当前

        if (execute)
        {
            m_started = true;
            m_currentPhase.Build(data);         // ③ 执行新阶段
        }
        else
            m_started = false;

        if(throwEvent)
            KHGlobal.dispatcher.dispatchEvent(new KHEvent(WorkflowEvent.SwitchPhase) { data = phase });
    }
    else
    {
        // ⚠ 只 Warning 不报错：阶段名写错会静默卡死
        Debuger.LogWarningFormat("Context Workflow: 尝试切换到不存在的Phase {0}", phaseString);
    }
}
```

`InitializePhases` 是**内环事件接线的关键**：

```csharp
// Module/Workflow/Workflow.cs:10-17
public virtual void InitializePhases()
{
    foreach(var phase in m_phases.Values)
    {
        phase.addEventListener(WorkflowEvent.SwitchPhase, OnSwitchPhase);   // ★ 给每个 Phase 挂监听
    }
    SwitchPhase(DefaultPhaseName, null, false);   // 落到默认阶段但不执行
}
```

`Start()` 有幂等保护；`Reset()` 回默认阶段但**不执行**：

```csharp
// Module/Workflow/Workflow.cs:42-49, 96-99
public void Start(object data)
{
    if (m_started) return;
    m_currentPhase.Build(data);
    m_started = true;
}

public void Reset(object data = null)
{
    SwitchPhase(DefaultPhaseName, data, false, false);   // execute=false, throwEvent=false
}
```

---

### 1.3 `Phase` —— 手册里的一个步骤

| 项    | 内容                                                                          |
| ---- | --------------------------------------------------------------------------- |
| 是什么  | **玩法内的一个阶段**（准备/运行/清理/切换…）                                                  |
| 代码   | `Assets/Scripts/Module/Workflow/Phase.cs`（141 行），**继承 `KHEventDispatcher`** |
| 数量   | **一 Workflow 4~5 个**（Boot 4 个，Duplicate 5 个）                                |
| 生命周期 | `Build(data)` → `OnBuild()` + `Execute(data)`；`Unbuild()` → `OnUnbuild()`   |
| 特点   | **自己不写业务逻辑，全委托给 Adapter**                                                   |

```csharp
// Module/Workflow/Phase.cs:25-34
public void Build(object data)
{
    OnBuild();
    Execute(data);
}

public void Unbuild()
{
    OnUnbuild();
}
```

```csharp
// Module/Workflow/Phase.cs:50-78
protected virtual void Execute(object data)
{
    activeAdapter.ExecutePhase(data);          // ★ 默认委托给激活的 Adapter
}

public void Execute(object data, object _adapterRalation)
{
    SwitchAdapter(_adapterRalation);           // 先切 Adapter 再执行
    activeAdapter.ExecutePhase(data);
}

protected virtual void Switch(string nextPhase, object data = null)
{
    activeAdapter.SwitchPhase(nextPhase, data);  // ★ 推进也委托给 Adapter
}

public virtual void SendSingal(string singal, object data = null)
{
    activeAdapter.SendSingal(singal, data);
}
```

**构造即装配 Adapter**：

```csharp
// Module/Workflow/Phase.cs:94-115
public Phase()
{
    InitSetting();                                  // setting = PhaseSetting.DefaultPhaseSetting
    RegisterAdapter(setting.AdapterNames);
    SetDefaultAdapter();                            // SwitchAdapter(true)
}

protected virtual void SwitchAdapter(object _key)
{
    string adapterName = setting.AdapterRelations[_key] as string;
    activeAdapter = KHPhaseAdapterFactory.Instance.GetPhaseAdapter(adapterName, this);
}
```

> **Phase 继承 `KHEventDispatcher`** —— 这是"切阶段靠事件驱动"的基础（见 §3 链路 B）。

---

### 1.4 `Adapter`（`KHPhaseAdapter`）—— 这一步的具体做法

| 项   | 内容                                                                   |
| --- | -------------------------------------------------------------------- |
| 是什么 | **同一 Phase 在不同运行态下的差异化实现**                                           |
| 代码  | `Module/PhaseAdapter/KHPhaseAdapter.cs` + `KHPhaseAdapterFactory.cs` |
| 数量  | 一 Phase **1~N 个**，运行期只激活 1 个                                         |
| 创建  | **反射**：`Type.GetType("KH." + 类名)`，缓存在工厂                              |
| 职责  | `ExecutePhase(data)` 干实际活；`SwitchPhase(next)` 派事件推进阶段                |

```csharp
// Module/PhaseAdapter/KHPhaseAdapter.cs:17-35
public virtual void ExecutePhase(object data)
{
}

public virtual void SwitchPhase(string nextPhase, object data = null)
{
    // ★ 关键：派发事件回 Workflow（闭环形成）
    phase.dispatchEvent(new WorkflowEvent(WorkflowEvent.SwitchPhase)
    {
        Argument = new SwitchPhaseArgument() { NextPhaseName = nextPhase, Data = data }
    });
}

public virtual void SendSingal(string singal, object data = null)
{
}
```

工厂反射创建（**要求 Adapter 必须在 `KH` 命名空间下**）：

```csharp
// Module/PhaseAdapter/KHPhaseAdapterFactory.cs:28-57
public KHPhaseAdapter CreatePhaseAdapter(string _name, Phase _parentPhase)
{
    string keyName = string.Format("{0}_{1}", _parentPhase.GetType().ToString(), _name);
    if (expressions.ContainsKey(keyName))
        return expressions[keyName];

    Type type = Type.GetType("KH." + _name);       // ★ 按类名反射
    expression = Activator.CreateInstance(type, _parentPhase) as KHPhaseAdapter;
    expressions.Add(keyName, expression);
    return expression;
}

public KHPhaseAdapter GetPhaseAdapter(string _name, Phase _parentPhase)
{
    ...
    Debuger.LogErrorFormat("[ERROR] 找不到对应的adapter. keyName = {0}", keyName);
    return null;      // ⚠ 返回 null，后续 NPE
}
```

---

### 1.5 `Boot` —— 具体档口之一（启动档）

| 项         | 内容                                                                                    |
| --------- | ------------------------------------------------------------------------------------- |
| 是什么       | **启动/登录期的 Context**（`KHLevelName.BOOT`），游戏第一个 Context                                 |
| 代码        | `Module/Boot/`：`KHBootContext.cs` + `BootWorkflow.cs` + `Phases/`（4 个）+ `BootView.cs` |
| 4 个 Phase | `Boot.Check` → `Login.Default` → `Boot.Switch` → `Boot.Standby`                       |
| 出口        | **只能切去 `GAME`**                                                                       |
| 业务插件      | `Plugin/Boot/`：`BootPlugin` + `LoginModel` + `LoginOperation`                         |

**它和 Context 的关系**：Boot **是一个** Context 实例，不是另一层东西。就像"早餐档"是"档口"的一个实例。

详见 §5。

---

### 1.6 `Duplicate` —— 具体档口之一（PVE 副本档）

| 项         | 内容                                                                                                      |
| --------- | ------------------------------------------------------------------------------------------------------- |
| 是什么       | **PVE 副本玩法 Context**（`KHLevelName.DUPLICATE`）                                                           |
| 代码        | `Module/Duplicate/`：`KHDuplicateContext.cs` + `DuplicateWorkflow.cs` + `Phases/`（5 个）+ `Res/`           |
| 5 个 Phase | `Duplicate.Prepare` → `Duplicate.Main` → `Duplicate.Cleaning` → `Duplicate.Switch` / `Duplicate.Change` |
| 出口        | 可切去 `GAME`（回主城）和 `DAWN`（晓玩法）                                                                            |

详见 §6。

---

## 2. 关系：一张图 + 一张表

```
                    KHGameFlow（店长·唯一）
                          │ SwitchLevel("Boot"/"Game"/"Duplicate"...)
                          │ 校验 SwitchTargetList 白名单
                          ▼
        ┌─────────────────────────────────────────┐
        │  KHGameLevelContext（档口·15 选 1）      │
        │  ┌───────────────────────────────────┐  │
        │  │ Workflow（手册·1:1）                │  │
        │  │  ┌─────────────────────────────┐  │  │
        │  │  │ Phase（步骤·4~5 个）          │  │  │
        │  │  │   ├─ "Boot.Check"            │  │  │
        │  │  │   ├─ "Login.Default"  ◄─当前  │  │  │
        │  │  │   ├─ "Boot.Switch"            │  │  │
        │  │  │   └─ "Boot.Standby"           │  │  │
        │  │  │        │ 委托                  │  │  │
        │  │  │        ▼                       │  │  │
        │  │  │  KHPhaseAdapter（做法·1~N）    │  │  │
        │  │  └─────────────────────────────┘  │  │
        │  └───────────────────────────────────┘  │
        └─────────────────────────────────────────┘
```

|  层  | 类                    |         数量关系        | 职责一句话             | 谁调它                                          |
| :-: | -------------------- | :-----------------: | ----------------- | -------------------------------------------- |
|  调度 | `KHGameFlow`         |          1          | 决定现在跑哪个玩法         | `KHGame.StartGame()`                         |
|  ①  | `KHGameLevelContext` |   15 种（同时只 1 个活跃）   | 一种玩法的生命周期壳        | `KHGameFlow.SwitchLevel`                     |
|  ②  | `Workflow`           |    1 Context : 1    | 玩法内阶段机，管 Phase 切换 | `Context.Build()` → `Workflow.Start()`       |
|  ③  | `Phase`              |   1 Workflow : 4~5  | 玩法内的一个阶段          | `Workflow.SwitchPhase` → `Phase.Build()`     |
|  ④  | `KHPhaseAdapter`     | 1 Phase : 1~N（激活 1） | 该阶段在当前运行态的具体实现    | `Phase.Execute()` → `Adapter.ExecutePhase()` |

> **Boot / Duplicate 不在层级里**——它们是 ①Context 层的**具体实例**，和 `Game`(主城)、`PKNS`(PVP)、`AutoChess`(自走棋) 平级。

### 辅助类

| 文件                                             | 作用                                                                                           |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `Module/Workflow/WorkflowEvent.cs`             | `WorkflowEvent : KHEvent`，`const SwitchPhase="SwitchPhase"` + `SwitchPhaseArgument Argument` |
| `Module/Workflow/SwitchPhaseArgument.cs`       | 切阶段参数：`NextPhaseName` + `Data`                                                               |
| `Module/Workflow/PhaseEvent.cs`                | Phase 级事件定义                                                                                  |
| `Module/Workflow/ContextMessage.cs`            | Context 消息（`KHGameFlow.MessageQueue` / `LoginMessageQueue` 排队处理）                             |
| `Module/PhaseAdapter/KHPhaseAdapterFactory.cs` | 反射创建 + 缓存 adapter                                                                            |

---

## 3. 两条调用链（务必分清）

### 链路 A：切换玩法（Context 之间）

```
业务代码：KHGameFlow.SwitchLevel("Duplicate")
   │
   ├─ 1. if (当前名 != 目标名) 才继续
   ├─ 2. 旧 Context.Unbuild()
   │        └─ Workflow.Reset()    → 回默认 Phase，不执行（execute=false）
   │        └─ 置 null，levelName = UNKNOW
   ├─ 3. GetContextByValue("Duplicate")
   │        └─ if (m_duplicateContext == null)
   │               new KHDuplicateContext() → AddModule → Init()
   │                   └─ new DuplicateWorkflow() → InitializePhases()
   │                        ├─ m_phases.Add(5 个 Phase)
   │                        ├─ 每个 phase.addEventListener(SwitchPhase, OnSwitchPhase)   ← 内环接上
   │                        └─ SwitchPhase("Duplicate.Prepare", execute=false)   ← 落位不执行
   ├─ 4. m_unitySceneLoader.addEventListener(COMPLETE, OnUnitySceneLoaded)
   ├─ 5. KHShaderBundleManager.Instance.OnSceneUnload()       ← 切场景前释放 shader
   ├─ 6. StartCoroutine(m_unitySceneLoader.load("Duplicate"))
   │
   └─ 7. [场景加载完成] OnUnitySceneLoaded(e)
            ├─ (GAME 场景且 EnablePVPWaitingMemoryClean) KHUtil.ReleaseMemoryUntil(...)
            ├─ Context.Build()
            │     ├─ base.Build() → KHUIManager.EnableOpenWindow = true    ← 允许开窗
            │     └─ Workflow.Start(null) → CurrentPhase.Build(null)
            │                                  → OnBuild() + Execute()
            │                                       → Adapter.ExecutePhase()
            └─ KHGlobalRenderPipeline.Instance.SyncKHTimeSinceLevelLoad()
   │
   └─ 8. 无条件派发 GAME_CONTEXT_CHANGE（在 if 外侧，每次 SwitchLevel 都发）
```

关键源码：

```csharp
// GameEntry/KHGameFlow.cs:250-296
public void SwitchLevel(string levelName)
{
    if (!m_currentLevelName.Equals(levelName))
    {
        if (m_currentLevelContext != null)
        {
            m_currentLevelContext.Unbuild();
            m_currentLevelContext = null;
            m_currentLevelName = KHLevelName.UNKNOW;
        }

        m_currentLevelContext = GetContextByValue(levelName);

        if (m_currentLevelContext != null)
        {
            m_currentLevelName = levelName;
            m_unitySceneLoader.addEventListener(KHEvent.COMPLETE, OnUnitySceneLoaded);

            // 切换场景前，把之前持有的shader释放掉；为了防止：sceneloaded后，
            // 可能把一些时序很前的持有shader操作释放。
            KHShaderBundleManager.Instance.OnSceneUnload();

            KHGlobalExt.StartCoroutine(m_unitySceneLoader.load(m_currentLevelName));
        }
    }

    m_evtGameContextChanged.data = levelName;
    KHGlobal.dispatcher.dispatchEvent(m_evtGameContextChanged);   // ⚠ 无条件派发
}

private void OnUnitySceneLoaded(KHEvent e)
{
    m_unitySceneLoader.removeEventListener(KHEvent.COMPLETE, OnUnitySceneLoaded);
    if (m_unitySceneLoader.getCurrentLevelName() == KHLevelName.GAME && DefineExt.EnablePVPWaitingMemoryClean)
        KHUtil.ReleaseMemoryUntil(() => { m_currentLevelContext.Build(); });
    else
        m_currentLevelContext.Build();

    KHGlobalRenderPipeline.Instance.SyncKHTimeSinceLevelLoad();
    ...
}
```

**带白名单校验的安全切换**：

```csharp
// GameEntry/KHGameFlow.cs:233-246
public void TrySwitchLevel(string target)
{
    if (KHUtil.ArrayContains(CurrentContext.SwitchTargetList, target))
    {
        CurrentContext.SendSingal("Switch");
    }
    else
    {
        Debuger.LogErrorFormat("当前场景{0}无法切换到场景{1}", Application.loadedLevelName, target);
        KHGlobal.dispatcher.dispatchEvent(new KHEvent(KHGameEvent.SWITCH_SCENE_FAILD) { data = target });
    }
}
```

---

### 链路 B：推进阶段（Phase 之间）—— 事件驱动闭环 ★最重要

```
当前 Phase 内部（通常在 Adapter 里）调用 Switch("Duplicate.Main")
   │
   ├─ 1. Phase.Switch(nextPhase, data)                [Phase.cs:73]
   │        └─ activeAdapter.SwitchPhase(nextPhase, data)
   │
   ├─ 2. KHPhaseAdapter.SwitchPhase()                 [KHPhaseAdapter.cs:22]
   │        └─ phase.dispatchEvent(new WorkflowEvent(SwitchPhase){ Argument = {NextPhaseName, Data} })
   │             ↑ 注意：是 Phase 自己派发（Phase : KHEventDispatcher）
   │
   ├─ 3. Workflow.OnSwitchPhase(evt)                  [Workflow.cs:85]
   │        （InitializePhases 时给每个 Phase 注册的监听）
   │        └─ SwitchPhase(wfEvent.Argument.NextPhaseName, wfEvent.Argument.Data)
   │
   └─ 4. Workflow.SwitchPhase(name, data, execute:true)   [Workflow.cs:51]
            ├─ 旧 Phase.Unbuild()
            ├─ m_currentPhase = 新 Phase
            ├─ 新 Phase.Build(data) → OnBuild() + Execute() → Adapter.ExecutePhase()
            └─ KHGlobal.dispatcher.dispatchEvent(KHEvent(SwitchPhase))
                  ↑ 外环：给 UI/红点/网络等外部系统旁听
```

**这就是全篇最关键的机制**：

| 通路     | 谁 → 谁                                              | 作用            |
| ------ | -------------------------------------------------- | ------------- |
| **内环** | Phase `dispatchEvent` → Workflow 的 `OnSwitchPhase` | **驱动阶段推进**    |
| **外环** | Workflow → `KHGlobal.dispatcher` 全局广播              | **给外部系统旁路监听** |

> ⚠ **新人最容易踩的坑**：搜"谁调用了 `SwitchPhase`"会**漏掉 90% 的真实切换点**，因为绝大多数切换是**派事件**触发的，不是直接调用。

---

## 4. 15 种 Context 全景

```csharp
// Module/DefineExt.cs:22-39
public class KHLevelName
{
    public const string UNKNOW = "Unknow";
    public const string BOOT = "Boot";
    public const string GAME = "Game";
    public const string DUPLICATE = "Duplicate";
    public const string NNAITRAIN = "NNAITrain";
    public const string PKNS = "PKNS";
    public const string RecordInit = "RecordInit";
    public const string INFINITY_WORLD = "InfinityWorld";
    public const string AUTO_CHESS = "AutoChess";
    public const string DAWN = "Dawn";
    public const string PERFORMANCE = "Performance";
    public const string DODOMEKI_MAIN = "DodomekiMain";
    public const string DODOMEKI_ROOM = "DodomekiRoom";
    public const string PAS = "PAS";
    public const string DODOMEKI_2D = "DODOMEKI_2D";
}
```

| 常量值                             | Context 类                         | 玩法      | 目录                      |
| ------------------------------- | --------------------------------- | ------- | ----------------------- |
| `Boot`                          | `KHBootContext`                   | 启动/登录   | `Module/Boot/`          |
| `Game`                          | `KHMainContext`                   | 主城/主界面  | `Module/Main/`          |
| `Duplicate`                     | `KHDuplicateContext`              | PVE 副本  | `Module/Duplicate/`     |
| `PKNS`                          | `KHPKNSContext`                   | PVP 竞技  | `Module/PKNS/`          |
| `NNAITrain`                     | `KHNNAITrainContext`              | AI 训练   | `Module/NNTrain/`       |
| `RecordInit`                    | `PVPRBLContext`                   | 录像回放初始化 | —                       |
| `InfinityWorld`                 | `InfinityWorldContext`            | 无限世界    | `Module/InfinityWorld/` |
| `AutoChess`                     | `AutoChessContext`                | 自走棋     | `Module/AutoChess/`     |
| `Dawn`                          | `DAWContext`                      | 晓       | `Module/Dawn/`          |
| `Performance`                   | `KHPerformanceContext`            | 演出/性能   | `Module/Performance/`   |
| `DodomekiMain` / `DodomekiRoom` | `DKMainContext` / `DKRoomContext` | 百目鬼     | `Module/Dodomeki/`      |
| `PAS`                           | `PASContext`                      | 3D 战斗   | —                       |

> 每种 Context 都配套一套 `Module/<玩法>/`（`XxxContext.cs` + `XxxWorkflow.cs` + `Phases/*.cs`）。
>   
> 多数玩法 Workflow 遵循 **Prepare → Running → Cleaning → Switch** 四阶段范式。

---

## 5. Boot 专章：启动档口

### 5.1 Boot 是什么

**Boot = 游戏启动期（登录前）**——从进程起来、版本检查、资源/脚本热更、引擎初始化，到玩家点登录进入主城之前的**全部阶段**。名字来自 bootstrap（引导启动）。

> ⚠ **Boot 不是"登录界面"**。登录界面只是 Boot 期间显示的一个 UI（`BootView`），Boot 本身是一个**游戏玩法上下文（Context）**。

### 5.2 四个 Phase

```csharp
// Module/Boot/BootWorkflow.cs:7-25
public override void InitializePhases()
{
    m_phases.Add("Boot.Check", new CheckVersionPhase());
    m_phases.Add("Login.Default", new LoginDefaultPhase());
    m_phases.Add("Boot.Switch", new BootSwitchPhase());
    m_phases.Add("Boot.Standby", new BootStandbyPhase());
    base.InitializePhases();
}

public override string DefaultPhaseName
{
    get { return "Boot.Check"; }
}
```

| 阶段                | 干什么                                                                       | 关键代码                                          |
| ----------------- | ------------------------------------------------------------------------- | --------------------------------------------- |
| **Boot.Check**    | 版本检查 / 热更下载                                                               | `VersionManager.Start()`，监听 `UPDATE_COMPLETE` |
| **Login.Default** | **启动 7 步**：bundle.xml → ILRuntime → Shader 预热 → Lua → 配置表 → 预加载 → MSDK 登录 | 见 `domains/login-flow.md`                     |
| **Boot.Switch**   | 登录收尾：清 UI、清缓存、GC、调 `LoginGame()`                                          | `BootSwitchPhase.goto_next_scene()`           |
| **Boot.Standby**  | 待机（强更等待、登录失败停留）                                                           | —                                             |

### 5.3 只能切去主城

```csharp
// Module/Boot/KHBootContext.cs:42-51
public override string[] SwitchTargetList
{
    get
    {
        return new string[] { KHLevelName.GAME };
    }
}
```

### 5.4 CheckVersionPhase：等动画 → 版本检查 → 全局初始化

```csharp
// Module/Boot/Phases/CheckVersionPhase.cs:30-48
if (isCheck == false)
{
    KHGlobalExt.StartCoroutine(waitRun(() =>
    {
        VersionManager versionMgr = VersionManager.getInstance();
        versionMgr.addEventListener(VersionUpdateEvent.UPDATE_COMPLETE, OnUpdateComplete);
        versionMgr.Start();
    }));
}
else
{
    KHGlobalExt.StartCoroutine(waitRun(() =>
    {
        Switch("Login.Default");     // 已检查过，直接跳过
    }));
}
```

```csharp
// Module/Boot/Phases/CheckVersionPhase.cs:52-62
public IEnumerator waitRun(Action fn)
{
    // 显示进度条,以前作为在版本检查前的一个判断, 以UI的出现作为判断很奇怪,
    // 所以现在单独一个状态标志 by seed
    while (!BootPlugin.isLoginAnimFinished)
    {
        yield return null;
    }
    fn();
}
```

```csharp
// Module/Boot/Phases/CheckVersionPhase.cs:74-92
Action doLogin = () =>
{
    // 执行一个全局的初始化方法,初始化PluginManager以外的模块
    KHGlobalExt.app.BuildGame(true);
    Switch("Login.Default");
};
```

### 5.5 BootSwitchPhase：清场 + 登录，失败回退

```csharp
// Module/Boot/Phases/BootSwitchPhase.cs:127-166
private void goto_next_scene()
{
    if (KHZoneConnection.Instance.IsConnOK)          // ① Zone 连接正常？
    {
        KHGlobal.dispatcher.addEventListener(KHSceneEvent.EXIT_SCENE, onExitScene);
        KH.Network.LoadingTipStack.Hide();
        KHUIManager.Instance.ClearAllWindows();       // ② 清 UI
        KHUIManager.EnableOpenWindow = false;
        KHPluginManager.Instance.ClearPluginResources();
        KHResManager.Instance.ClearUnityCache();
        if (DefineExt.BootSwitchPhaseGC)
            KHResource.UnloadUnusedAssets(true);      // ③ GC
        
        if (KHGame.getInstance().LoginGame())         // ④ 服务器登录
            return;
    }
    /// 如果网络有问题了，或者调用LoginGame失败，则返回登录界面
    Switch("Login.Default");                          // ⑤ 失败回退
    UIAPI.ShowMsgTip("网络突然断开，重新登录！");
}
```

> **文档与代码的出入**：文档称 `BootSwitchPhase` 里 `SwitchLevel("Game")`，实际代码**只调 `LoginGame()` 就 return**，切场景在登录回包后由别处触发。

### 5.6 Boot 的三套东西（别混淆）

| 概念                 | 类型          | 位置                                             | 作用            |
| ------------------ | ----------- | ---------------------------------------------- | ------------- |
| **Boot 场景**        | Unity Scene | `KHLevelName.BOOT`                             | 启动期所在的场景      |
| **`Module/Boot/`** | 状态机代码       | `KHBootContext` / `BootWorkflow` / `Phases/`   | 启动流程的**调度**   |
| **`Plugin/Boot/`** | 业务插件        | `BootPlugin` + `LoginModel` + `LoginOperation` | 启动流程的**业务实现** |

`BootPlugin` 被当作**临时数据容器**用（源码注释自己承认了）：

```csharp
// Plugin/Boot/BootPlugin.cs:20-26
// 这些状态 包括 BootSwitchPhase.loaded应该抽取出来单独一个数据model类中的,
// 现在先将BootPlugin作为model使用了, 减少改动
public static bool isLoginAnimFinished = false;
public static bool isPreloadFinished = false;
public static bool isLoginAnimLoaded = false;
public static GameObject loginBGAnim;
public static RuntimeAnimatorController startupCtrl;
```

`BootView` 是挂在 Boot 场景里的 MonoBehaviour，负责加载登录动画：

```csharp
// Module/Boot/BootView.cs:42-58
/// 这里用静态的，因为这时候plugin还没有初始化，也不去改初始化流程了，它是等到启动动画完后才进行了
BootPlugin.chooseType = chooseType;
BootPlugin.chooseZone = chooseZone;
BootPlugin.defaultZone = defaultZone;
BootPlugin.zoneItem = zoneItem;
BootPlugin.loginHideItem = loginHideItem;
BootPlugin.loadingBar = loadingBar;
BootPlugin.isLoginAnimFinished = false;
BootPlugin.isPreloadFinished = false;
```

> 注意注释：**"这时候 plugin 还没有初始化"** —— Boot 期存在**先有 UI、后有 Plugin 框架**的时序窗口，只能用静态字段硬传。这是启动期代码比较"脏"的根源。

`BootView` 加载登录动画时 `bundle.xml` 还没加载，所以**自己手写了一套 AB 加载**：

```csharp
// Module/Boot/BootView.cs:202-203
// 这个时候游戏的bundle.xml还未加载, 只能自己去加载了
IEnumerator _LoadLoginAnimBundle(string assetBundlePath, System.Action<AssetBundle> callback)
```

---

## 6. Duplicate 专章：PVE 副本档口

### 6.1 结构

```csharp
// Module/Duplicate/DuplicateWorkflow.cs:7-25
public override void InitializePhases()
{
    m_phases.Add("Duplicate.Prepare", new DuplicatePreparePhase());
    m_phases.Add("Duplicate.Main", new DuplicateRunningPhase());
    m_phases.Add("Duplicate.Cleaning", new DuplicateCleaningPhase());
    m_phases.Add("Duplicate.Switch", new DuplicateSwitchPhase());
    m_phases.Add("Duplicate.Change", new DuplicateChangePhase());
    base.InitializePhases();
}

public override string DefaultPhaseName
{
    get { return "Duplicate.Prepare"; }
}
```

| 阶段                   | 类名                       | 职责                            |
| -------------------- | ------------------------ | ----------------------------- |
| `Duplicate.Prepare`  | `DuplicatePreparePhase`  | 准备（含 `PrepareItems/` 13 个准备项） |
| `Duplicate.Main`     | `DuplicateRunningPhase`  | 战斗运行                          |
| `Duplicate.Cleaning` | `DuplicateCleaningPhase` | 结算清理                          |
| `Duplicate.Switch`   | `DuplicateSwitchPhase`   | 切去别的 Context                  |
| `Duplicate.Change`   | `DuplicateChangePhase`   | 换关卡（复用本 Context）              |

### 6.2 出口白名单

```csharp
// Module/Duplicate/KHDuplicateContext.cs:36-46
public override string[] SwitchTargetList
{
    get
    {
        return new string[]
        {
            KHLevelName.GAME,      // 回主城
            KHLevelName.DAWN       // 去"晓"玩法
        };
    }
}
```

### 6.3 生命周期实现（与 Boot 同构）

```csharp
// Module/Duplicate/KHDuplicateContext.cs:7-34
public override void Init()
{
    if (m_workflow == null)
    {
        m_workflow = new DuplicateWorkflow();
        m_workflow.InitializePhases();
    }
    else
        m_workflow.Reset();            // ★ 复用分支
}

public override void Build()
{
    Debuger.LogInfo("KHDuplicateContext.build()");
    base.Build();                       // EnableOpenWindow = true
    m_workflow.Start(null);
    TGPAManager.Instance.UpdateGameScene("Duplicate");
}

public override void Unbuild()
{
    m_workflow.Reset();
}
```

> ⚠ **命名小坑**：类名 `DuplicatePreparePhase` ≠ 注册 key `"Duplicate.Prepare"`。搜代码时搜类名搜不到注册处，要搜**字符串**。

---

## 7. 真实场景串联：启动 → 主城 → 副本 → 回主城

```
【Boot 档口】
KHGame.StartGame()
 └─ KHGameFlow.Start() → SwitchLevel("Boot")
     └─ KHBootContext.Build() → BootWorkflow.Start(null)
         ├─ "Boot.Check"    → VersionManager 版本检查/热更
         ├─ "Login.Default" → 启动 7 步：bundle.xml / ILRuntime / Shader / Lua / 配置 / 资源 / MSDK
         └─ "Boot.Switch"   → 清 UI + GC + LoginGame()
              └─ 登录成功 → SwitchLevel("Game")     ← Boot.Unbuild()，只能去 GAME

【Game 档口（主城）】
KHMainContext.Build() → MainWorkflow.Start()
 └─ MainDefaultPhase
     └─ Adapter 三选一：
          ├─ MainDefaultPhaseAdapter  （基类/通用）
          ├─ MainDefaultPVEAdapter    （PVE 分支）
          └─ MainDefaultPVPAdapter    （PVP 分支）
     玩家点副本 → SwitchLevel("Duplicate")

【Duplicate 档口（PVE 副本）】
KHDuplicateContext.Build() → DuplicateWorkflow.Start()
 ├─ "Duplicate.Prepare"  → 准备（PrepareItems/ 13 个准备项）
 ├─ "Duplicate.Main"     → 战斗运行
 ├─ "Duplicate.Cleaning" → 结算清理
 └─ "Duplicate.Switch"   → SwitchLevel("Game") 回主城
    或 "Duplicate.Change" → 换关卡（复用本 Context）
  ↑ 出口白名单只有 GAME 和 DAWN
```

### 主城 Adapter 差异化（PVE/PVP 分流）

| Adapter（`Module/PhaseAdapter/MainDefault/`） | 运行态   | 差异              |
| ------------------------------------------- | ----- | --------------- |
| `MainDefaultPhaseAdapter`                   | 基类/通用 | 主城默认处理（含 GMQ 等） |
| `MainDefaultPVEAdapter`                     | PVE   | PVE 分支的主城行为     |
| `MainDefaultPVPAdapter`                     | PVP   | PVP 分支的主城行为     |

→ 同一 `MainDefaultPhase`，靠 `SwitchAdapter(key)` 在运行期切换，**Phase 骨架不动**。

这也解释了一个业务判据——"是否在主城主界面"的官方写法：

```csharp
// GameEntry/KHGameFlow.cs:474-489
public bool AbsoluteWithinMainUI
{
    get
    {
        var tCurContext = KHGlobalExt.app.CurrentContext;
        if (tCurContext != null && tCurContext.ContextName == KHLevelName.GAME)
        {
            if (tCurContext.Workflow.CurrentPhase as MainDefaultPhase != null)
                return true;
        }
        return false;
    }
}
```

---

## 8. 代码里发现的 5 个隐患

|  #  | 隐患                                            | 位置                               | 后果                                                            |
| :-: | --------------------------------------------- | -------------------------------- | ------------------------------------------------------------- |
|  1  | **Adapter 缓存按"父 Phase 类型"共享**                 | `KHPhaseAdapterFactory.cs:31-40` | 同类型 Phase 创建两次时，第二个拿到的是指向第一个 Phase 的 Adapter                  |
|  2  | **`GetPhaseAdapter` 失败返回 null**               | `KHPhaseAdapterFactory.cs:55`    | 只 LogError，后续 `activeAdapter.ExecutePhase()` 才 NPE，堆栈误导       |
|  3  | **`SwitchLevel` 无条件派发 `GAME_CONTEXT_CHANGE`** | `KHGameFlow.cs:275-276`（在 if 外）  | 监听方可能收到重复事件                                                   |
|  4  | **切到不存在的 Phase 只 Warning**                    | `Workflow.cs:81`                 | 阶段名写错会**静默卡死**，无异常无报错                                         |
|  5  | **`Type.GetType("KH." + name)` 硬编码命名空间**      | `KHPhaseAdapterFactory.cs:38`    | Adapter 不在 `KH` 命名空间就返回 null → `Activator.CreateInstance` 抛异常 |

---

## 9. 排查速查表

| 现象                    | 定位到                                              | 关键检查点                                                         |
| --------------------- | ------------------------------------------------ | ------------------------------------------------------------- |
| 切玩法没反应 / 切错场景         | `KHGameFlow.SwitchLevel` + 目标 `SwitchTargetList` | 目标是否在白名单；`TrySwitchLevel` 是否报 `SWITCH_SCENE_FAILD`            |
| 阶段卡住不推进               | 当前 Phase 的 Adapter                               | Adapter 是否派了 `WorkflowEvent.SwitchPhase`；`OnSwitchPhase` 是否接住 |
| "尝试切换到不存在的Phase" 警告   | `Workflow.InitializePhases`                      | `m_phases.Add` 的 key 与 `Switch()` 传入的字符串是否一致（**类名 ≠ key 名**）  |
| 找不到对应的 adapter（Error） | `KHPhaseAdapterFactory.GetPhaseAdapter`          | adapter 类名是否匹配 `PhaseSetting.AdapterRelations`；是否在 `KH` 命名空间  |
| 主城 PVE/PVP 行为串了       | `Module/PhaseAdapter/MainDefault/`               | `SwitchAdapter(key)` 选错适配器                                    |
| 启动卡在某阶段               | `Module/Boot/Phases/LoginDefaultPhase.cs`        | 见 `domains/login-flow.md` §二 启动 7 步                           |
| Context 复用后状态残留       | `Context.Init` 里的 `Workflow.Reset()`             | `Reset` 只回默认 Phase 不执行，需自己清状态                                 |
| 进不去战斗 / 战斗卡死          | 见 `state-machine-framework.md` §九                | TAPD 31,415 单模式分析                                             |

---

## 10. 文件位置速查

| 层           | 文件                                                                              | 关键符号                                                                                                                               |
| ----------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 流程管理        | `GameEntry/KHGameFlow.cs`（497 行）                                                | `Start` / `SwitchLevel` / `TrySwitchLevel` / `GetContextByValue` / `BuildWorkflowAdapters`                                         |
| Context 基类  | `Module/KHGameLevelContext.cs`（50 行）                                            | `Init/Build/Unbuild/Final` / `Workflow` / `SwitchTargetList` / `SendSingal`                                                        |
| 常量定义        | `Module/DefineExt.cs:22-39`                                                     | `KHLevelName` 15 个常量                                                                                                               |
| Workflow 基类 | `Module/Workflow/Workflow.cs`（101 行）                                            | `m_phases` / `InitializePhases` / `SwitchPhase` / `OnSwitchPhase` / `Reset`                                                        |
| Phase 基类    | `Module/Workflow/Phase.cs`（141 行）                                               | `Build/Unbuild` / `OnBuild/OnUnbuild` / `Execute` / `SwitchAdapter` / `RegisterAdapter`                                            |
| Adapter     | `Module/PhaseAdapter/KHPhaseAdapter.cs` + `Factory`                             | `ExecutePhase` / `SwitchPhase`(派事件) / 反射 `Type.GetType("KH."+name)`                                                                |
| 辅助类         | `Module/Workflow/WorkflowEvent.cs` 等                                            | `WorkflowEvent` / `SwitchPhaseArgument` / `ContextMessage`                                                                         |
| Boot 样板     | `Module/Boot/`                                                                  | `KHBootContext` / `BootWorkflow` / `CheckVersionPhase` / `LoginDefaultPhase` / `BootSwitchPhase` / `BootStandbyPhase` / `BootView` |
| Boot 业务     | `Plugin/Boot/BootPlugin.cs`                                                     | `BootPlugin` / `LoginModel` / `LoginOperation`                                                                                     |
| Duplicate   | `Module/Duplicate/`                                                             | `KHDuplicateContext` / `DuplicateWorkflow` / 5 个 Phase / `PrepareItems/`                                                           |
| 各玩法         | `Module/{AutoChess,Dawn,PKNS,InfinityWorld,Dodomeki,Main,NNTrain,Performance}/` | `XxxContext` / `XxxWorkflow` / `Phases/`                                                                                           |

---

## 11. 与其它框架的衔接

状态机是**调度者**，其它框架是**被调度的能力**：

| 框架                | 被谁拉起                     | 代码证据                                                                      |
| ----------------- | ------------------------ | ------------------------------------------------------------------------- |
| `KHPluginManager` | `KHGameFlow.BuildGame()` | `KHGameFlow.cs:178` `KHPluginManager.Instance.initializePlugins(isAsync)` |
| `VersionManager`  | `CheckVersionPhase`      | `CheckVersionPhase.cs:36-38`                                              |


| `KHDataManager` | `KHGameFlow.OnLoadComplete()` | `KHGameFlow.cs:196` `KHDataManager.getInstance().PostProcess()` |
  
| `KHUIManager` | Context 基类 `Build()` | `KHGameLevelContext.cs:31` `EnableOpenWindow = true` |
  
| `KHZoneConnection` | `BootSwitchPhase` 检查 | `BootSwitchPhase.cs:129` |
  
| `KHResManager` | `BootSwitchPhase` 清缓存 | `BootSwitchPhase.cs:145` |

```
KHGame → KHGameFlow → Context → Workflow → Phase → Adapter
                                              ↓
                               Plugin 框架 / UI 框架 / 网络 / 资源 / 配置
```

**理解项目的正确顺序**：先抓 `KHGameFlow → Context → Workflow → Phase → Adapter` 这条主干（一共 5 个类、不到 1000 行），再学 Plugin / Act / UI / 网络——你会清楚知道"我写的这段业务代码，是被哪个 Phase 拉起来的"。

---

## 12. 记忆口诀

| 问题                    | 答案                                                                      |
| --------------------- | ----------------------------------------------------------------------- |
| Context 决定什么？         | **在哪个玩法**（档口）                                                           |
| Workflow 决定什么？        | **流程怎么走**（手册）                                                           |
| Phase 决定什么？           | **现在走到哪一步**（步骤）                                                         |
| Adapter 决定什么？         | **这一步具体怎么做**（做法）                                                        |
| Boot / Duplicate 是什么？ | **Context 的具体实例**，和其它玩法平级                                               |
| 切玩法走哪条链？              | 链路 A：`SwitchLevel` → `Unbuild` → 懒创建 → 载场景 → `Build` → `Workflow.Start` |
| 推进阶段走哪条链？             | 链路 B：`Switch` → Adapter 派事件 → `OnSwitchPhase` → `SwitchPhase`           |

> **三层职责正交，互不越权** —— 这是整套设计的核心。

---

## 相关笔记

- [[KiHan 框架阅读索引]]（系列总索引，建议从这里开始）
- [[KiHan Manager台账速查]]（78 个 Manager 谁管什么）
- [[KiHan Plugin框架详解]]（C# 业务被 Phase 拉起）
- [[KiHan热更双引擎详解]]（Boot 期 LoginDefaultPhase 做了什么）
