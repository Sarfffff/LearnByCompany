---
title: KiHan 框架系列阅读索引
tags: [KiHan, 架构, MOC, 索引]
created: 2026-09-18
---

# KiHan 框架系列 · 阅读索引

> 本目录是基于 `Others/AIDev/context/framework/` 主线 8 篇 + 源码核验整理的系列笔记。
> 统一模板：定位 → 类比 → 概念表 → 链路 → 避坑 → 排查速查 → 口诀。

## 文件位置


```
Obsidian Vault/
└── 火影海外/
    └── Framework主线/
        ├── KiHan 框架阅读索引.md        ← 本文件（入口）
        ├── KiHan状态机架构详解.md
        ├── KiHan Manager台账速查.md
        ├── KiHan Plugin框架详解.md
        ├── KiHan ActFramework详解.md
        ├── KiHan UI框架详解.md
        ├── KiHan 网络框架详解.md
        ├── KiHan 资源加载框架详解.md
        └── KiHan热更双引擎详解.md
```

> 💡 Obsidian 的 `[[双链]]` 按**文件名**解析，不按路径——本系列移动目录后链接依然有效，无需逐个修正。

## 阅读顺序（按依赖关系）

| # | 笔记 | 回答的问题 | 前置 |
|:--:|---|---|---|
| 1 | [[KiHan状态机架构详解]] | 游戏怎么在玩法间切换？Boot→登录完整链路？ | 无（**主干，最先读**） |
| 2 | [[KiHan Manager台账速查]] | 78 个 Manager 各管什么？谁初始化谁？ | 1 |
| 3 | [[KiHan Plugin框架详解]] | C# 业务模块怎么写？ | 1、2 |
| 4 | [[KiHan ActFramework详解]] | Lua 活动怎么写？ | 3（对照学） |
| 5 | [[KiHan UI框架详解]] | 界面怎么开、层级怎么排？ | 3 |
| 6 | [[KiHan 网络框架详解]] | 五层栈、9 种连接、重连真相 | 1 |
| 7 | [[KiHan 资源加载框架详解]] | 六层加载、软 LRU、设备分档 | 无 |
| 8 | [[KiHan热更双引擎详解]] | 改动能不能热更？四通道怎么走？ | 1、7 |

## 一图总览

```
KHGame → KHGameFlow（状态机，笔记1）
            ├─ BuildGame → KHPluginManager（笔记3：C# 业务）
            ├─ LoginDefaultPhase → ILRuntime + xLua（笔记8：热更）
            ├─ VersionManager（笔记8：四通道下载）
            ├─ KHResManager（笔记7：资源加载）
            ├─ KHUIManager（笔记5：UI 体系）
            └─ NetworkManager（笔记6：网络）
Lua 活动 → ActFramework（笔记4）
全局管理器 → 78 个 Manager（笔记2）
```

## 使用约定

- 每篇 frontmatter 带 `confidence` 与 `source`（AIDev 原文档 + 源码路径）
- **细节以 AIDev 原文档为权威**，本系列是"理解骨架 + 排查入口"的精简版
- 原文档 `confidence: high`（带 file:line 证据）的结论可直接用；`ai-batch` 的需回源码复核
- 查不到的细节：`py context/tools/kb_search.py -r . --keyword <关键词>`

## 相关笔记

- [[KiHan 新人知识库阅读路线]]（vault 根目录：AIDev 全库的分阶段阅读计划，与本篇互补——那是"读库路线"，本篇是"框架骨架"）
