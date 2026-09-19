---
title: KiHan 项目认知清单
tags: [KiHan, 认知清单, checklist, 新人入门, MOC]
created: 2026-09-18
source: Others/AIDev/context/{framework, entities, domains}（截图框选三层）
---

# KiHan 项目认知清单

> 对应知识库 `AIDev/context/` 的三层核心（截图红框）：
>
> | 层 | 回答的问题 | 谁写的 | 认知目标 |
> |---|---|---|---|
> | `framework/` | **用什么造**——框架/库怎么用 | 人工通读源码 | 懂机制 |
> | `entities/` | **造了什么**——单个模块是什么 | 工具批量 + 人工深度 | 会检索 |
> | `domains/` | **怎么串起来**——跨模块规律 | 人/AI 二次提炼 | 通链路 |
>
> 用法：Obsidian 里直接点击方框打勾。每条尽量附"自验标准"——能讲给别人听才算过。

---

## A. framework 层认知（懂机制）🏗️

### A1. 调度主干

- [ ] **状态机四层**：能画出 Context → Workflow → Phase → Adapter 的层级图，并说出各层职责
	→ [[KiHan状态机架构详解]]
- [ ] **15 种 Context**：能说出 Boot/Game/Duplicate/PKNS 各是什么玩法，`SwitchTargetList` 白名单是干嘛的
- [ ] **Boot 语义**：知道 Boot = 启动期（版本检查→启动7步→服务器登录），不是"登录界面"；只能切去 Game
- [ ] **事件双通路**：知道切阶段靠 Phase 派 `WorkflowEvent`（内环），搜"谁调 SwitchPhase"会漏 90% 切换点
- [ ] **Adapter 反射装配**：知道按类名 `Type.GetType("KH."+name)` 创建，PVE/PVP 差异在 Adapter 层

### A2. 业务双主干

- [ ] **Plugin 四基类**：Plugin(Controller)/Operation(行为)/Model(数据)/View(界面)，靠消息字符串解耦
	→ [[KiHan Plugin框架详解]]
- [ ] **三个反射魔法**：`[Operation("消息名")]`、`[UpdateProcessor(cmdId)]`、`base.RegisterOperations()` 注入 ViewOperation——以及各自搜不到代码的原因
- [ ] **Views[] 反查钥匙**：Plugin 名 → Views[] → UIDef.cs → prefab 路径 → View 脚本
- [ ] **8 种 Plugin 形态**：知道先学 MVC 标准型（NinjaBattleField），Shopping/Arena 是 Lua 主导别照抄
- [ ] **Plugin vs Act 边界**：长期系统功能 → Plugin；限时运营活动 → Act
- [ ] **ActFramework**：5 种 Entity 选型、11 个标准 Component、编码优先级四级铁律（内置→ActLib→CS.*→老全局别用）
	→ [[KiHan ActFramework详解]]

### A3. 表现与交互

- [ ] **UI 三层体系**：NGUI（渲染）→ UIWindow（视图基类）→ View（业务），KHUIManager 全局管控
	→ [[KiHan UI框架详解]]
- [ ] **生命周期真实顺序**：`OnInitData` 早于 `OnOpenWindow`（数据放前者，渲染放后者）
- [ ] **关闭 ≠ 销毁**：普通 Close 只 Hide 复用 → OnCloseWindow 必须清监听/定时器
- [ ] **双层级模型**：WindowLayer（大层）× LayerDepth（层内深度），depth 动态重排
- [ ] **TUI 组件库**：知道搭 UI 查 `tui-component-library.md` + 按 `mockup-to-tui-prefab` SOP 走

### A4. 基础设施

- [ ] **网络五层栈**：NetworkManager → KiHanProxy → Connection → MessageRouter → Thread&Queue
	→ [[KiHan 网络框架详解]]
- [ ] **9 种连接**：能说出 GAME/UDP/PVP/OB/AUTOCHESS/STATUS_SCENE 各走 TCP 还是 UDP
- [ ] **重连真相**：GCloud 自动重连被有意关闭，全靠自研 Reconnector；static 字段竞态是已知故障 F1
- [ ] **资源六层**：门面→三 Loader→调度→缓存(软LRU)→IO线程→Unity API
	→ [[KiHan 资源加载框架详解]]
- [ ] **编辑器陷阱**：Editor Loader 无缓存无卸载，内存/缓存问题必须真机验
- [ ] **热更三语三层**：AOT(❌) / ILRuntime(✅) / Lua(✅)，判定入口 `createMode 0/1/2`
	→ [[KiHan热更双引擎详解]]
- [ ] **xLua 单 VM**：没有 SLua 双引擎；核心在 `Packages/khengine/Runtime/Lua/`
- [ ] **四通道更新**：出包/资源/IL/Lua；VersionManager 只管下载，生效在 LoginDefaultPhase
- [ ] **Manager 全景**：78 个 Manager、5 种单例形态、核心 16 个有专篇
	→ [[KiHan Manager台账速查]]
