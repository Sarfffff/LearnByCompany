# layout规则
包含五个UMG蓝图：FirstCharge_SubView,FirstCharge_MainView,FirstCharge_MainViewBG1,FirstCharge_TabItem,FirstChagre_SixCharge_SubVIew。

#FirstCharge_SubView:
	![[Pasted image 20260721110115.png|1557]]
``` c
CanvasPanel_0 (全屏)
├── w_nameSlot_SubView [VAR]     全屏Fill     ← 子界面挂载点
├── Overlay_78                    左上角       ← Tab列表容器
│   └── w_list_GiftTag [VAR]      Vertical    ← Tab ListView
└── w_nameSlot_SelfMoney [VAR]    右上角       ← 货币显示
```
关键规则：
	w_nameSlot_SubView 必须全屏 Fill，子界面才能铺满
	w_nameSlot_SelfMoney 必须 ZOrder=2，浮在子界面上方
	w_list_GiftTag 的 Padding Top=17，让红点有溢出空间
	Overlay_78 设 ClipToBounds，Tab 列表超出部分被裁剪
	ListView: EntryWidgetClass = FirstCharge_TabItem，ScrollBarVisibility = Collapsed

#FirstCharge_TabItem:
	![[Pasted image 20260721110242.png|1552]]
``` c
Overlay_0 (AutoSize, 居中)
├── w_img_Tag [VAR]        HAlign_Left,  VAlign_Top     ← 主题图标
├── w_img_Select [VAR]     HAlign_Fill,  VAlign_Fill    ← 选中高亮框
│   Padding: -6/-18/-7/-5（向外扩展一圈）
├── Overlay_34             HAlign_Fill,  VAlign_Bottom   ← 底部文字区
│   ├── Image_67           HAlign_Center,VAlign_Fill    ← 文字背景条
│   └── w_txt_name [VAR]   HAlign_Center,VAlign_Center  ← Tab名称
├── UI_CommonComp_RedDot   HAlign_Right, VAlign_Top     ← 红点
│   Padding: -35/-25（溢出到右上角外部）
└── w_btn_Select [VAR]     HAlign_Fill,  VAlign_Fill    ← 点击按钮（覆盖全区域）

```
关键规则：
	负值 Padding = 控件向外扩展（高亮框、红点溢出）
	w_btn_Select 必须 Fill+Fill，确保全区域可点击
	父类必须 WBP_ListWidgetBase_C（包含 UserObjectListEntry 接口）

#FirstCharge_MainView:
	![[Pasted image 20260721110538.png|1509]]
```c
CanvasPanel_0 (全屏)
├── UI_CommonComp_Preview_78 [VAR]   顶部居中     ← 3D预览组件（非2D背景！）
├── CanvasPanel_91                    正中心       ← 装饰元素（可删除）
├── HorizontalBox_115
│   └── w_txt_TitleName [VAR]                     ← 标题文本
├── Overlay_757                       正中心       ← 奖励列表区
│   └── w_switcher_List [VAR]                     ← 列表切换器
│       ├── [0] w_list_ShowSevenDaysRewards  Horizontal  ← 7天奖励
│       └── [1] w_list_ShowRewards           Horizontal  ← 普通奖励
├── Overlay_855
│   └── w_horizontal_price
│       ├── w_img_Icon [VAR]                       ← 货币图标
│       └── w_txt_Price [VAR]                      ← 价格文本
└── Overlay_3
    └── w_switcher_Recharge [VAR]                  ← 充值按钮切换器
        ├── [0] UI_CommonBtn_Recharge               ← 可点击充值按钮
        └── [1] 已充值标签                          ← 不可点击

```
关键规则：
	UI_CommonComp_Preview_78 是 3D 预览组件，背景和角色位置由 Camera_Recharge 的 PreviewLevel 配置决定，不是 BP 里的 2D 图片
	w_switcher_List 通过 ActiveWidgetIndex 切换 7天列表和普通列表
	两个 ListView 都是 Horizontal 方向，SelectionMode = Multi
	w_switcher_Recharge 通过 ActiveWidgetIndex 切换充值按钮和已充值标签

#FirstChagre_SixCharge_SubVIew:
	![[Pasted image 20260721110730.png|1600]]
```c
w_switcher_List
└── [0] 三天分列奖励（替换 7天列表）
    └── HorizontalBox
        ├── w_list_ShowSevenDaysRewards1  ← 第1天
        ├── w_list_ShowSevenDaysRewards2  ← 第2天
        └── w_list_ShowSevenDaysRewards3  ← 第3天

额外控件：
├── w_img_ItemIcon_1 [VAR]  SpineWidget  ← 动画1
└── w_img_ItemIcon_2 [VAR]  SpineWidget  ← 动画2

```
关键规则：
	六充 BP 没有 UI_CommonBtn_Recharge，Lua 中不绑定该按钮
	三个 ListView 横向排列，各包在 SizeBox 中限宽