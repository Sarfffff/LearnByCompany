### 1.新手系统的功能是除了配置之外独立于活动的？
	ActivitySystem 提供了活动时间、活动 ID、部分数据和通用拍脸打开能力；但新手奖励如何组合页签、显示入口、判断奖励状态、展示主界面，是 NoviceReward 自己管理的。

新手奖励在业务归属、入口、主界面和主要状态判断上，是一个独立的 NoviceReward 系统；但部分配置、活动有效期、七日签到数据及拍脸打开方式复用了 ActivitySystem。就是说，不要因为配置里出现了：activityId，ActivityMainConfig，activityType，slapFace，ActivityModel就把整个新手奖励当成普通活动去读。
独立的部分
项目中有独立的新手奖励实现：
	独立 Model：NoviceRewardModel.lua
	独立主界面：UI_NoviceReward_MainView.lua
	独立大厅入口：UI_Lobby_RightUp_NewBieReward.lua
	独立配置访问层：NoviceRewardConfTable.lua
	独立 UI 目录：System/NoviceReward/

### 2.拍脸是什么？
“拍脸”就是达到条件后自动弹到用户面前的强展示窗口。它通常受场景、优先级、平台、等级、频率和业务状态共同控制。

### 3.新手奖励整体结构和拍脸整体结构？
```lua
新手奖励配置
    ↓
NoviceRewardConfTable / ActivityTable
    ↓
NoviceRewardModel
    ↓
大厅入口 / 新手奖励主界面 / 各子页签

```

```lua
登录完成、返回大厅等场景
    ↓
PushFaceModel 收集符合条件的拍脸配置
    ↓
PushFace_SevenDayBP.NeedShow()
    ↓
NoviceRewardModel 判断有没有未领取奖励
    ↓
PushFace_SevenDayBP.HandleShow()
    ↓
ActivityModel:ShowPushFaceActivity(activityId)
    ↓
打开对应的新手七日奖励页面

```
### 4.配置表的UIName的挂在名称是UI_SevenDayBP_MainView，但是实际读取的是UI_SevenDayFreeCheckIn_MainView，走的代码的替换逻辑
![[Pasted image 20260729104423.png]]
### 5.奖励导航的结构
```lua
UI_NoviceReward_MainView                       新手奖励顶层窗口
├─ w_list_TagList                              左侧页签列表
│  ├─ UI_NoviceReward_Tab                      奖励导航
│  ├─ UI_NoviceReward_Tab                      新手7天礼
│  └─ UI_NoviceReward_Tab                      新手任务送
│
└─ w_namedSlot_SubPage                         右侧动态页面挂点
   │                                           配置表存在排序，默认加载奖励导航
   │
   ├─ UI_NoviceNavigation_View                 奖励导航页面
   │  └─ w_List_Info                           奖励导航卡片列表
   │     └─ UI_NoviceNavigation_Item1          奖励导航卡片
   │
   ├─ UI_SevenDayBP_MainView                   七日礼付费版
   ├─ UI_SevenDayFreeCheckIn_MainView          七日礼免费版
   ├─ UI_Task_NoviceTaskPage                   新手任务页
   └─ UI_Model_GameGuide_V2                    玩法任务页


```

### 6.调用链一： 进入新手奖励，默认线上奖励导航

