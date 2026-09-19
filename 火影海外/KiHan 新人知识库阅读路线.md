\---  
title: KiHan 新人知识库阅读路线

tags: [KiHan, 新人入门, 知识库, 阅读路线]

source: Others/AIDev/context/{framework,domains,entities}

created: 2026-09-18  
\---

# KiHan 新人知识库阅读路线

> 适用对象：刚接手 KiHan 项目的开发/策划/测试新人
>
> 知识库根目录：`Others/AIDev/`（SVN 管理），本文所有相对路径均以此为基准

---

## 0. 先记住一句话

**不要一头扎进 `entities/` 的 1043 篇 Act 文档。** 正确顺序是：

```
建坐标系（overview + 路由 + 规则）
   → 读框架（framework/，最稳定）
   → 用领域文档串联（domains/）
   → entities/ 只按任务按需检索
```

配套认知：全库 **1862 篇**文档中约 **2/3 是 AI 生成未经人工核实**。每篇文档头部都有 `confidence` 字段，它决定你能信几分。

| confidence                     | 含义                          | 检索权重 | 能否当结论   |
| ------------------------------ | --------------------------- | :--: | ------- |
| `high`                         | 人工核实 / 源码级证据（带 `file:line`） |  1.0 | ✅ 可以    |
| `medium`                       | 主干可信、细节待验                   |  0.8 | ⚠️ 主干可用 |
| `ai-llm-analysis`              | LLM 深度分析产出，未核实              |  0.5 | ❌ 仅参考   |
| `ai-batch`                     | 批量生成，未核实（entities 主力）       |  0.4 | ❌ 仅线索   |
| `ai-draft` / `low` / `pending` | 草稿 / 低置信 / 待定               |  0.3 | ❌ 仅线索   |

---

## 1. 阶段 0：建坐标系（半天）

这一步不看 `framework/domains/entities`，先建立"项目长什么样 + 怎么找东西"的地图。

|  顺序 | 读什么                                              | 拿到什么                                                                                             |
| :-: | ------------------------------------------------ | ------------------------------------------------------------------------------------------------ |
|  1  | `AGENTS.md` §一 §二 §三                             | 全库**唯一总路由**（意图路由表）+ AI 检索 SOP + 五条铁律                                                             |
|  2  | `context/overview/system-architecture-map.md`    | 13 组系统 → 各层权威文档导航，一页看清骨架                                                                         |
|  3  | `context/overview/code-distribution-overview.md` | 20,151 C# + 8,997 Lua 的分布，"代码在哪"                                                                 |
|  4  | `context/overview/project-navigation.md`         | 精确路径规则（找源文件第一站）                                                                                  |
|  5  | `rules/INDEX.md` 中 4 篇                           | `naming-convention` / `analysis-discipline` / `lua-method-call-style` / `feasibility-check-rule` |
|  6  | `context/INDEX.md` 的 confidence 与 defect-type 段  | 可信度枚举、9 类缺陷分类、5 类发现来源                                                                            |

> `rules/` 是**每次会话必读**的硬约束，优先级高于一切默认行为。

---

## 2. 阶段 1：framework/ 主线（3~5 天）

`framework/` 回答「用什么造」，最稳定、最值得精读。**按依赖顺序读，不要乱跳。**

|  #  | 文档                                                     | 读完应能回答                                           |
| :-: | ------------------------------------------------------ | ------------------------------------------------ |
|  1  | `state-machine-framework.md`                           | 游戏怎么在启动/主城/副本/PVP 间切换？Boot→登录界面完整链路？             |
|  2  | `plugin-framework.md`                                  | C# 业务模块怎么写？Plugin / Operation / Model / View 四基类 |
|  3  | `actframework.md` + `actlib-api.md`                    | Lua 活动怎么写？Entity + 11 Component                  |
|  4  | `ui-framework.md` + `tui-component-library.md`         | 界面怎么开、层级怎么排、组件有哪些                                |
|  5  | `network-framework.md`                                 | 五层栈、9 种连接、为什么重连全靠自研 `Reconnector`                |
|  6  | `res-load-framework.md`                                | 六层加载链路、三种 Loader、软 LRU 缓存                        |
|  7  | `lua-runtime-framework.md` + `il-runtime-framework.md` | 两套热更通道（xLua 单 VM / ILRuntime 多域）                 |
|  8  | `framework/manager/INDEX.md`                           | 78 个 Manager 台账与优先级分级                            |

