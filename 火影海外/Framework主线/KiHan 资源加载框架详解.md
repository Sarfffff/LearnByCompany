---
title: KiHan 资源加载框架详解（KHResManager / IResLoader / 缓存）
tags: [KiHan, 架构, 资源, AssetBundle, 缓存]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/res-load-framework.md（源码：Assets/Scripts/Manager/ResManager/）
---

# KiHan 资源加载框架详解

> 全项目资源加载的**唯一底座**。加载失败 / 黑图 / 卡顿 / OOM / 内存泄露类问题的机制根源都在这里。

---

## 0. 一句话总览：图书馆类比

| 层 | 类比 | 职责 |
|---|---|---|
| 门面层 `KHResManager` | **服务台** | 静态单例，全局唯一入口，按环境选 Loader |
| 策略层 `IResLoader` | **三种借阅方式** | Editor 直读 / Resources 内置 / AB 加载（线上主路径） |
| 调度层 `KHLoadTaskManager` | **借阅排队系统** | Asset/Bundle 双队列 + 并发上限 + 依赖编排 |
| 缓存层 CachePool | **还书暂存架** | 引用计数 + backup 队列 = **软 LRU** 卸载 |
| IO 线程 `FileLoader` | **后台仓库管理员** | worker 线程异步读磁盘/APK |

---

## 1. 六层分层全景

```
业务层     LoadRes / LoadBundle 调用方（UI / 战斗 / 数据 / 特效）
门面层     KHResManager（静态单例，按环境三选一装 Loader）
策略层     IResLoader 三实现：KHEditorResLoader / KHResouceResLoader / KHBundleResLoader
调度层     KHLoadTaskManager（双任务队列 + 并发上限 + 依赖 Bundle 编排）
缓存层     KHAssetCachePool / KHBundleCachePool（引用计数 + backup 软 LRU）
IO 线程    FileLoader + BundleLoadTask（异步磁盘/APK 读取）
底层       Resources.Load / AssetBundle.LoadFromFile/FromMemory

批量层(旁路) KHBlockResLoader / KHMutiLoader / UILoader（批量带进度/优先级/懒加载）
下载支(独立) WWWLoader / MutiWWWLoader（HTTP 远程下载：公告图/热更包）
```

---

## 2. 三种 Loader 对比

| 维度 | KHEditorResLoader | KHResouceResLoader | KHBundleResLoader |
|---|---|---|---|
| 场合 | 编辑器 | Resources 内置包 | **线上正式包** |
| 底层 API | Resources.Load 直读 | Resources.Load | AssetBundle.LoadFromFile + LoadAsset |
| 缓存 | 无 | Asset 缓存 | Asset + Bundle **双缓存** |
| 异步 | 无（全同步） | 有 | 有 |

**选择逻辑**（KHResManager 构造时三选一）：`EDITOR → Editor；UseAssetBundle → Bundle（线上主路径）；否则 → Resource`

---

## 3. 核心机制

### 加载主流程

```
KHResManager 收请求 → 转给当前 IResLoader
  → 查缓存：命中 → 同步返回
  → 未命中 → 生成 Task 交 KHLoadTaskManager 排队并发加载
  → 完成写入缓存池 → 回调业务
```

### 设备分档 ★

- `AdjustParamsByDeviceModel()` 按 `SystemInfo.systemMemorySize` 分档
- **低内存机 backup 容量置 0 = 引用归零立即卸载**（不启用备份缓存）

### 并发档位

`SetLoadingPriority(ThreadPriority)`：High=1000/100，Normal=8/4，Low=1/1（Asset/Bundle 并发上限）

---

## 4. 必知重点与坑

1. **⚠ 编辑器测不出线上问题**：Editor Loader 无缓存无任务队列无卸载，缓存/OOM/泄露只能真机验
2. **⚠ `ForceSync` 开关**：`LoadRes` 里有强制同步分支，注释"只在测试环境生效"——加载莫名全同步先查它
3. **⚠ EmbededInside 资源泄露**：`GetObject` 未命中时同步补加载，源码 todo 自认泄露
4. **Lua 资源特殊路径**：`KHResUtil.IsLuaRes` → 走 `LuaScriptResource.LoadAsset` 直接同步返回
5. **UILoader**：UI 专用门面，UI 层应走它而非直调 KHResManager

---

## 5. 排查速查

| 现象 | 先查 |
|---|---|
| 黑图 / 资源丢失 | 缓存池是否被 LRU 卸载；低内存机 backup=0 立即卸载 |
| 加载卡顿 | 并发档位；`KHLoadTaskManager` 队列积压 |
| OOM | 设备分档；BundleCache 备份容量；`ClearBackupCache` |
| 编辑器正常真机黑 | Editor Loader 无缓存语义，回源码查 Bundle 路径 |
| 图集丢失 | `bundle.xml` 清单；AB 依赖 Bundle 编排 |

---

## 6. 记忆口诀

> **一个门面三 Loader，双队列排队进缓存；**
> **引用计数软 LRU，低配机器立即卸；**
> **编辑器全是假象，内存问题真机验。**

## 相关笔记

- [[KiHan热更双引擎详解]]（AB 与热更四通道）
- [[KiHan状态机架构详解]]（BootSwitchPhase 清缓存时机）
