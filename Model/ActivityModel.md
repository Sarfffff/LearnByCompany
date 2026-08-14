项目确实将原来 **7476行** 的 `NewActivityModel.lua` 大文件拆分成了 **门面模式 + 17个子Model** 的架构：
- **门面类**: `ActivityModel.lua` (278行)
    
- **子Model数量**: 17个核心功能模块 + 大量活动实例Model
    
- **总Model数量**: 约 **120+** 个活动相关Model
### 🔧 核心设计机制

#### 1. **子模块注册系统**

```lua
-- 批量注册事件常量到类表
ActivityModel.Events = ActivityModel_EventConstants
_RegisterEventConstants()  -- 自动挂载所有非函数属性
```

#### 2. **动态方法注册**
```lua
-- 外部事件 → 门面类 → 对应子模块
function ActivityModel:RegisterEvents()
    self:AddListener(_MOE.EventEnum.ON_PANDORA_RED_POINT_STATE_UPDATED, self, function(self, appId)
        self.m_redDot.OnPandoraRedPointStateUpdate(self, appId)  -- 转发到红点子模块
    end)
end
```

### 🎯 各子模块职责分工

通过映射表实现
```lua
-- ==================== 子模块映射表 ====================
-- 子模块映射表：field = 挂载字段名, module = 子模块引用
local _subModuleMapping = {
    { field = "m_tabData",          module = ActivityModel_TabData },
    { field = "m_redDot",           module = ActivityModel_RedDot },
    { field = "m_featureMgr",       module = ActivityModel_FeatureMgr },
    { field = "m_dataQuery",        module = ActivityModel_DataQuery },
    { field = "m_protocol",         module = ActivityModel_Protocol },
    { field = "m_viewMgr",          module = ActivityModel_ViewMgr },
    { field = "m_noticeData",       module = ActivityModel_NoticeData },
    { field = "m_activityDisplay",  module = ActivityModel_ActivityDisplay },
    { field = "m_jumpHelper",       module = ActivityModel_JumpHelper },
    { field = "m_luckBuy",          module = ActivityModel_LuckBuy },
    { field = "m_pilot",            module = ActivityModel_Pilot },
    { field = "m_takeaway",         module = ActivityModel_Takeaway },
    { field = "m_superLinear",      module = ActivityModel_SuperLinear },
    { field = "m_kongFuPanda",      module = ActivityModel_KongFuPanda },
    { field = "m_conan",            module = ActivityModel_Conan },
    { field = "m_miscActivity",     module = ActivityModel_MiscActivity },
}
```