### 各篇必抓重点

**① 状态机四层（最核心）**

```
KHGameFlow            流程管理器（唯一）SwitchLevel("Boot"/"Game"/"Duplicate"...)
  ↓
KHGameLevelContext    15 种玩法上下文 + SwitchTargetList 切换白名单
  ↓
Workflow              一 Context 一个，管 Phase 字典与切换
  ↓
Phase : KHEventDispatcher   一 Workflow 若干阶段
  ↓
KHPhaseAdapter        同一 Phase 按运行态（PVE/PVP）差异化，反射装配
```

- 职责正交：Context 定"哪个玩法"，Phase 定"哪一步"，Adapter 定"当前运行态怎么做"
- 切阶段靠**事件驱动**：Phase 派 `WorkflowEvent` → Workflow 接住再切，二者解耦
- Adapter 按类名字符串 `Type.GetType("KH."+name)` 反射创建，新增运行态**不改 Phase 代码**

**② Plugin 四基类**

- Plugin = Controller，Model = 数据，Operation = 行为单元，**三者靠消息字符串解耦**
- `[Operation("MsgName")]` 注册路由；`[UpdateProcessor(cmdId, Type)]` 注册 Model 网络回调
- `base.RegisterOperations()` 会注入 `ViewOperation`，自动响应 `ShowView/HideView/...`
- ⭐ `PluginSetting.Views[]` 是 Plugin 反查的钥匙——该 Plugin 所有 View 都在这里

**③ ActFramework 编码优先级铁律**

```
1. Entity 内置能力（__protected.SendActCmd / SetTimer ...）
2. ActLib 模块（ActLib.UIUtil / Network / NGUIUtil ...）
3. 直接调 CS.*（CS.UnityEngine.* / CS.KH.*）
4. 老式全局函数（SendCmdHandleForAct 等遗留，已被替代）
```

- 发现 CS 裸调用频繁 → 封装进 ActLib；发现基础设施缺失 → 扩 ActFramework

**④ UI 三个高频坑**

- 生命周期真实顺序：`OnInitData(object)` **早于** `OnOpenWindow()`
- 普通 `CloseWindow` **只 Hide 不销毁**（实例复用）→ `OnCloseWindow` 必须清干净监听/定时器
- 双层级模型：`WindowLayer`（大层）× `UIDef.LayerDepth`（层内深度），depth 会动态重排

**⑤ 网络**

- GCloud 自带自动重连**被有意关闭**，断线统一走 `Error → OnDisconnected → 自研 Reconnector 三次重连`
- 已知 F1：`Reconnector` 的 `_retrytimes` 等字段是 **static 共享**，Zone/自走棋/OB 三类连接并发争用

**⑥ 热更两套（破除旧认知）**

- 全工程 `using SLua` 命中 **0 次**——**没有双引擎**，只有 xLua
- `new LuaEnv()` 全工程只一处，V1/V2 **共享同一个 VM**
- Lua 框架核心不在 `Assets/Scripts/`，在 `Packages/khengine/Runtime/Lua/`

> **读法**：每篇先看 `confidence` → 扫目录 → 直接跳「故障模式 / 排障速查」章节（带 `file:line` 的清单密度最高）。35KB 的 `ui-framework.md` 拆 3 次读，不要通读。

---

## 3. 阶段 2：domains/ 串联（2~3 天）

`domains/` 回答「怎么串起来」，把 framework 碎片拼成链路。**按问题驱动。**

