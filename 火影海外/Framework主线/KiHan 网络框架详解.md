---
title: KiHan 网络框架详解（NetworkManager 五层栈 + 双连接 + 重连）
tags: [KiHan, 架构, 网络, Network, 重连, FSP, KCP]
created: 2026-09-18
confidence: high
source: Others/AIDev/context/framework/network-framework.md（源码：Assets/Scripts/Manager/Network/）
---

# KiHan 网络框架详解

> 自研网络框架，底层 GCloud SDK（TCP）+ 自研 FSP/KCP（UDP）。对外**唯一入口 `NetworkManager`**。
> 网络断连 / 收不到包 / 重连 / PVP 卡顿问题的第一落点。

---

## 0. 一句话总览：邮局类比

| 层 | 类比 | 职责 |
|---|---|---|
| L5 `NetworkManager` | **营业窗口** | 业务唯一 API：`Send / Register / Callback` |
| L4 `KiHanProxy` | **分拣中心** | 多连接管理、多线程 PB 解析、消息队列分发 |
| L3 `Connection` | **运输车队** | ApolloConnection(GCloud TCP) / KiHanUDPConnection2(FSP+KCP) |
| L2 `MessageRouter` | **地址分拣员** | CmdId 路由、Serial 匹配、超时检测 |
| L1 `Thread & Queue` | **夜间装卸工** | KHThreadReadBody 后台反序列化 / NetworkMessageQueue |

---

## 1. 9 种连接类型（`CONNECTION_TYPE`）

| 值 | 名称 | 用途 | 传输 |
|:--:|---|---|---|
| 0 | DIR | 目录服务器 | TCP(Apollo) |
| 1 | GAME | 主游戏服(Zone) | TCP(Apollo) |
| 2 | UDP | UDP 战斗 | UDP(FSP/KCP) |
| 3 | TEAMPVE | 组队 PVE | TCP(Apollo) |
| 4 | GUILD_SCENE | 公会场景 | TCP(Apollo) |
| 5 | PVP | PVP 竞技 | UDP(FSP/KCP) |
| 6 | OB | 观战 | TCP(Apollo) |
| 7 | AUTOCHESS | 自走棋 | TCP(Apollo) |
| 8 | STATUS_SCENE | 状态场景（忍界行旅） | TCP(Apollo) |

---

## 2. 核心链路

### 发送链

```
业务 NetworkManager.Send(cmdId, body, callback)
  → KiHanProxy.Send → MessageRouter.Send → ApolloConnection.Send
```

### 双连接 + 重连上层模型

```
KHZoneConnection（Zone 主连接，心跳/登录/断线重连调度）
  └─ 内嵌 Reconnector（自研三次重连）
其它连接：自走棋 / OB（启用 Reconnector）
         忍界行旅 / 公会场景（EnabledReconnect=false，依赖 Zone 重连，自定义流程）
```

---

## 3. 重连真相 ★（最重要的机制澄清）

**GCloud `Connector` 自带的自动重连被有意关闭，重连全靠自研**：

- `ApolloConnection.cs:807-816` 组装 `ConnectorInitInfo` 时**从未设置 `AutoReconnect`**（默认 false）
- `OnStateChanged` 的 `Reconnecting` / `Reconnected` 分支是**空实现**（因为根本不会触发，属合理设计）
- 实际断线路径：`ConnectorState.Error → OnError → OnDisconnected → KHZoneConnection.HandleDisconnect → 自研 Reconnector 三次重连`

**已知故障 F1**：`Reconnector` 的 `_retrytimes` / `m_ReconnectStartTime` / `m_LastReportTime` 三个字段是 **static 类级共享**，而 Zone / 自走棋 / OB 三类连接各持实例且都启用重连 → **并发争用 static 字段**。

---

## 4. 关键文件

| 文件 | 大小 | 职责 |
|---|---|---|
| `NetworkManager.cs` | 19.8KB | 对外唯一 API（partial + SimpleSingleton） |
| `KiHanProxy.cs` | 39.5KB | 多连接管理 + 多线程 PB 解析 |
| `ApolloConnection.cs` | 40.8KB | GCloud TCP 封装：DNS/鉴权/收发 |
| `KiHanUDPConnection2.cs` | 15.2KB | UDP（PVP 实时同步），底层 FSPClient + KCP |
| `MessageRouter.cs` | 18.7KB | 路由 / Serial 匹配 / 超时 |
| `ClientHead.cs` | 2.0KB | 24 字节固定协议包头 |
| `KHThreadReadBody.cs` | 14.0KB | 后台线程 ProtoBuf 反序列化 |
| `NetworkManagerRegisters.cs` | 165KB | CmdId → handler 注册总表 |
| `KHGameConnection.cs` / `KHZoneConnection.cs` | 17.5 / 27.4KB | 连接封装 + Reconnector / Zone 心跳重连 |
| `FSPClient.cs` | 62.6KB | 帧同步客户端（3 线程 + UDP/TCP 双通道 + GSDK 加速） |

---

## 5. 必知重点与坑

1. **`NetworkManagerRegisters.cs`（165KB）是协议 handler 总表**——查"某 cmdId 谁在处理"先搜它
2. **弱网模拟**：`NetworkManager.SetWeakNetworkSimulation(enable, delayMs, lossRate)` 调试用
3. **DNS 三层解析**：`KHDnsResolverProvider` 按 host 路由 GCloud/KH/Fallback 三层 resolver（主流程已从旧 `HttpDnsManager` 迁出）
4. **多线程 PB 解析**：原始字节进后台队列反序列化，避免主线程卡顿——抓包/断点时注意不在主线程
5. **Lua 侧收发**：见 `lua-proto.md`；协议模式三种见 `domains/protocol-patterns.md`

---

## 6. 排查速查

| 现象 | 先查 |
|---|---|
| 断线不重连 | `Reconnector` 状态；该连接 `EnabledReconnect` 是否 false |
| 收不到回包 | `NetworkManagerRegisters.cs` 是否注册该 cmdId；Serial 匹配 |
| PVP 卡顿 | FSPClient 三线程；UDP 通道；GSDK 加速开关 |
| 登录连接失败 | `KHZoneConnection` 心跳 + `KHDnsResolverProvider` DNS 解析链 |
| 重连计数异常 | F1：static 字段被多连接并发争用 |
| 回包乱序/超时 | `MessageRouter` 超时检测；`domains/protocol-patterns.md` §七 |

---

## 7. 记忆口诀

> **五层栈：窗口收件、中心分拣、车队运输、地址路由、夜间装卸；**
> **九种连接 TCP/UDP 分流；重连全自研，GCloud 只报"断了"。**

## 相关笔记

- [[KiHan状态机架构详解]]（BootSwitchPhase 检查 Zone 连接）
- [[KiHan热更双引擎详解]]（协议与热更的关系）
