## 项目中 "Model" 的含义

在元梦之星项目中，**Model 是数据模型层**，对应 MVC/MVP 架构中的 **M 层**，是整个游戏的数据核心。
### 一句话定义

Model 负责 **数据存储、业务逻辑、协议收发、配置查询**，通过事件系统与 View（UI层）解耦通信，**绝不直接操作 UI**。
### 职责划分

|能做|不能做|
|---|---|
|存储游戏数据（道具、邮件、任务等）|操作 UI / 调用 UIManager|
|处理业务逻辑（计算、判断、状态变更）|直接刷新界面|
|与服务器 Protobuf 通信（发协议、绑推送）|—|
|读取游戏配表|—|
|通过 `DispatchEvent` 通知 View 刷新|—|

### 继承体系

```
BaseModel (基类)
  └── SystemBaseModel (一级系统Model)
        └── SystemSubModel (子Model，分 Persistent/Temporary)
```

创建语法：`_MOE.class("BagModel", _MOE.SystemBaseModel)`
### 核心生命周期

```
Ctor → Init → OnInit → RegisterEvents → PostInitialize → BindAllNotify
                              ↓
                    运行中（业务逻辑 / OnUpdate Tick）
                              ↓
                    Clear → OnClear → UnBindAllNotify
```

|方法|说明|
|---|---|
|**OnInit()**|必须重写，初始化数据（`self._DataMap = {}`）|
|**OnClear()**|必须重写，清理数据、定时器、引用|
|**OnReset()**|可选，断线重连时重置（通常直接调 `OnInit()`）|
|**BindAllNotify()**|可选，绑定服务器推送通知|

### 子 Model 体系（门面模式）

复杂系统的一级 Model 通过子 Model 拆分职责：

|类型|生命周期|示例|
|---|---|---|
|**Persistent 子Model**|持久化，切场景不销毁|`BagItemInfoModel`|
|**Temporary 子Model**|临时，切场景销毁|`BagNetworkModel`|
|**Helper**|纯工具/配置查询，不持有状态|`BagItemHelper`|

### 数据流向

```
用户操作 → View 调用 Model 方法 → Model 发协议/处理逻辑
                                          ↓
服务器响应 → Model 更新数据 → DispatchEvent → View 监听刷新 UI
```

**简单说：View 不碰网络和业务逻辑，Model 不碰 UI，两者通过事件解耦。**



## 项目 Model 完整继承层次

你看到的这些类，构成了一套清晰的三层体系：

```
                        BaseModel  (所有 Model 的根)
                       /          \
                      /            \
           SystemBaseModel      直接继承 BaseModel
          (系统一级Model)       (不需要子Model管理的)
              |
              |  GetSubModel() 创建和管理
              |
         SystemSubModel
        (Persistent/Temporary)
```

---

### 各层对比

| 层级 | 类名 | 干什么的 | 有无子Model |
|------|------|----------|------------|
| **根** | `BaseModel` | 提供生命周期、事件、网络、Tick | 无 |
| **一级** | `SystemBaseModel` | 在 BaseModel 上加子Model管理、场景切换清理 | 有 |
| **一级(简化)** | 直接继承 `BaseModel` | 简单模块，不需要子Model拆分 | 无 |
| **二级** | `SystemSubModel` | 被一级Model通过 `GetSubModel()` 懒加载创建 | 无 |

---

### 举个例子：BagModel（背包系统）

```
BagModel (SystemBaseModel)        ← 一级门面，对外提供统一接口
  ├── BagItemInfoModel (Persistent)  ← 道具数据
  ├── BagDressModel (Persistent)     ← 穿脱管理
  ├── BagViewModel (Persistent)      ← 视图状态
  ├── BagSkinModel (Persistent)      ← 皮肤
  ├── BagNetworkModel (Temporary)    ← 网络请求，切场景就销毁
  ├── BagItemHelper (Temporary)      ← 工具类，不持有数据
  └── ... 共 20 个子Model
```

外部调用时只访问 `_MOE.Models.BagModel`，内部怎么拆分的外部不关心——这就是**门面模式**。

---

### 关键区别：Persistent vs Temporary

| 类型 | 场景切换时 | 典型用途 |
|------|-----------|----------|
| **Persistent** | 实例保留，只清临时数据 | 道具信息、任务数据、皮肤等核心数据 |
| **Temporary** | 实例销毁，置 nil | 网络请求中间态、临时查询、Helper |

### 两种注册方式

| 注册方式 | 行为 | 适用场景 |
|----------|------|----------|
| **PreAdd**（懒加载） | 首次访问 `_MOE.Models.XXX` 时才创建 | 非关键路径 Model |
| **PreLoad**（立即加载） | 启动就创建实例 | 登录/核心 Model |

### 一句话总结

```
BaseModel = 所有 Model 的共同能力（生命周期+事件+网络）
SystemBaseModel = 一级门面（+子Model管理+场景清理）
SystemSubModel = 二级子Model（Persistent常驻 / Temporary临时）
```

你之前看的 `ActivityModel` 就是继承 `SystemBaseModel` 的一级门面，通过 `_subModuleMapping` 管理了 16 个子模块。这个三层体系让复杂的游戏系统能够按职责拆分成小而专注的模块。
![[Pasted image 20260709094425.png]]