| 优先级 | 文档                                                               | 解决什么                                                      |
| :-: | ---------------------------------------------------------------- | --------------------------------------------------------- |
| ★★★ | `login-flow.md`                                                  | 冷启动/登出/重登录/断线重连四态，串起 GameEntry→网络→状态机→数据                  |
| ★★★ | `update-flow.md`                                                 | 四通道热更（出包/资源/IL/Lua）+ 传输层 vs 消费加载层                         |
| ★★★ | `module-boundary-constraints.md`                                 | 跨模块嵌入成本与禁区，**写需求前先看**                                     |
|  ★★ | `protocol-patterns.md`                                           | 三种协议写法：`[Operation]` 反射 / `SendCmdHandleForAct` / 直发+Push |
|  ★★ | `act-taxonomy.md`                                                | 1000+ Act 按 28 个 domain 分类；写新活动先来这找同类样板                   |
|  ★★ | `plugin-taxonomy.md`                                             | 144 个 Plugin 分类                                           |
|  ★★ | `ui-entry-refresh.md` + `ui-architecture-evolution.md`           | 入口/红点刷新时机；UI 基类三代演进                                       |
|  ★  | `config-pipeline.md`                                             | 配置表 Excel→导出→加载→消费链路                                      |
|  ★  | `battle-context-flow.md` / `pvp-tournament-battle-enter-flow.md` | 进战链路（接触战斗时再读）                                             |

### 必须记住的两个模型

**更新四通道**

| 通道   | 载体                      | 能否热更 | 生效时机        |
| ---- | ----------------------- | :--: | ----------- |
| 出包更新 | `Assembly-CSharp`       |   ❌  | 重装整包        |
| 资源热更 | AssetBundle             |   ✅  | 下次进入使用点     |
| 代码热更 | `Hotfix.dll`（ILRuntime） |   ✅  | 下次启动加载 DLL  |
| 脚本热更 | `.lua.txt`              |   ✅  | 下次启动 / 脚本重载 |

- 判定入口：`KHPluginManager._pluginInfoDict[id].createMode` → `0=C#原生 / 1=IL / 2=Lua`
- **关键边界**：`VersionManager` 只负责下载安装到磁盘，**不加载** IL/Lua；加载生效在 `LoginDefaultPhase`

**domains/INDEX.md 的高频问题索引表**

问题关键词 → 文档的映射表，是**接手任务时最快的入口**。例：

- "充值面板打不开" → `entities/system/payment-system.md`
- "招募页签点不动" → `entities/system/recruit-system.md`
- "进组织卡转场黑屏" → `entities/system/guild-system.md`

---

## 4. 阶段 3：entities/ 只按需查，绝不通读

1187 篇，**只有检索价值**。分清三个质量层级：

| 子类                 | 数量         | 性质                            | 怎么用                         |
| ------------------ | ---------- | ----------------------------- | --------------------------- |
| `acts/` `plugins/` | 1043 + 144 | 机械生成（`ai-batch`），浅层文件清单       | 找同类样板抄骨架                    |
| `system/`          | ~30 篇      | **人工源码级**（`confidence: high`） | ⭐ 最值得学，是"系统该怎么分析"的范例        |
| `config/`          | 6 张表       | 配置表机械事实                       | 配合 `skills/kh-config-qa` 使用 |

### 推荐的第一篇

挑小的 `system/` 文档，比如：

- `system/badge-system.md`（徽章，最简单）
- `system/artifact-system.md`（神器）
- `system/magatama-system.md`（勾玉）

然后打开**同名浅层篇**（如 `plugins/Badge_徽章系统.md`）**对比着看** —— 五分钟就能懂「浅层清单 vs 深度分析」的差距，也明白以后自己该写到什么程度。

### system/ 文档的标准结构（顺手记住）

```
机制总览 → 数据链路 → 协议全景 → N 套并存编号 → 风险清单（N 条）
   → 排障速查（N 行）→ 范式对比
```

最后那&#x4E2A;**「范式对比」是精华**：读几篇就能看出 KiHan 各系统的设计套路（后台驱动页签 / 客户端注册表驱动 / 配置表定形 / 服务器快照驱动……）。

---

## 5. 一周速查表

| 天     | 内容                                                                                                                |
| ----- | ----------------------------------------------------------------------------------------------------------------- |
| Day 1 | `AGENTS.md` → `overview/system-architecture-map.md` → `overview/code-distribution-overview.md` → `rules/INDEX.md` |
| Day 2 | `framework/state-machine-framework.md`                                                                            |
| Day 3 | `framework/plugin-framework.md`                                                                                   |
| Day 4 | `framework/actframework.md` + `actlib-api.md`                                                                     |
| Day 5 | `framework/ui-framework.md`（分 3 次）+ `tui-component-library.md` 速览                                                 |
| Day 6 | `domains/login-flow.md` + `domains/update-flow.md`                                                                |
| Day 7 | `domains/module-boundary-constraints.md` + `protocol-patterns.md` + 挑一篇 `entities/system/` 对比读                    |

