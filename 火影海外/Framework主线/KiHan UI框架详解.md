---
title: KiHan UI 框架详解（UIWindow + KHUIManager + TUI 组件库）
tags: [KiHan, 架构, UI, NGUI, TUI, UIWindow]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/ui-framework.md + tui-component-library.md + ngui-framework.md
---

# KiHan UI 框架详解

> 基于 NGUI 的自研 UI 框架。**UIWindow** 是所有视图基类（557 行），**KHUIManager** 是全局基础设施（~2630 行，95KB）。
> 关联文档：`ui-framework.md`（全景）、`tui-component-library.md`（组件库）、`ngui-framework.md`（渲染层）、`main-ui.md`（主界面入口）、`redpoint-framework.md`（红点）

---

## 0. 一句话总览：剧院类比

| 层 | 类比 | 职责 |
|---|---|---|
| NGUI 层 | **舞台灯光设备** | UIPanel / UIWidget / UICamera（渲染+输入），KiHan 定制版 3.5.7，122 类 |
| UIWindow 层 | **剧场管理制度** | 开关动画、层级、异形屏、Modal、音效（自研） |
| View 层 | **具体剧目** | 业务 View（继承 UIWindow，嵌 ViewArg 输入模型） |
| KHUIManager | **剧院经理** | 所有 View 的生命周期/层级/事件 |

---

## 1. 核心机制

### 双层级模型

- `WindowLayer`（大层，权威定义在 `Data/UIDef.cs`）
- `UIDef.LayerDepth`（层内深度）
- depth 会**动态重排**

### UIWindow 生命周期 ★注意真实顺序

```
Prefab 实例化（KHUIManager）
  → Awake()
      ├─ OnInitWindow()            绑控件、注册事件
      ├─ OnInitWindowCompleted()   延迟一帧，子节点就绪
      └─ IPX Bound 初始化（18:9 异形屏）
  → OnInitData(object _data)       ★ 早于 OnOpenWindow！收 ViewArg 准备数据
  → OnOpenWindow()                 ★ 后触发！数据已就绪，做首次渲染
  → OnReOpenWindow(object)         已打开又被重开（复用，不重建 Prefab）
  → [可见期间] IsAnimating 管理交互屏蔽
  → PlayCloseWindowAni() → OnCloseWindow()   关闭动画完成（清订阅/停定时器）
  → DoCloseWindow() → OnDestroyWindow()      仅 DestroyWindow 路径（真销毁）
```

### 关闭 ≠ 销毁 ★最高频的坑

- 普通 `CloseWindow` → 只 `HideWindow`（SetActive false），**实例保留复用**
- 只有 `DestroyWindow` 路径 → `DoCloseWindow` 真销毁
- → **`OnCloseWindow` 里必须清干净监听/定时器，否则复用时报残留 bug**

### 三级触摸屏蔽

- 打开/关闭动画期间 `IsAnimating = true` 全局屏蔽 UI 触摸
- 动画完成且无其它窗口在动画时恢复
- 完整三级机制见 `ui-framework.md` §3.16

---

## 2. 关键可重写方法速查

| 方法 | 时机 | 典型用途 |
|---|---|---|
| `OnInitWindow()` | Awake 第一帧 | 绑 NGUI Widget、注册 EventListener |
| `OnInitWindowCompleted()` | 延迟一帧 | 子节点就绪后操作 |
| `OnInitData(object)` | 打开时（**早于 OnOpen**） | 接 ViewArg、备数据 |
| `OnOpenWindow()` | 数据就绪后 | 首次渲染、弹 Tips |
| `OnReOpenWindow(object)` | 已存在被重开 | 刷新数据（不重建） |
| `OnCloseWindow()` | 关闭动画完成 | **注销监听、停定时器** |
| `OnDestroyWindow()` | Destroy 前 | 清 Model 引用、释放资源 |

---

## 3. TUI 组件库

- NGUI 之上的**自研组件库**（`framework/tui-component-library.md`，48KB 全量手册）
- 分组：Normal / Icon / Button / Player / Ninja / 通用 View / Template
- **按示意图搭 UI**：走 `workflows/mockup-to-tui-prefab.md` SOP（识别原则：**按结构信号，不按业务名**）

## 4. 与其它系统衔接

| 系统 | 关系 | 文档 |
|---|---|---|
| Plugin 框架 | View 由 Plugin 的 `Views[]` 注册，经 ViewOperation 打开 | [[KiHan Plugin框架详解]] |
| 红点 | `KHRedPointManager` 双通道 + LockSysHash 三向映射 | `redpoint-framework.md` |
| 主界面入口 | `BtnDestination`/`StateBit`/`open_sys ID` 三套编号 + `CanUnlock` 判定 | `main-ui.md` |
| UI 基类演进 | `LuaBehaviour → LuaUIWindow → ActBehaviourEntity` 三代 | `domains/ui-architecture-evolution.md` |

---

## 5. 排查速查

| 现象 | 先查 |
|---|---|
| 界面数据不显示 | `OnInitData` vs `OnOpenWindow` 顺序搞反了（数据要放前者） |
| 复用后状态残留 | `OnCloseWindow` 没清监听/定时器 |
| 点击穿透/失灵 | IsAnimating 屏蔽窗口；三级触摸屏蔽（§3.16） |
| 层级穿层/遮挡 | WindowLayer / LayerDepth 配置；depth 动态重排 |
| 异形屏错位 | IPX Bound（`KHUIManagerAdapter` 有 Loading 类特例） |
| 入口不显示 | `main-ui.md` 的 LockSysHash 判定链 + static 解锁快照（换区残留 F1） |

---

## 6. 记忆口诀

> **数据进 OnInitData，渲染放 OnOpenWindow；**
> **关闭只藏不销毁，OnClose 清理要做全；**
> **层级两把尺：WindowLayer 定层，LayerDepth 定位。**

## 相关笔记

- [[KiHan Plugin框架详解]]（谁打开 View）
- [[KiHan 网络框架详解]]（数据从哪来）