|子模块|字段名|主要职责|
|---|---|---|
|[`ActivityModel_TabData`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_TabData%22%2C%5B%7B%22line%22%3A21%2C%22character%22%3A6%7D%2C%7B%22line%22%3A21%2C%22character%22%3A27%7D%5D%5D)|[`m_tabData`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_tabData%22%2C%5B%7B%22line%22%3A43%2C%22character%22%3A15%7D%2C%7B%22line%22%3A43%2C%22character%22%3A24%7D%5D%5D)|活动标签数据管理|
|[`ActivityModel_RedDot`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_RedDot%22%2C%5B%7B%22line%22%3A22%2C%22character%22%3A6%7D%2C%7B%22line%22%3A22%2C%22character%22%3A26%7D%5D%5D)|[`m_redDot`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_redDot%22%2C%5B%7B%22line%22%3A44%2C%22character%22%3A15%7D%2C%7B%22line%22%3A44%2C%22character%22%3A23%7D%5D%5D)|红点系统管理|
|[`ActivityModel_FeatureMgr`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_FeatureMgr%22%2C%5B%7B%22line%22%3A23%2C%22character%22%3A6%7D%2C%7B%22line%22%3A23%2C%22character%22%3A30%7D%5D%5D)|[`m_featureMgr`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_featureMgr%22%2C%5B%7B%22line%22%3A45%2C%22character%22%3A15%7D%2C%7B%22line%22%3A45%2C%22character%22%3A27%7D%5D%5D)|功能特性管理|
|[`ActivityModel_DataQuery`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_DataQuery%22%2C%5B%7B%22line%22%3A25%2C%22character%22%3A6%7D%2C%7B%22line%22%3A25%2C%22character%22%3A29%7D%5D%5D)|[`m_dataQuery`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_dataQuery%22%2C%5B%7B%22line%22%3A46%2C%22character%22%3A15%7D%2C%7B%22line%22%3A46%2C%22character%22%3A26%7D%5D%5D)|数据查询接口|
|[`ActivityModel_Protocol`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_Protocol%22%2C%5B%7B%22line%22%3A26%2C%22character%22%3A6%7D%2C%7B%22line%22%3A26%2C%22character%22%3A28%7D%5D%5D)|[`m_protocol`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_protocol%22%2C%5B%7B%22line%22%3A47%2C%22character%22%3A15%7D%2C%7B%22line%22%3A47%2C%22character%22%3A25%7D%5D%5D)|网络协议处理|
|[`ActivityModel_ViewMgr`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_ViewMgr%22%2C%5B%7B%22line%22%3A27%2C%22character%22%3A6%7D%2C%7B%22line%22%3A27%2C%22character%22%3A27%7D%5D%5D)|[`m_viewMgr`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_viewMgr%22%2C%5B%7B%22line%22%3A48%2C%22character%22%3A15%7D%2C%7B%22line%22%3A48%2C%22character%22%3A24%7D%5D%5D)|视图管理|
|[`ActivityModel_NoticeData`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_NoticeData%22%2C%5B%7B%22line%22%3A28%2C%22character%22%3A6%7D%2C%7B%22line%22%3A28%2C%22character%22%3A30%7D%5D%5D)|[`m_noticeData`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_noticeData%22%2C%5B%7B%22line%22%3A49%2C%22character%22%3A15%7D%2C%7B%22line%22%3A49%2C%22character%22%3A27%7D%5D%5D)|公告数据管理|
|[`ActivityModel_ActivityDisplay`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_ActivityDisplay%22%2C%5B%7B%22line%22%3A29%2C%22character%22%3A6%7D%2C%7B%22line%22%3A29%2C%22character%22%3A35%7D%5D%5D)|[`m_activityDisplay`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_activityDisplay%22%2C%5B%7B%22line%22%3A50%2C%22character%22%3A15%7D%2C%7B%22line%22%3A50%2C%22character%22%3A32%7D%5D%5D)|活动展示逻辑|
|[`ActivityModel_JumpHelper`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_JumpHelper%22%2C%5B%7B%22line%22%3A30%2C%22character%22%3A6%7D%2C%7B%22line%22%3A30%2C%22character%22%3A30%7D%5D%5D)|[`m_jumpHelper`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_jumpHelper%22%2C%5B%7B%22line%22%3A51%2C%22character%22%3A15%7D%2C%7B%22line%22%3A51%2C%22character%22%3A27%7D%5D%5D)|页面跳转辅助|
|[`ActivityModel_LuckBuy`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_LuckBuy%22%2C%5B%7B%22line%22%3A31%2C%22character%22%3A6%7D%2C%7B%22line%22%3A31%2C%22character%22%3A27%7D%5D%5D)|[`m_luckBuy`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_luckBuy%22%2C%5B%7B%22line%22%3A52%2C%22character%22%3A15%7D%2C%7B%22line%22%3A52%2C%22character%22%3A24%7D%5D%5D)|幸运购买功能|
|[`ActivityModel_Pilot`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_Pilot%22%2C%5B%7B%22line%22%3A32%2C%22character%22%3A6%7D%2C%7B%22line%22%3A32%2C%22character%22%3A25%7D%5D%5D)|[`m_pilot`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_pilot%22%2C%5B%7B%22line%22%3A53%2C%22character%22%3A15%7D%2C%7B%22line%22%3A53%2C%22character%22%3A22%7D%5D%5D)|导航功能|
|[`ActivityModel_Takeaway`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_Takeaway%22%2C%5B%7B%22line%22%3A33%2C%22character%22%3A6%7D%2C%7B%22line%22%3A33%2C%22character%22%3A28%7D%5D%5D)|[`m_takeaway`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_takeaway%22%2C%5B%7B%22line%22%3A54%2C%22character%22%3A15%7D%2C%7B%22line%22%3A54%2C%22character%22%3A25%7D%5D%5D)|外卖功能|
|[`ActivityModel_SuperLinear`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_SuperLinear%22%2C%5B%7B%22line%22%3A34%2C%22character%22%3A6%7D%2C%7B%22line%22%3A34%2C%22character%22%3A31%7D%5D%5D)|[`m_superLinear`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_superLinear%22%2C%5B%7B%22line%22%3A55%2C%22character%22%3A15%7D%2C%7B%22line%22%3A55%2C%22character%22%3A28%7D%5D%5D)|超级线性活动|
|[`ActivityModel_KongFuPanda`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_KongFuPanda%22%2C%5B%7B%22line%22%3A35%2C%22character%22%3A6%7D%2C%7B%22line%22%3A35%2C%22character%22%3A31%7D%5D%5D)|[`m_kongFuPanda`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_kongFuPanda%22%2C%5B%7B%22line%22%3A56%2C%22character%22%3A15%7D%2C%7B%22line%22%3A56%2C%22character%22%3A28%7D%5D%5D)|功夫熊猫活动|
|[`ActivityModel_Conan`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_Conan%22%2C%5B%7B%22line%22%3A36%2C%22character%22%3A6%7D%2C%7B%22line%22%3A36%2C%22character%22%3A25%7D%5D%5D)|[`m_conan`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_conan%22%2C%5B%7B%22line%22%3A57%2C%22character%22%3A15%7D%2C%7B%22line%22%3A57%2C%22character%22%3A22%7D%5D%5D)|柯南活动|
|[`ActivityModel_MiscActivity`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_MiscActivity%22%2C%5B%7B%22line%22%3A37%2C%22character%22%3A6%7D%2C%7B%22line%22%3A37%2C%22character%22%3A32%7D%5D%5D)|[`m_miscActivity`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22m_miscActivity%22%2C%5B%7B%22line%22%3A58%2C%22character%22%3A15%7D%2C%7B%22line%22%3A58%2C%22character%22%3A29%7D%5D%5D)|杂项活动管理|
|[`ActivityModel_EventConstants`](command:gongfeng.gongfeng-copilot.chat.open-symbol-in-file?%5B%7B%22%24mid%22%3A1%2C%22fsPath%22%3A%22d%3A%5C%5CLetsGoEditor%5C%5CEditor%5C%5CLetsGo%5C%5CContent%5C%5CFeature%5C%5CSystem%5C%5CScript%5C%5CSystem%5C%5CActivity%5C%5CPublic%5C%5CModel%5C%5CActivityModel.lua%22%2C%22_sep%22%3A1%2C%22external%22%3A%22file%3A%2F%2F%2Fd%253A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22path%22%3A%22%2Fd%3A%2FLetsGoEditor%2FEditor%2FLetsGo%2FContent%2FFeature%2FSystem%2FScript%2FSystem%2FActivity%2FPublic%2FModel%2FActivityModel.lua%22%2C%22scheme%22%3A%22file%22%7D%2C%22ActivityModel_EventConstants%22%2C%5B%7B%22line%22%3A24%2C%22character%22%3A6%7D%2C%7B%22line%22%3A24%2C%22character%22%3A34%7D%5D%5D)|Events|事件常量定义|

