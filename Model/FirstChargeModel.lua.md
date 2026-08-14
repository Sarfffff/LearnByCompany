``` lua
-- 局部函数：判断首充功能是否开启,检查玩家的等级/功能开关是否解锁了"首充"功能。比如新手玩家等级不够时，首充功能不开放。
local function IsFirstRechargeVisible()

    return _MOE.Models.GradeInfoModel:IsFunctionOpenByName("FirstRecharge")

end


---@class FirstChargeModel
--创建一个 Model 类，继承自 `SystemBaseModel`（系统基础 Model，提供生命周期管理）。

local FirstChargeModel = _MOE.class("FirstChargeModel", _MOE.SystemBaseModel)

  
-- 定义4个事件常量（其他地方通过这些字符串名来监听事件）
FirstChargeModel.FirstChargeBackgroundTag = "Background_Recharge" -- 背景标记（用于切换背景）

FirstChargeModel.FirstChargeModel_RefreshReward = "FirstChargeModel_RefreshReward" -- 充值后刷新奖励

FirstChargeModel.FirstChargeModel_SecondTabChanged = "FirstChargeModel_SecondTabChanged" -- Tab切换

-- FirstChargeModel.FirstChargeModel_ShowFirstChargeFullScreen = "FirstChargeModel_ShowFirstChargeFullScreen"

FirstChargeModel.FirstChargeModel_ReceiveSameValueRewards = "FirstChargeModel_ReceiveSameValueRewards" -- 领取一组相同value值的奖励通知
--这些是事件名常量。比如充值成功后，某处会 `DispatchEvent("FirstChargeModel_RefreshReward")`，Main 页面监听这个事件来隐藏充值按钮。
  

---@protected override

function FirstChargeModel:OnInit()--Model 被创建时调用一次。初始化5个数据容器为空。此时还没有任何数据，等服务器返回后才填充。

    --Private

    ---@field m_resIds number 首充配置id数组

    self.m_resIds = nil  -- 服务器下发的首充档位ID数组，初始为空

    ---@field m_firstChargeConfigDataMap table 首充配置数据map

    self.m_firstChargeConfigDataMap = {} --配表数据，key=id, value=配置（标题、价格等）

    ---@field m_firstChargeTaskDataMap table 首充任务map

    self.m_firstChargeTaskDataMap = {}  -- 任务数据，key=id, value=任务列表

  

    ---@field m_firstChargeStateList table 首充任务状态map

    self.m_firstChargeStateList = {} ---- 状态列表，用于Tab排序

  

    ---@field m_bIsInitData bool 是否已经初始化数据

    self.m_bIsInitData = false -- 是否已从服务器获取过数据

  

end

  

function FirstChargeModel:BindAllNotify()

  

end

  
--Model 不会自己主动轮询，而是**被动监听**4个事件。游戏运行中这些事件触发时，对应的函数会被自动调用。
function FirstChargeModel:RegisterEvents()
	--① 任务系统初始化完成后 → 请求首充数据
    self:AddListener(_MOE.EventEnum.GET_ALL_TASK_INFO, self, self.ReqFirstChargeTaskInfo)
	-- ② 任务有变更时（充值/领奖后）→ 更新红点
    self:AddListener(_MOE.EventEnum.TASK_INFO_MAP_UPDATE_NOTICE, self, self.OnUpdateReddotInfo)

    --增加首充

    -- self:AddListener(_MOE.Models.FirstChargeModel.FirstChargeModel_ShowFirstChargeFullScreen, self, self.TryOpenFirstChargeFullScreen)
	-- ③ 场景礼包变化（服务器推送首充拍脸）→ 准备弹全屏首充
    _MOE.EventManager:RegisterEvent(_MOE.EventEnum.ON_SCENEGIFT_DATA_CHANGE, self, self.OnSceneGiftDataChange)
	-- ④ 切换场景时 → 尝试弹全屏首充（如果之前收到了推送）
    _MOE.EventManager:RegisterEvent(_MOE.EventEnum.ON_REAL_SWITCH_SCENE, self, self.TryOpenFirstChargeFullScreen)

end

  

---场景礼包数据变化处理

function FirstChargeModel:OnSceneGiftDataChange(giftData, isExist)

    ---处理相关联的场景礼包

    if not isExist and giftData and giftData.Type == _MOE.ServerEnum.SceneGiftPackageType.SGPT_FirstChargePush then

        self.HaveFirstChargePush = true

        self:TryOpenFirstChargeFullScreen(giftData.Config)

    end

end

  

function FirstChargeModel:GetHaveFirstChargePush()

    return self.HaveFirstChargePush == true

end

  

-- function FirstChargeModel:ChangeFirstChargePush(value)

--     self.HaveFirstChargePush = value

-- end

  

function FirstChargeModel:TryOpenFirstChargeFullScreen(giftCfg)

    --回流屏蔽

    if _MOE.Models.PlayerReturnModel:OnShieldShowPushFace() or _MOE.Models.PlayerReturnModel:ReturnFullScreenViewOnShield() or not _MOE.Models.CloudModel:SupportPurchase(true) then

        _MOE.Logger.Log("OnSeasonChangedHandler", "PlayerReturnModel:OnShieldShowPushFace")

        return

    end

    if _MOE.SceneManager:IsInLobbyScene() then

        local lobbyVisible = _MOE.UIManager:IsWindowVisible(_MOE.WindowName.UILobbyView)

        local wxlobbyVisible = _MOE.UIManager:IsWindowVisible(_MOE.WindowName.UI_WXGame_LobbyView)

        local newWXLobbyVisible = _MOE.UIManager:IsWindowVisible(_MOE.WindowName.UI_WXGame_NewLobbyView)

        if lobbyVisible or wxlobbyVisible or newWXLobbyVisible then

            if self:GetHaveFirstChargePush() then

                _MOE.UIManager:OpenWindow(_MOE.WindowName.UI_Recharge_FirstChargeSubViewFullScreen,giftCfg)

                self.HaveFirstChargePush = false

            end

        end

    end

end

  

function FirstChargeModel:RefreshReddot()

    _MOE.Models.RedDotModel:UpdateRedDotByType(_MOE.CommonDefine.E_RDT_TYPE.FirstCharge)

    _MOE.Models.RedDotModel:UpdateRedDotByType(_MOE.CommonDefine.E_RDT_TYPE.LuckBuy)

    _MOE.Models.RedDotModel:UpdateRedDotByType(_MOE.CommonDefine.E_RDT_TYPE.Recharge_FirstCharge_Tab)

    _MOE.Models.RedDotModel:UpdateRedDotByType(_MOE.CommonDefine.E_RDT_TYPE.Recharge_LobbyEnter)

end

  

---@des 通过id判断是否在版本内

function FirstChargeModel:IsInVersionByConfig(config)

    if config == nil then

        return false

    end

    local minVersion = config.minVersion

    if minVersion then

        local minVersionNum = _MOE.Utils.CommonUtils:ClientVersionToNumber(minVersion)

        local version = _MOE.AppVersionManager:GetVersionCode()

        if version then

            return version >= minVersionNum

        end

    end

    return true

end

  

---@des 判断是否在版本内

function FirstChargeModel:IsInVersion()

    if self.m_resIds == nil then

        _MOE.Logger.Log("FirstChargeModel:IsInVersion() self.m_resIds == nil")

        return false

    end

    if self.m_firstChargeConfigDataMap == nil or next(self.m_firstChargeConfigDataMap) == nil then

        _MOE.Logger.Log("FirstChargeModel:IsInVersion() self.m_firstChargeConfigDataMap == nil")

        return false

    end

    return true

    -- for i = 1, #self.m_resIds do

    --     local id = self.m_resIds[i]

    --     local data = _MOE.Tables.RechargeTable.GetResFirstChargeConfById(id)

    --     if self:IsInVersionByConfig(data) then

    --         return true

    --     end

    -- end

    -- return false

end

  

---@des 是否显示大厅首充按钮,4个条件全部满足显示


function FirstChargeModel:IsVisibilityLobbyBtn()

    if not self:IsInVersion() then

        _MOE.Logger.Log("FirstChargeModel:IsVisibilityLobbyBtn() Version Error")

        return false

    end

    local isVisible = _MOE.Models.RechargeModel:RechargeSubPageIsVisible(_MOE.WindowName.UI_Recharge_FirstChargeSubView)

    if isVisible == false then

        _MOE.Logger.Log("FirstChargeModel:InitFirstChargeConfigMapData, RechargeSubPageIsVisible Error")

        return false

    end

    if not IsFirstRechargeVisible() then

        _MOE.Logger.Log("FirstChargeModel:InitFirstChargeConfigMapData, IsFirstRechargeVisible() Error")

        return false

    end

    self:RefreshReddot()

    return not self:IsFinishAllFirstChargeTask()

end

  

---@des 初始化数据

function FirstChargeModel:InitFirstChargeConfigMapData()

    _MOE.Logger.Log("FirstChargeModel:InitFirstChargeConfigMapData, call")

    if self.m_resIds == nil then

        return

    end

    for i = 1, #self.m_resIds do

        local id = self.m_resIds[i]

        local data = _MOE.Tables.RechargeTable.GetResFirstChargeConfById(id)

        if data then

            if self:IsInVersionByConfig(data) then

                self.m_firstChargeConfigDataMap[id] = data

            end

        end

    end

end

  

---@des 初始化数据

function FirstChargeModel:InitFirstChargeTaskMapData()

    if self.m_firstChargeConfigDataMap == nil or next(self.m_firstChargeConfigDataMap) == nil then

        _MOE.Logger.Log("FirstChargeModel:InitFirstChargeTaskMapData self.m_firstChargeConfigDataMap is nil")

        return

    end

  

    for key, value in pairs(self.m_firstChargeConfigDataMap) do

        local taskGroupId = value.taskGroupId

        local taskData = _MOE.Models.TaskSystemModel:GetQueryModel():GetTaskListByGroupIdWithoutSort(taskGroupId)

        if taskData then

            self.m_firstChargeTaskDataMap[key] = taskData

        end

    end

  

    if next(self.m_firstChargeTaskDataMap) == nil then

        return

    end

    self.m_bIsInitData = true

    self:RefreshReddot()

end

  

---@des 获取首充数据

---@return table 首充数据

function FirstChargeModel:GetFirstChargeTaskDataMap()

    return self.m_firstChargeTaskDataMap

end

  

---@des 获取首充配置数据

---@return table 首充配置数据

function FirstChargeModel:GetFirstChargeConfigDataMap()

    if self.m_firstChargeConfigDataMap == nil or next(self.m_firstChargeConfigDataMap) == nil then

        self:InitFirstChargeConfigMapData()

    end

    return self.m_firstChargeConfigDataMap

end

  

---@des 是否含有完成的首充任务

---@return bool 是否完成首充任务

function FirstChargeModel:IsCompletedOrFinishTaskById(id)

    if id == nil then

        return false

    end

    local map = self:GetFirstChargeTaskDataMap()

    local data = map[id]

    if data and next(data) then

        for i = 1, #data do

            local task = data[i]

            if task:GetTaskIsCompletedOrFinish() then

                return true

            end

        end

    end

    return false

end

  

---@des 初始化任务状态map

function FirstChargeModel:InitFirstChargeStateMap(id)

    if id == nil then

        return false

    end

    local isCompleted = false

    local isAllFinish = false

    local finishCount = 0

    local map = self:GetFirstChargeTaskDataMap()

    local data = map[id]

    if data and next(data) then

        local count = #data

        for i = 1, #data do

            local task = data[i]

            if task:GetTaskIsCompleted() then

                isCompleted = true

            elseif task:GetTaskIsFinish() then

                finishCount = finishCount + 1

            end

        end

        isAllFinish = finishCount >= count

    end

    local isUnlock = isCompleted or finishCount > 0

    local configMap = self:GetFirstChargeConfigDataMap()

    local seqId = id

    if configMap and configMap[id] then

        seqId = configMap[id].seqId

    end

    local list = {}

    list.id = id

    list.isUnlock = isUnlock and 1 or 0

    list.isCompleted = isCompleted and 1 or 0

    list.isAllFinish = isAllFinish and 1 or 0

    list.seqId = seqId

    table.insert(self.m_firstChargeStateList, list)

end

  

---@des 排序任务状态list

function FirstChargeModel:SortStateList()

    if self.m_firstChargeStateList and next(self.m_firstChargeStateList) then

        table.sort(self.m_firstChargeStateList, function(a, b)

            if a.isUnlock ~= b.isUnlock then

                return a.isUnlock > b.isUnlock

            else

                if a.isUnlock == 0 then

                    return a.seqId < b.seqId

                end

                if a.isCompleted ~= b.isCompleted then

                    return a.isCompleted > b.isCompleted

                end

                if a.isAllFinish ~= b.isAllFinish then

                    return a.isAllFinish < b.isAllFinish

                end

                return a.seqId > b.seqId

            end

        end)

    end

end

  

function FirstChargeModel:GetFirstChargeStateList()

    return self.m_firstChargeStateList

end

  

function FirstChargeModel:SetFirstChargeStateList(data)

    self.m_firstChargeStateList = data or {}

end

  

---@des 是否完成某组首充任务

---@return bool 是否完成首充任务

function FirstChargeModel:IsFinishChargeTaskById(id)

    if id == nil then

        return

    end

    local map = self:GetFirstChargeTaskDataMap()

    local data = map[id]

    if data and next(data) then

        for i = 1, #data do

            local task = data[i]

            if not task:GetTaskIsFinish() then

                return false

            end

        end

        return true

    end

    return false

end

  

---@des 是否完成所有首充任务

---@return bool 是否完成所有首充任务

function FirstChargeModel:IsFinishAllFirstChargeTask()

    local map = self:GetFirstChargeTaskDataMap()

    if map and next(map) then

        for key, _ in pairs(map) do

            if not self:IsFinishChargeTaskById(key) then

                _MOE.Logger.Log("FirstChargeModel:IsFinishAllFirstChargeTask(), IsFinishChargeTaskById() ,key = ", key)

                return false

            end

        end

        return true

    end

    _MOE.Logger.Log("FirstChargeModel:IsFinishAllFirstChargeTask(), map Error")

    return false

end

  

function FirstChargeModel:GetRuleId()

    local data = self:GetFirstChargeConfigDataMap()

    local ruleId = nil

    if data then

        for key, value in pairs(data) do

            ruleId = value.ruleId

        end

    end

    return ruleId

end

  

---@des 请求首充信息

function FirstChargeModel:ReqFirstChargeTaskInfo()

    if self.m_bIsInitData then

        _MOE.Logger.Log("FirstChargeModel:FirstChargeTaskInfo self.m_bIsInitData is true!")

        self:InitFirstChargeConfigMapData()

        self:InitFirstChargeTaskMapData()

        return

    end

    local function OnSuccess(msg)

        if msg then

            self.m_resIds = msg.resIds

            self:InitFirstChargeConfigMapData()

            self:InitFirstChargeTaskMapData()

            _MOE.EventManager:DispatchEvent(_MOE.EventEnum.GET_FIRST_CHARGE_INFO)

        end

    end

    local function Onfail(msg)

        _MOE.Logger.Log("FirstChargeModel:FirstChargeTaskInfo Fail")

    end

    _MOE.NetworkManager:SendMsg(_MOE.MsgName2Id.FirstChargeTaskInfo_C2S_Msg, {}, OnSuccess, Onfail)

end

  

---@des 充值完更新红点

function FirstChargeModel:OnUpdateReddotInfo(changeTask, isChangeStatus,taskMap)

  

    local taskGroupIdList = {}

    self.m_firstChargeConfigDataMap = self:GetFirstChargeConfigDataMap()

    if self.m_firstChargeConfigDataMap then

        for key, value in pairs(self.m_firstChargeConfigDataMap) do

            table.insert(taskGroupIdList, value.taskGroupId)

        end

    end

  

    if _MOE.Models.TaskSystemModel:GetQueryModel():CheckTaskIsChangeByGroupIdList(taskGroupIdList,taskMap) then

        self:RefreshReddot()

    end

  

end

  

function FirstChargeModel:UpdateFirstChargeSubTabRedDot(id)

    if id == nil then

        return false

    end

    local map = self:GetFirstChargeTaskDataMap()

    local data = map[id]

    if data and next(data) then

        for i = 1, #data do

            local task = data[i]

            if task:GetTaskIsCompleted() then

                return true

            end

        end

    end

    return false

end

  

function FirstChargeModel:OnReset()

    self.m_firstChargeConfigDataMap = {}

    self.m_firstChargeTaskDataMap = {}

    self.m_bIsInitData = false

end

  
  

function FirstChargeModel:OnClear()

    self.m_firstChargeConfigDataMap = {}

    self.m_firstChargeTaskDataMap = {}

    self.m_bIsInitData = false

end

  

return FirstChargeModel
```
# 数据得到
这个是model是读完配置表的ID从服务器拿到的数据，想要得到这个数据比如subView得到这个数据通过InitTaskData函数得到的
```
function UI_Recharge_FirstChargeSubView:InitTaskData()
    -- ★ 核心数据来源：直接从 FirstChargeModel 读取
    self.FirstChargeDataMap = _MOE.Models.FirstChargeModel:GetFirstChargeTaskDataMap()
    self.FirstChargeConfigData = _MOE.Models.FirstChargeModel:GetFirstChargeConfigDataMap()
end

```
![[Pasted image 20260709144611.png]]
```
玩家进游戏
  │
  ├→ FirstChargeModel:OnInit()           ← 创建空容器
  ├→ FirstChargeModel:RegisterEvents()   ← 注册4个事件监听
  │
  ↓ 任务系统初始化完成
  │
  ├→ GET_ALL_TASK_INFO 事件触发
  │  └→ ReqFirstChargeTaskInfo()
  │     └→ 服务器请求 FirstChargeTaskInfo_C2S_Msg
  │        └→ 服务器返回 resIds = {2, 3}
  │           ├→ InitFirstChargeConfigMapData()  ← 用 resIds 读配表
  │           │  └→ configMap[2] = {title="橙小兔", price=50, ...}
  │           │  └→ configMap[3] = {title="再送师徒双人", price=100, ...}
  │           ├→ InitFirstChargeTaskMapData()    ← 用 taskGroupId 读任务
  │           │  └→ taskMap[2] = {task1, task2, ...}
  │           │  └→ taskMap[3] = {task3, task4, ...}
  │           └→ DispatchEvent(GET_FIRST_CHARGE_INFO)  ← 通知UI数据就绪
  │
  ↓ 玩家打开首充页面
  
  │
  ├→ SubView:InitUI()
  │  └→ ReqFirstChargeTaskInfo()  ← 防止未初始化，再请求一次
  │     └→ 如果已初始化 → 直接用缓存
  │
  ├→ SubView:InitTaskData()
  │  └→ FirstChargeModel:GetFirstChargeConfigDataMap()  ← 读配置
  │  └→ FirstChargeModel:GetFirstChargeTaskDataMap()    ← 读任务
  │
  ↓ 玩家充值
  │
  ├→ PayModel:OnProcBuyRMB({count=1})
  │  └→ 服务器处理支付
  │     └→ 任务变更推送
  │        ├→ TASK_INFO_MAP_UPDATE_NOTICE 事件
  │        │  └→ FirstChargeModel:OnUpdateReddotInfo() → 刷新红点
  │        ├→ FirstChargeModel_RefreshReward 事件
  │        │  └→ Main:RefreshRechargeBtnVisibility(1) → 隐藏充值按钮
  │        └→ FirstChargeModel_ReceiveSameValueRewards 事件
  │           └→ Main:OnReceiveSameValueRewards() → 批量领奖
  │              └→ TaskSystemModel:ReqGetTaskRewards()
  │                 └→ GET_TASK_REWARD 事件
  │                    └→ SubView:OnReqNewData() → 刷新Tab列表
  │
  ↓ 玩家领完所有奖励
  │
  └→ IsFinishAllFirstChargeTask() = true
     └→ IsVisibilityLobbyBtn() = false → 大厅图标消失

```