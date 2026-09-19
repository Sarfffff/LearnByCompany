---
title: KiHan ActFramework 详解（Lua 活动框架：Entity + Component）
tags: [KiHan, 架构, Act, Lua, 活动]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/actframework.md（源码：LuaScript/KiHan/ActFramework/ ~75 个 .lua.txt）
---

# KiHan ActFramework 详解

> Lua 活动框架。**1000+ 个 Act**（限时运营活动）的统一写法。
> 源码：`Assets/Resources/LuaScript/KiHan/ActFramework/`，五层结构（Base / Entity / Component / HFSM / Data）

---

## 0. 一句话总览：乐高类比

| 概念 | 类比 |
|---|---|
| `Entity` | **乐高底盘**（选哪种底盘决定活动形态） |
| `Component` | **标准积木块**（网络/UI事件/红点/定时器…插上就能用） |
| `ActLib` | **工具箱**（通用函数库） |
| `HFSM` | **变速箱**（分层状态机，桥接 C# StateMachineWrapper） |

---

## 1. 五层目录结构

| 目录 | 内容 |
|---|---|
| `Base/` | `ActEntityBase`（Component 容器+生命周期驱动）、`ActComponentBase`（CopyType 机制 + F2EE 拷贝）、`ComponentDefine` |
| `Entity/` | 5 种核心 Entity + UI/ Mesh/ AggregatePages/ MiniGame 四个子目录 |
| `Component/` | 11 个标准 Component + AI/ Mesh/ ActMiniGame |
| `HFSM/` | `LuaMotionFsmBase` + `LuaStateBase` + `LuaTransitionBase` |
| `Data/` | `ActStableData`（不受 GC 清除的稳定数据） |

### 5 种核心 Entity（选型决策）

| Entity | 用途 | Component 数 |
|---|---|---|
| `ActEntity` | 基础活动 | Network + Mock + UIBindData |
| `ActBehaviourEntity` | **完整活动面板**（活动中心内嵌） | 10 |
| `ActUIWindowEntity` | 独立入口窗口 | — |
| `ActPopupWindowEntity` | 弹窗（Wrapper） | 8 |
| `ActEvtInterfaceEntity` | 纯事件接口（无界面） | 8 |

### 11 个标准 Component（按需插拔）

`Network`（通信）/ `UIEvt` / `BtnEvt` / `UIBindData`（20+ 种 Bind）/ `CustomEvt` / `GameEvt` / `RedPoint` / `Timer` / `StateMachine` / `UIGroup`（互斥）/ `MokeDebug`（Mock 调试），另有特效裁剪父子、AgpData、AI 行为树等。

---

## 2. 编码优先级铁律 ★（最重要的一节）

```
1. Entity 内置能力（__protected.SendActCmd / SetTimer / OnRegBtnEvents / DelayRefreshActRP）
      ↓ 框架没有时
2. ActLib 模块（ActLib.UIUtil / NGUIUtil / Network / Audio / PopUp / PlayerInfo）
      ↓ ActLib 没有时
3. 直接调 CS.*（CS.UnityEngine.* / CS.KH.*）—— 最低优先级
      ↓
4. LuaScript/utils/ 老式全局函数 —— 遗留，均有替代：
   SendCmdHandleForAct   → __protected.SendActCmd(cmd, arg)
   HandleErrorCode       → __protected.OnRspError(retCode, retMsg, cmd)
   ShowPanelHandleForAct → ActLib.UIUtil.ShowPanelForAct / ShowPanel
```

**扩展原则**：

| 场景 | 做法 |
|---|---|
| 整块逻辑需复用 | 提取到 ActLib（判断"足够通用"：≥2 个活动用、不依赖特定活动数据） |
| 基础设施缺失 | 扩 ActFramework：新增 Component（继承 ActComponentBase）或 Entity |
| `CS.*` 裸调用频繁 | 封装成 `ActLib_XXX.lua.txt` 收口 |

---

## 3. 与 Plugin 框架的边界

| | ActFramework | Plugin 框架 |
|---|---|---|
| 语言 | Lua | C# |
| 目标实体 | 限时活动 Act（1000+） | 长期系统 Plugin（144） |
| 注册 | `ActCenterPlugin` 子注册 | `KHPluginManager` 全局 |
| 生命周期 | 活动期内（有限） | 持续（部分常驻） |
| 范式 | Entity + Component 组合 | MVC（Plugin/Model/Operation/View） |

---

## 4. 必知重点与坑

1. **选基类先查样板**：`domains/act-taxonomy.md` 按 28 个 domain 分组，**先找同类活动抄骨架**，别照错样板
2. **老式全局函数是反例**：新代码用 Entity 内置 / ActLib；`iEachOne`、`List_New` 等 C# 集合桥接函数无替代仍需使用
3. **UI 基类三代演进**：`LuaBehaviour → LuaUIWindow → ActBehaviourEntity`，新活动一律用新式 Entity
4. **模板刷新**：改 `templates/act-analysis-template.md` 后要重跑 `tools/probe_act.py` 增量刷新实体文档（幂等安全）

---

## 5. 排查速查

| 现象 | 先查 |
|---|---|
| 活动面板打不开 | Entity 选型对不对；是否走了 ActCenterPlugin 注册 |
| 发协议没反应 | 用 `__protected.SendActCmd` 还是老 `SendCmdHandleForAct`；协议号对不对 |
| 红点不刷新 | `__protected.DelayRefreshActRP` 是否调用；ActRedPointComponent 是否挂上 |
| 找同类参考 | `domains/act-taxonomy.md` → `entities/acts/Act_{ID}.md` |
| 活动策划案原文 | `kb_query.py get_design_doc <活动号>`（改老活动前必读） |

---

## 6. 记忆口诀

> **Entity 是底盘，Component 是积木，ActLib 是工具箱；**
> **能力四级找：内置 → ActLib → CS.* → 老全局（别用）。**

## 相关笔记

- [[KiHan Plugin框架详解]]（C# 侧对照）
- [[KiHan状态机架构详解]]（Act 被哪个环节调度）