---

## 6. 四条纪律

1. **不顺手就查，不硬读** —— 用检索 CLI 比翻目录快得多
2. **看到 `ai-batch` / `ai-draft` 必须回源码复核** —— 那是未核实的批量产物
3. **改代码前查 `context/reference-index/file-to-docs.md`** —— 拿文件名反查哪些知识文档引用了它
4. **查不到就登记 `GAPS.md`，绝不臆造路径** —— 库里明文铁律

---

## 7. 常用检索命令速查

```bash
cd <AIDev 根>

# 关键词检索（含同义词扩展）
py context/tools/kb_search.py -r . --keyword 重连

# 看命中原因
py context/tools/kb_search.py -r . --keyword 掉线 --explain

# 源码文件 → 反查引用它的知识文档
py context/tools/kb_search.py -r . --file KHGameConnection.cs

# 按 tag / 域 / 类型过滤
py context/tools/kb_search.py -r . --tag sys:Recruit
py context/tools/kb_search.py -r . --domain lottery --type entity

# 程序化消费（给下游脚本用）
py context/tools/kb_search.py -r . --keyword 转盘 --json
```

> ⚠️ Windows PowerShell 传中文参数可能乱码，改用 `cmd` 或直接 `import kb_search` 调用。

### 代码事实查询（Lua 侧）

```bash
cd Others/AIDev/evals/kb-console
../../ExcelTool/Python3/python.exe kb_query.py get_symbol_detail <符号> --resolve-inherited
../../ExcelTool/Python3/python.exe kb_query.py find_usage_examples <符号>
../../ExcelTool/Python3/python.exe kb_query.py get_subscribers <事件名>
../../ExcelTool/Python3/python.exe kb_query.py get_impact <符号 或 file:line>
../../ExcelTool/Python3/python.exe kb_query.py get_design_doc <活动号>   # 改老活动前必读
```

> 🔴 **覆盖边界**：索引内 6621 个符号 **100% 是 Lua**，**C# 符号为 0**。查 C# 类/方法走 `context/framework/*` 机制文档 + `file-to-docs` 反查 + IDE grep。

---

## 8. 附：按任务方向的窄路线

| 你的任务           | 优先读                                                                                                                         |
| -------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **写新活动（Act）**  | `domains/act-taxonomy.md` → `framework/actframework.md` → 抄同类 `entities/acts/` 样板 → `workflows/entity-analysis-workflow.md` |
| **写 Plugin**   | `framework/plugin-framework.md` → `domains/plugin-taxonomy.md` → 同类 `entities/plugins/`                                     |
| **修 bug / 归因** | `skills/root-cause-system/SKILL.md` → `guides/troubleshooting/` → `domains/INDEX.md` 高频问题索引                                 |
| **UI / 搭界面**   | `framework/tui-component-library.md` → `workflows/mockup-to-tui-prefab.md` → `framework/ui-framework.md` §3 内核机制            |
| **配置表**        | `skills/kh-config-qa/BOOTSTRAP.md` → `entities/config/INDEX.md` → `domains/config-pipeline.md`                              |
| **红点问题**       | `framework/redpoint-framework.md`（F1-F8 故障模式）+ `skills/redpoint-guard`                                                      |
| **协议 / 联调**    | `framework/csharp-proto.md` + `lua-proto.md` + `domains/protocol-patterns.md` + `skills/kihan-proto-query`                  |

---

## 9. 已知的知识库坑（读的时候注意）

- `skills/INDEX.md` 与磁盘实态已漂移：`code-quality-review` / `pipeline-yaml-generator` 在 INDEX 有登记但磁盘不存在；`act1280-anim-contract` / `kihan-dev-whitebox-review` / `redpoint-guard` / `root-cause-system` 磁盘存在但 INDEX 未登记
- `root-cause-system/SKILL.md` 的 `name: root-cause-fix` 与目录名不一致（违反 README 硬约定，但功能不受影响）
- `context/INDEX.md` 声明"不再新建 `.bugs.md` 伴生文件"，但 `entities/INDEX.md` 里仍列着大量 `.bugs.md`（历史遗留，按新规应融入主文档）