- [ ] **事件双轨**：FlashLikeEvents（字符串，UI级）vs KHEventDispatcher/KHEvent（自研 DLL，继承式）
- [ ] **红点系统**：双通道推送 + 三类红点 + LockSysHash 三向映射
- [ ] **场景两代**：CityWorld（传统）vs StsyScene（状态同步：WorldState + state_version + 增量同步）
- [ ] **协议双份**：csharp-proto（kihan.proto，380 文件）/ lua-proto；三种通信模式见 protocol-patterns

---

## B. entities 层认知（会检索）🎯

### B1. 结构与分级

- [ ] **规模**：1043 Act + 144 Plugin = 1187 实体 + ~30 篇 system 深度篇 + 6 张配置表
- [ ] **三层质量分级**（最重要的认知）：

	| 子类 | 性质 | 怎么用 |
	|---|---|---|
	| `acts/` `plugins/` | 机械生成 `ai-batch`，浅层文件清单 | 只做找同类样板 |
	| `system/` | 人工源码级 `high` | 最有学习价值 |
	| `config/` | 配置表机械事实 | 配合 kh-config-qa |

- [ ] **对比读法**：拿一篇 system/ 深度篇和同名浅层篇对比过（如 badge-system vs Badge_徽章系统）
- [ ] **system 标准结构**：机制→数据链路→协议全景→N套编号→风险清单→排障速查→**范式对比**

### B2. 检索技能

- [ ] 会用 `domains/act-taxonomy.md` 按 28 个 domain 找同类活动样板
- [ ] 会用 `domains/INDEX.md` 高频问题索引（问题关键词 → 文档）
- [ ] 知道 system/ 里最复杂的几篇在哪：guild / item / payment / recruit / ninja-weapon / psychic / secretscroll
- [ ] 配置表：会走 `kh-config-qa` 答疑流程（先 paths.py 校验根目录）；会查 `entities/config/INDEX.md`
- [ ] 会用 `kb_query.py` 查 Lua 符号/影响面/用法示例，且**知道 C# 符号为 0 的覆盖边界**

---

## C. domains 层认知（通链路）🌐

- [ ] **login-flow**：冷启动/登出/重登录/断线重连四态，串 GameEntry→网络→状态机→数据
- [ ] **update-flow**：两层心智模型（传输安装层 vs 消费加载层），"热更不生效"会二分定位
- [ ] **protocol-patterns**：`[Operation]` 反射 vs `SendCmdHandleForAct` vs 直发+Push 三种写法及选用
- [ ] **module-boundary-constraints**：跨模块嵌入的禁区，**接到需求先查这里**
- [ ] **ui-entry-refresh**：入口/红点刷新时机；ReqActEntryInfo 链路
- [ ] **ui-architecture-evolution**：UI 基类三代演进 LuaBehaviour→LuaUIWindow→ActBehaviourEntity
- [ ] **battle-context-flow**：进战 6 段流水 + 13 Context 注册表（接触战斗时读）
- [ ] **config-pipeline**：Excel→导出→加载→消费及前后台分流
- [ ] **缺陷分类体系**：9 类 defect-type（redpoint/network/ui-interaction/…）+ 5 类 discovery（crashsight/tapd/…）两轴交叉
- [ ] **bug 知识管线**：证据(实体文档) → 模式(缺陷模式卡) → 处置(troubleshooting) → 规范(ADR)

---

## D. 横切纪律（随时自查）📏

- [ ] `AGENTS.md` §二意图路由表——任何检索先命中"第一站"
- [ ] `confidence` 7 档——`ai-batch/ai-draft` 必须回源码复核
- [ ] S/W/N 检索分层——rules/workflows 顺流程走，别指望搜到
- [ ] 三条铁律：逐层下钻 INDEX / 查不到登记 GAPS / 绝不臆造路径
- [ ] 改代码前查 `file-to-docs.md`（文件名反查知识文档）

---

## E. 自测题（全勾完再验一次）

> 每题 30 秒内能说清思路即通过。

1. 玩家在主城点副本进入战斗，经过哪些层？（状态机链路 A + DuplicateContext）
2. 改了一段 C# 代码，怎么判断能不能热更？（createMode + 四通道）
3. 界面打开了但数据不显示，先查什么？（OnInitData vs OnOpenWindow 顺序）
4. 某活动的界面文件在哪？（act-taxonomy → entities/acts/ → Views[]/UIDef 反查）
5. 红点不刷新，走哪篇文档？（redpoint-framework + redpoint-guard）
6. 服务器登录成功但进不去主城，怎么二分？（login-flow + BootSwitchPhase 链路）
7. 发消息给 Plugin 没反应，三个可能原因？（消息名拼错/Lua Hook 拦截/没注册）
8. 收到网络回包但 Model 没处理，查什么？（[UpdateProcessor] 标签 + cmdId + Registers 总表）
9. 评估一个跨模块需求，第一步做什么？（feasibility-check-rule + module-boundary-constraints）
10. 文档说的和你测的不一致，怎么办？（查 confidence → 回源码 → 登记 GAPS）

---

## 相关笔记

- [[KiHan 框架阅读索引]] —— 框架系列 9 篇总入口（A 区的展开）
- [[KiHan 新人知识库阅读路线]] —— 分阶段读库路线（本清单的"过程版"）
- 本清单是"**结果验收**"：路线是怎么走，清单是走到没有
