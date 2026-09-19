---
title: KiHan Manager 台账速查（78 个全局管理器）
tags: [KiHan, 架构, Manager, 单例]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/manager/INDEX.md（源码：Assets/Scripts/Manager/，实测 78 个 *Manager.cs）
---

# KiHan Manager 台账速查

> `Assets/Scripts/Manager/` 下 **78 个 `*Manager.cs`** 的反查台账。查"某系统归哪个 Manager 管"从这里开始。

---

## 0. 单例形态（先认清，源码逐个核验过）

| 形态 | 代表 | 备注 |
|---|---|---|
| 普通类 + 手写静态单例 | `KHDataManager`(getInstance)、`KHMovieManager`、`KHEffectManager`、`KHAudioRecordManager`、`GVoiceManager`、`ExpandPackManager` | 事件靠内持/全局 dispatcher |
| `KHEventDispatcher` + 静态单例 | `KHResManager`、`KHBattleManager`、`KHAudioManager`、`KHCityPlayerManager`、`VersionManager` | **自身即事件源**，可 dispatchEvent |
| `Singleton<T>`（MonoBehaviour） | `KHMultiCameraManager` | 靠 LateUpdate 轮询 |
| `SimpleSingleton<T>`（纯 C#） | `HDiffManager`、`PreDownloadManager` | |
| partial class + 手写单例 | `KHGame`（KHGameFlow 为普通类） | 引擎启动入口 |

> ⚠ 本目录登记的 Manager **全部 AOT**（无 IL 热更 DLL 承载）。

---

## 1. 核心 Manager 速查（有专篇的）

| Manager | 大小 | 职责 | 专篇 |
|---|---|---|---|
| `NetworkManager` | 19.8KB | 网络层唯一入口（五层栈+双连接+重连） | network-framework.md |
| `KHUIManager` | 95KB | UI 窗口/层级/生命周期 | ui-framework.md |
| `KHPluginManager` | 65.8KB | 插件（C#/IL/Lua）创建与生命周期 | plugin-framework.md |
| `KHDataManager` | **419KB** | 全局数据中心/配置加载/数据转换 | manager/KHDataManager.md |
| `KHBattleManager` | 84.6KB | 战斗生命周期/资源调度/模式切换 | manager/KHBattleManager.md |
| `KHGame`/`KHGameFlow` | — | 游戏入口/主循环/Context 切换 | manager/KHGame.md |
| `KHResManager` | 9.4KB | 资源加载（三 Loader/调度/缓存） | manager/KHResManager.md |
| `KHMovieManager` | 77KB | 影视/过场 CG | manager/KHMovieManager.md |
| `KHEffectManager` | 60KB | 特效创建/生命周期/性能降级 | manager/KHEffectManager.md |
| `KHAudioManager` | 65KB | 声音（FMOD Bus/3 声道/BGM 防错序列号） | manager/KHAudioManager.md |
| `GVoiceManager` | 52KB | 实时语音（GCloud Voice） | manager/GVoiceManager.md |
| `KHCityPlayerManager` | 50KB | 主城人物显隐/换装 | manager/KHCityPlayerManager.md |
| `KHMultiCameraManager` | 24KB | 多摄像机排序/屏幕缩放/HDR | manager/KHMultiCameraManager.md |
| 更新四件套 | — | VersionManager/ExpandPack/HDiff/PreDownload | manager/update-flow-managers.md |
| `KHDeviceAdapterManager` | 13KB | 异形屏安全区适配 | manager/KHDeviceAdapterManager.md |
| `KHAudioRecordManager` | 15.5KB | 录像音频轨（按帧序列化 FMOD 事件） | manager/KHAudioRecordManager.md |

---

## 2. 优先级分级

### P2 中优先级（专项子系统）
`KHOpRecordStatusManager`(24.7K) / `UDPProbingManager`(24K,补网络) / `GSDKManager`(23.4K) / `GRobotManager`(20.7K) / `PVPRecordPBLManager`(18.8K) / `VPlotManager`(17.8K,剧情) / `KHVideoManager`(16.6K,录像) / `KHConfigReleaseManager`(14K,灰度) / `ErrorManager`(12.7K) / `KHSystemStatisticsManager`(11K) / `HttpDnsManager`(10K)

### P3 低优先级（小工具/低频）
`KHKeyManager` / `KHShadowManager` / `KHPropManager` / `KHHead*Manager` 系列 / `KHIllustrationManager` / `KHFluxQTEManager` / `KHTongLingManager` / `DolphinSpeedManager` 等

---

## 3. 必知重点与坑

1. **⚠ 旧稿臆造名不存在**：`KHNinjaManager` / `KHBagManager` / `KHQualityManager` / `KHFPSAdapter` 在真实目录**并不存在**（已核验）——搜不到不是你搜错了
2. **初始化时机各异**：配置加载在 Boot（KHDataManager）/ 战斗级（KHBattleManager）/ MonoBehaviour 生命周期（KHMultiCameraManager）/ 引擎入口（KHGame）/ 懒创建（其余）——详见各专篇「初始化/销毁时机」
3. **台账引用规则**：有专篇的 Manager 只登记指针不重写正文；跨模块依赖图/故障模式归 `domains/` 层

---

## 4. 记忆口诀

> **78 个 Manager 五种单例；四百公斤 KHDataManager 是数据总仓；**
> **UI 插件网络战斗四巨头各有专篇；臆造 Manager 名（KHNinjaManager 等）不要信。**

## 相关笔记

- [[KiHan状态机架构详解]]（Manager 被哪个 Phase 拉起）
- [[KiHan Plugin框架详解]]（KHPluginManager）