UI_NoviceReward_MainView:OnOpen()
```lua
UI_Lobby_RightUp_NewBieReward                  大厅新手奖励入口
└─ OnClickedBtnNoviceReward()                  点击新手奖励按钮
   └─ UIManager:OpenWindow()
      └─ UI_NoviceReward_MainView              打开新手奖励顶层窗口
         └─ OnOpen(Data)
            ├─ self.Data = Data                保存外部传入参数
            ├─ self.m_PageInfo = {}            初始化一级页签列表
            ├─ OnInitializedEvent()            绑定返回按钮等事件
            │
            ├─ InitData()                      初始化页面数据
            │  └─ OnRefreshPanelData()
            │     ├─ GetResNoviceRewardTabData()
            │     │                             读取“新手奖励系统页签”配置
            │     │
            │     ├─ 遍历 ResNoviceRewardTabData
            │     │  ├─ CheckNoviceTabActiveStatus(value, true)
            │     │  │                             检查一级页签能否显示
            │     │  │
            │     │  ├─ GetExtendPageInfoByTask(pageValue)
            │     │  │                             补充活动、任务数据
            │     │  │
            │     │  ├─ 七日礼页面判断
            │     │  │  ├─ isSevendDayBPUMG = true
            │     │  │  │  └─ UI_SevenDayBP_MainView
            │     │  │  └─ isSevendDayBPUMG = false
            │     │  │     └─ UI_SevenDayFreeCheckIn_MainView
            │     │  │
            │     │  └─ table.insert(self.m_PageInfo, pageValue)
            │     │
            │     ├─ table.sort(self.m_PageInfo)   按 sortId 排序
            │     └─ 设置 index、maxIndex          生成运行时页签下标
            │
            ├─ InitEvent()                         注册页签事件
            │  ├─ Event_OnChangeNoviceTab
            │  │  └─ OnChangeTabInfo()             Item1 跳转使用
            │  └─ UI_CommonComp_Tab_Click
            │     └─ OnSelectedTabChanged()        公共 Tab 切换使用
            │
            └─ InitUI()
               └─ BindTimer(0.05)
                  └─ RefreshUI(jumpUIName)
                     ├─ jumpUIName 为空
                     │  └─ firstPage = self.m_PageInfo[1]
                     │     └─ UI_NoviceNavigation_View
                     │
                     ├─ SetCommonTabSelectInfo(viewTag, 1)
                     │                             默认选中第一个 Tab
                     │
                     ├─ ListSetDatasByFrame(w_list_TagList, m_PageInfo)
                     │  └─ 创建多个 UI_NoviceReward_Tab
                     │     └─ UI_NoviceReward_Tab:OnOpen(Data)
                     │
                     └─ RefreshRightPage(UI_NoviceNavigation_View)
                        ├─ 查找对应 PageInfo
                        ├─ self.m_CurrentUIName =
                        │      UI_NoviceNavigation_View
                        │
                        └─ AddWidgetAsyn()
                           └─ UI_NoviceNavigation_View:OnOpen(PageInfo)
                              ├─ OnInitializedEvent()
                              ├─ InitData()
                              ├─ InitEvent()
                              └─ InitUI()
                                 └─ RefreshUI()
                                    ├─ GetResNoviceRewardPageData()
                                    │   读取“新手导航页签”配置
                                    │
                                    ├─ 遍历 PageData
                                    │  ├─ IsInVersion()
                                    │  ├─ CheckNoviceTabActiveStatus(
                                    │  │      value, false)
                                    │  └─ 加入 self.OpenPageList
                                    │
                                    ├─ 按 sortId 排序
                                    └─ RefreshListInfo()
                                       ├─ GetTaskPageCfgDBySystemId()
                                       │  ├─ 查询 PageA
                                       │  └─ 查询 PageB
                                       │
                                       ├─ 检查任务、奖励状态
                                       ├─ 生成 self.OpenPageListAB
                                       └─ ListSetDatasByFrame(
                                              w_List_Info,
                                              OpenPageListAB)
                                          └─ UI_NoviceNavigation_Item1
                                             └─ OnOpen(Data)


```

### 7.调用链二：点击导航卡片 Item1 跳转页签

