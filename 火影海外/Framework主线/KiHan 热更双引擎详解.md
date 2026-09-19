---
title: KiHan 热更双引擎详解（xLua 单 VM + ILRuntime 多域 + 四通道更新）
tags: [KiHan, 架构, 热更, xLua, ILRuntime, 更新流程]
created: 2026-09-18
confidence: high
source: lua-runtime-framework.md + il-runtime-framework.md + domains/update-flow.md
---

# KiHan 热更双引擎详解

> 两套热更通道：**Lua 脚本**（xLua）+ **C# 代码**（ILRuntime），加上资源 bundle，构成完整更新体系。
> "我这个改动能不能热更"看这一篇。

---

## 0. 三个破除谣言的澄清 ★（源码核验）

1. **只有一个引擎：xLua。没有"V1=SLua / V2=xLua 双引擎"**
   - 全工程 `using SLua` 命中 **0 次**；SLua 只是腾讯 Pandora 运营 SDK 残留
2. **Lua 框架核心不在 `Assets/Scripts/`，在 `Packages/khengine/Runtime/Lua/`**
   - `LuaVirtualMachine` / `LuaClass` / `RuntimeLuaProxy` / `LuaCodec` 全在 khengine 包内
3. **V1 与 V2 共享同一个 xLua VM**
   - 全工程 `new LuaEnv()` 只出现一处（`LuaVirtualMachine.cs:39`）；`RuntimeLuaProxy` 是 V1↔V2 桥梁

---

## 1. 三语三层运行时

| 层 | 载体 | 能否热更 | 判定 |
|---|---|:--:|---|
| AOT C#（主工程） | `Assembly-CSharp` | ❌ 必须出包 | `createMode == 0` |
| ILRuntime C# | `Hotfix.dll`（.bytes 下发） | ✅ | `createMode == 1` |
| Lua 脚本 | `.lua.txt` | ✅ | `createMode == 2` |

判定入口：`KHPluginManager._pluginInfoDict[id].createMode`

---

## 2. Lua 运行时：五层架构

```
L5 业务脚本  LuaScript/（500+ .lua.txt，按模块分目录）
L4 绑定层    Assets/Scripts/LuaWrap/（AutoGen 76 + 手动 KHWrap 5 + GenConfig）
L3 运行时门面 Assets/Scripts/LuaSupportV2/Core/（RuntimeLua 单例 / LuaCmdCenter / LuaScriptResource）
L2 C#↔Lua 桥接  LuaBehaviour（V1/V2）+ LuaClass（khengine，一个 lua 一个类+实例）
L1 虚拟机内核 Packages/khengine/Runtime/Lua/（LuaVirtualMachine 唯一 new LuaEnv / LuaCodec 解密）
```

三大机制：**初始化**（RuntimeLua.Instance 懒创建）→ **加载解密**（CustomLoader + LuaCodec）→ **卸载防泄漏**

---

## 3. ILRuntime：三段式 + 多域

| 层 | 落点 |
|---|---|
| 引擎本体 | `Packages/com.ourpalm.ilruntime` + `Assets/ThirdParty/ILRuntime/ILRuntime/` |
| KH 接入层 | `Assets/ThirdParty/ILRuntime/`（AppDomain 生命周期 + KHILRuntime 适配器 + ILKexiu 热修） |
| 热更业务工程 | `Others/ILRuntimeTools/ILAPPDomain/`（11 个域，VS2022 打开 ILAppDomain.sln） |

**11 个域**：ILAppDomain（主）/ **ILCommonDomain**（公共，唯一由 C# 侧显式注册，其余域由它的 IL main 自行装配）/ ILKexiuDomain（热修）/ ILMonoDomain / ILTongLingDomain / ILTestDomain / PKNS / PVEGamePlay / SwapPlayerPvp / WanderingExploration / Lib

生命周期：`AppDomainManager`（多域单例）→ `AppDomainMaker`（单域构建：Dispose 旧域 → `new AppDomain` → `LoadAssembly` 从 MemoryStream 加载 dll+pdb）

---

## 4. 更新体系：两层心智模型 ★

> **`VersionManager` 只负责把文件下载安装到本地磁盘，它不加载 IL/Lua！**
> 加载生效发生在更晚的 `LoginDefaultPhase`。

```
【传输安装层】VersionManager（AppCheckAndUpdate 出包 / ResCheckAndUpdate 周版本资源
              / PreResCheckAndUpdate 战斗首更）+ HDiffManager（差分）+ ExpandPackManager
              + PreDownloadManager，底座 GCloud Dolphin
        ↓ 文件落盘
【消费加载层】Boot Context → LoginDefaultPhase（早于服务器登录）
              ① bundle.xml ② 初始化 ILRuntime(Hotfix.dll) ③ Shader 预热
              ④ 初始化 Lua ⑤ 配置表 ⑥ 预加载 ⑦ MSDK 登录
```

### 四通道更新表

| 通道 | 载体 | 能否热更 | 生效时机 |
|---|---|:--:|---|
| 出包更新 | `Assembly-CSharp` | ❌ | 重装整包 |
| 资源热更 | AssetBundle（bundle.xml 清单） | ✅ | 下次进入使用点 |
| 代码热更 | `Hotfix.dll` | ✅ | **下次启动**加载 DLL |
| 脚本热更 | `.lua.txt` | ✅ | 下次启动 / 脚本重载 |

> **关键洞察**：`Hotfix.dll` 和 `.lua.txt` 物理上是**随资源热更 bundle 一起下发的特殊文件**——没有独立的 IL/Lua 下载器。

---

## 5. 必知重点与坑

1. **"热更不生效"二分法**：先分传输（下载了吗）还是消费（加载了吗）——`VersionManager` 日志 vs `LoginDefaultPhase` 时序
2. **Lua 热更生效时机是"下次启动"**，改完 Lua 不会热生效（除非走 `reload_lua`，见 `skills/kihan-mcp-server`）
3. **IL 热修走 `ILKexiuDomain`**：桥接字段名查表 / 新字段外挂 / 新方法内联自包含，SOP 见 `workflows/il-hotfix-authoring-workflow.md`
4. **编辑器 PDB / 真机 bytes**：编辑器走 `EditorInitAppDomain`（加载 PDB 可调试），运行时走 `SyncInitAppDomain`

---

## 6. 排查速查

| 现象 | 先查 |
|---|---|
| 改动没生效 | 四通道判定：`createMode` 0/1/2；是 AOT 改动就必须出包 |
| 热更包下载了没生效 | 传输层 vs 消费层二分：`LoginDefaultPhase` 是否跑到对应步骤 |
| Lua 报找不到类 | Wrap 绑定层是否生成；`GenConfig` 是否声明导出 |
| IL 域初始化失败 | `AppDomainConfig.AppDomainDic`；dll/pdb bytes 是否落盘 |
| Lua 泄漏 | V1/V2 共享 VM，卸载走 `LuaCodec`/LuaScript 释放链 |

---

## 7. 记忆口诀

> **AOT 出包，IL 下 DLL，Lua 下脚本，资源下 Bundle；**
> **下载归 VersionManager，生效归 LoginDefaultPhase；**
> **一个 xLua 一个 VM，ILRuntime 十一个域。**

## 相关笔记

- [[KiHan状态机架构详解]]（LoginDefaultPhase 所在的 Boot 链路）
- [[KiHan 网络框架详解]]（协议侧）