### 🔄 事件系统设计

#### 事件常量管理

`-- 批量注册事件常量到类表 ActivityModel.Events = ActivityModel_EventConstants _RegisterEventConstants()  -- 自动挂载所有非函数属性` 

#### 事件转发机制

`-- 外部事件 → 门面类 → 对应子模块 function ActivityModel:RegisterEvents()     self:AddListener(_MOE.EventEnum.ON_PANDORA_RED_POINT_STATE_UPDATED, self, function(self, appId)         self.m_redDot.OnPandoraRedPointStateUpdate(self, appId)  -- 转发到红点子模块     end) end` 

### 🌟 懒加载与缓存机制

#### 1. **子模块懒加载**
```lua
-- 通过元表实现按需加载
local activityMetaTable = {
    __index = function(table, key)
        local modelIns = self:GetModel(key)  -- 动态加载
        if modelIns then
            self.subModels[key] = modelIns   -- 缓存实例
            return modelIns
        end
    end
}
setmetatable(self.subModels, activityMetaTable)
```

#### 2. **AnimSkipReason 懒加载**
```lua
-- 依赖 _MOE.ServerEnum，首次访问时初始化
ActivityModel.AnimSkipReason = setmetatable({}, {
    __index = function(t, k)
        ActivityModel_EventConstants.InitAnimSkipReason()  -- 延迟初始化
        ActivityModel.AnimSkipReason = ActivityModel_EventConstants.AnimSkipReason
        return ActivityModel.AnimSkipReason[k]
    end
})
```