```lua
UI_NoviceNavigation_View                     当前处于奖励导航页面
└─ w_List_Info                               奖励导航卡片列表
   └─ UI_NoviceNavigation_Item1              某一张奖励导航卡片
      └─ w_btn_Go                            “前往”按钮
         └─ OnClickedBtnGo()
            ├─ GetResNoviceRewardPageDataById(
            │      self.Data.systemId)
            │                                  根据 systemId 查询目标页面
            │
            ├─ ResNoviceRewardPageCfg.uiName   得到配置中的目标 UI
            │
            ├─ GetIsSevenDayBPOpen()           七日礼特殊处理
            │  ├─ isSevendDayBPUMG = true
            │  │  └─ UI_SevenDayBP_MainView
            │  └─ isSevendDayBPUMG = false
            │     └─ UI_SevenDayFreeCheckIn_MainView
            │
            └─ DispatchEvent(
                   Event_OnChangeNoviceTab,
                   uiName)
               └─ UI_NoviceReward_MainView
                  └─ OnChangeTabInfo(uiName)
                     ├─ 遍历 self.m_PageInfo
                     ├─ 根据 uiName 找到目标 PageInfo
                     └─ DispatchEvent(
                            UI_CommonComp_Tab_Click,
                            PageInfo)
                        │
                        ├─ UI_NoviceReward_MainView
                        │  └─ OnSelectedTabChanged(PageInfo)
                        │     ├─ SetCurRechageTab(PageInfo)
                        │     ├─ 根据 PageInfo.index 查找页面
                        │     ├─ RefreshRightPage(PageInfo.uiName)
                        │     │  ├─ RemoveChildWidget(
                        │     │  │      w_namedSlot_SubPage)
                        │     │  │       移除 UI_NoviceNavigation_View  --因为此处是从首页的导航页面点击进入的，所以移除这个导航的view
                        │     │  │
                        │     │  ├─ 更新 self.m_CurrentUIName
                        │     │  └─ AddWidgetAsyn()
                        │     │     └─ 目标页面:OnOpen(PageInfo)
                        │     │
                        │     └─ CachePageStatus(
                        │            PageInfo.uiName, true)
                        │
                        └─ 所有 UI_NoviceReward_Tab
                           └─ OnSelectBtnIdxUpdate(PageInfo)
                              ├─ 目标 Tab
                              │  ├─ SetCommonTabSelectInfo()
                              │  ├─ AnimationPlayForward()
                              │  └─ 切换成选中状态
                              │
                              └─ 其他 Tab
                                 └─ 切换成未选中状态
UI_CommonComp_Tab_Click 是事件广播。主界面和所有 Tab 都会收到，监听者之间不依赖固定执行顺序。
```
## 8.调用链三：直接点击左侧 Tab 切换页签
```lua
UI_NoviceReward_MainView                     新手奖励顶层窗口
└─ w_list_TagList                            左侧 Tab 列表
   └─ UI_NoviceReward_Tab                    用户点击的目标 Tab
      └─ w_btn_CheckIn                       Tab 点击按钮
         └─ OnClickedBtnCheckIn()
            ├─ IsLocked()
            │  ├─ true
            │  │  ├─ _ShowLockedTips()
            │  │  └─ return
            │  │
            │  └─ false
            │
            ├─ 普通页签
            │  └─ OnClickedBtnCallBack()
            │
            └─ UI_Model_GameGuide_V2
               ├─ CheckGameGuideIsOpen()
               ├─ CheckPakIsReadyByGroupId()
               └─ 资源准备完成
                  └─ OnClickedBtnCallBack()
                     │
                     ├─ GetCommonTabSelectInfo(viewTag)
                     │
                     ├─ 判断是否已选中
                     │  ├─ 已选中
                     │  │  ├─ isHasSelect = true
                     │  │  ├─ GetRedDotIdListByTagId()
                     │  │  └─ 没有红点操作则 return
                     │  │
                     │  └─ 未选中
                     │     └─ SetCurSelectActivityInfo(nil)
                     │
                     └─ DispatchEvent(
                            UI_CommonComp_Tab_Click,
                            self.Data,
                            isHasSelect)
                        │
                        ├─ UI_NoviceReward_MainView
                        │  └─ OnSelectedTabChanged(self.Data)
                        │     ├─ SetCurRechageTab(self.Data)
                        │     ├─ PageInfo =
                        │     │      m_PageInfo[self.Data.index]
                        │     │
                        │     ├─ RefreshRightPage(PageInfo.uiName)
                        │     │  ├─ RemoveChildWidget()
                        │     │  ├─ 更新 m_CurrentUIName
                        │     │  └─ AddWidgetAsyn()
                        │     │     └─ 目标页面:OnOpen(PageInfo)
                        │     │
                        │     └─ CachePageStatus()
                        │
                        └─ 所有 UI_NoviceReward_Tab
                           └─ OnSelectBtnIdxUpdate(self.Data)
                              ├─ 当前目标 Tab
                              │  ├─ SetCommonTabSelectInfo()
                              │  ├─ 播放选中动画
                              │  └─ 显示选中状态
                              │
                              └─ 其他 Tab
                                 └─ 显示未选中状态

```
![[Pasted image 20260729170400.png]]