### 🎨 个性化展示系统
```lua
ActivityModel.ActivityCustomCodData = {
    ShowBrithday = {
        NeedShow = function()
            return _MOE.Models.BirthdayModel:IsShowBirthdayActivity()
        end
    },
    -- 其他活动显示逻辑...
}
```

### 🔄 生命周期管理

#### 初始化顺序
```lua
function ActivityModel:OnInit()
    self.subModels = {}                    -- 1. 初始化子模块容器
    setmetatable(self.subModels, meta)     -- 2. 设置懒加载元表
    _RegisterSubModuleMethods()            -- 3. 注册子模块方法
    _RegisterEventConstants()              -- 4. 注册事件常量
    for _, entry in ipairs(_subModuleMapping) do
        self[entry.field] = entry.module   -- 5. 挂载子模块引用
    end
end
```
#### 清理机制
```lua
function ActivityModel:OnClear()
    for _, entry in ipairs(_subModuleMapping) do
        if entry.module.Clear then
            entry.module.Clear()  -- 调用子模块清理方法
        end
        self[entry.field] = nil   -- 解除引用
    end
    self.subModels = {}           -- 清空子模块容器
end
```



### 各子模块职责分工详解

#### 1. **ActivityModel_TabData (39.38KB)**

- **职责**：活动页签数据管理
    
- **核心功能**：
    
    - 活动列表请求与缓存
        
    - 页签初始化与排序逻辑
        
    - 活动数据映射构建
        
    - 多语言适配支持
        
    - 失败重试机制
        

#### 2. **ActivityModel_RedDot (100.80KB)**

- **职责**：红点系统全生命周期管理
    
- **核心功能**：
    
    - 红点类型判定（数字/圆点）
        
    - 红点数据维护与更新
        
    - 飞鹰/无极公告红点处理
        
    - Pandora/PixUI红点管理
        
    - 红点点击上报与清除
        

#### 3. **ActivityModel_FeatureMgr (17.69KB)**

- **职责**：活动分组过滤与玩法隔离
    
- **核心功能**：
    
    - 活动分组判断（COC/StarP/Rich/Farm等）
        
    - 查询条件设置与清理
        
    - 副玩法活动显示控制
        
    - UGC活动TagId修正
        

#### 4. **ActivityModel_DataQuery (28.00KB)**

- **职责**：活动数据查询统一接口
    
- **核心功能**：
    
    - 活动信息获取（ID/名称/类型）
        
    - 可见性检查（时间/暂停状态）
        
    - 活动有效性验证
        
    - 隐藏活动处理逻辑
        

#### 5. **ActivityModel_ViewMgr (31.09KB)**

- **职责**：界面视图管理与导航
    
- **核心功能**：
    
    - 主界面打开与关闭控制
        
    - 子视图跳转逻辑
        
    - AB测试视图选择
        
    - 视图锁定/解锁机制
        
    - UGC活动中心参数构建
        

### 🔄 数据流与事件传递机制