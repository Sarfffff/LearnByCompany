### 1.UI的搭建
1.可以使用通用的组件和组件：
	通用按钮 UI_CommonBtn_XXX
	通用组件 UI_Componet_xxxxx
	通用弹框
搭建完UI后，使用工具一键生成对于的lua代码进行相关事件的绑定

### 生成对应的Lua脚本
#### 1.主玩法生成
 在对于的UMG界面右键->ScriptedActions->GenerateLuaCode会生成或修改下图中的3个文件
 ![[Pasted image 20260706092327.png]]
 备注：当前有2个命令，分别对应在第一次生成和后续生成时使用，区别是第一次生成会强制覆盖View字段
 1、WindowName：生成了操作界面的key，如：_MOE.UIManager:OpenWindow(_MOE.WindowName.UI_Mental_MyPropPopUp)，一般不需要手动修改
![[Pasted image 20260706092632.png]]
2、WindowSoundConfig：生成了每个界面打开和关闭时需要播放的声音，该声音会在BaseViewClass的Open和Close函数中调用，生成后会填充默认的开关音效，根据自己的需要来修改，目前已修改到UMG属性中
![[Pasted image 20260706092649.png]]
 3、UIWndNameToLuaPath：生成了每个界面名称对应的绑定lua文件位置，一般不需要手动修改，目前已修改到UMG属性中
![[Pasted image 20260706092722.png]]
4、界面绑定对应的lua文件，一般在对应的InitData、InitEvent、InitUI中书写自己UI的数据、事件及显示逻辑
![[Pasted image 20260706092802.png]]
ps：新增界面后需要生成对应的AssetNameMapping文件，否在在创建界面时会找不到对应的umg文件

#### 2.特色玩法生成
 #1、生成区别
	主玩法根路径对应"Content\LetsGo\…"
	特色玩法根路径对应"Content\Feature\<FeatureName>\…"
因此，对应生成的3个界面文件示例为：
![[Pasted image 20260706093238.png]]
1、WindowName 在使用时需要添加后缀，如_MOE.UIManager:OpenWindow(_MOE.WindowName_DDB.UI_Mental_MyPropPopUp)
![[Pasted image 20260706093247.png]]
2、UIWndNameToLuaPath 指向的lua路径也是对应玩法中的路径，一般不需要修改，目前已修改到UMG属性中
![[Pasted image 20260706093302.png]]
#2、路径添加

新增副玩法需要在Content\LetsGo\Script\Config\FeatureNameConfig.lua中添加对应的ScriptPath位置及AssetNamePath 位置
![[Pasted image 20260706093311.png]]
2、如果该玩法是通过下载后启动的，则需要在下载资源完成后，调用_MOE.FeatureNameConfig.LoadWindowConfigByFeatureName(FeatureName) 来加载对应的4个文件(该步骤暂时不需要，请忽略)

#3、自定义特色玩法全局mod名

在特色玩法隔离需求中，部分特色玩法需求把全局变量_MOE替换成自己定义的别名，比如农场需要替换为_Farm，如下图所示：
![[Pasted image 20260706093417.png]]
特色玩法如果有相关需求，可以在模板文件LetsGo-Develop\LetsGo\Content\Editor\FeatureNameDefine.txt中新增自己的别名，key为特色玩法的mod名，value为全局变量名。

如下图所示：
![[Pasted image 20260706093345.png]]
如果配置自定义全局变量名，则在生成UMG界面的lua脚本时会把全局变量_MOE替换调，否则保持为_MOE不变

上述的内容包括了UI搭建以及生成对应的lua代码实现具体的逻辑操作，但是对于资源映射的关系并未处理。以下是资源配置映射的处理和为什么需要的原因。

### 资源映射处理

原因：游戏运行时会动态加载各种类型的==资产==文件，而这些资产会配置在各个excel表格、UE的datatable等等各个地方，为了方便加载和配置，游戏内提供了一个统一的资产管理文件：AssetNameMapping.txt，其结构map文件，key为资产名称，value为该资产在工程内的路径。

#### 第一步：生成AssetNameMapping的前提
1.需要告诉系统需要哪些资源文件，AssetNameMapping文件生成是根据我们指定的文件目录和该目录下资源类型来生产的，因此需要配置文件AssetDirectorySetTable.uasset,在该datatable中，按照需要配置我们想要加载的文件，其配置内容如下图所示：
![[Pasted image 20260706095348.png]]
2.AssetDirectorySetTable结构说明：
	RowName:该行配置的别名，为了方便阅读，一般命名为资源类型名
	Asset Filter:需要动态加载的资产类型
	Asset Directory:需要动态加载的资产所在的目录
如上截图中第三行配置作用：加载目录/Game/LetsGo/Blueprints/UI下的所有UMG资产。

3.目录配置文件AssetDirectorySetTable.uasset
	主玩法文件所在目录：/Content/LetsGo/Data/AssetData/AssetDirectorySetTable.uasset
	各feature玩法文件所在目录（以FPS玩法为例）：/Content/Feature/FPS/Data/AssetData/AssetDirectorySetTable_FPS.uasset

不同玩法都有自己独立的文件配置，文件目录在各个feature根目录下的/Data/AssetData目录中，文件名为AssetDirectorySetTable_xxxxx.uasset

#### 第二步：什么时候需要生成AssetNameMapping.txt文件
当我们操作的资产所在目录，在AssetDirectorySetTable.uasset中配置了，那么我们进行以下操作时，需要重新生成该文件：
	1.新增
	2.重命名
	3.删除
	4.变更资产目录
如果不确定当前目录是否有配置，可以在文件操作完成后，都重新执行命令来生成AssetDirectorySetTable.txt。多生成几次不会有任何问题，但是少生成可能会导致资源无法加载

#### 第三步：如何生成对应的AssetNameMapping.txt文件

项目的的结构被划分为主玩法仓库和多个单独Feature玩法仓库，两者在生成时有一点点区别。
1.关于主玩法的生成方式
![[Pasted image 20260706100210.png]]

启动editor之后，会在顶部看到一个ClientTools入口，点击后选择GenerateAassetNameMap指令，即可生成，生成文件和路径如下图所示。

2.关于各Feature玩法的生成方式
![[Pasted image 20260706100201.png]]
1、点选Content/Feature目录下的各Feature目录名称，然后右键，在出现的菜单栏中选择“生成AssetNameMapping资源映射”即可。生成的结果为各个Feature的/Data/AssetData目录下
示例：生成结果
![[Pasted image 20260706100154.png]]
2、重要！重要！重要！添加副玩法时，需要修改仓库https://git.woa.com/TimiT1/MOE/LetsGo/BuildTools.git中的BuildTools\Config\PackConfig.csv文件，把对应目录添进DirectoriesToAlwaysStageAsUFS，否则打包时无法把该文件打入
![[Pasted image 20260706100146.png]]
#### 资源重名

因为AssetNameMapping.txt文件其结构为key-value 的map文件，key为资产名称，所以我们需要保证资产在工程内命名是唯一的，否则会导致加载不到自己预期中的文件问题。各个feature在新增资产时最好加上自己feature名的前缀，和其他feature来做区分。

最后强调一下：文件名唯一，此为强制规则！

#### 表格配置长路径支持

目前游戏内有部分副玩法商品需要在主玩法的商城中售卖，这样就需要把副玩法对应的分包下载完成后，加载AssetNameMapping.txt才能显示对应的商品。因此，为了省去AssetNameMapping.txt的加载，表格里支持长路径配置，比如：

	1.图片配置 ：/Game/LetsGo/Assets/Textures/UI/Coin/Frames/T_Common_Icon_Coin_10.T_Common_Icon_Coin_10
	2.UMG 界面UI配置：/Game/LetsGo/Blueprints/UI/UGCEditor/Program/Item/UI_BagTag_Item.UI_BagTag_Item_C
	3.动画配置：/Game/LetsGo/Assets/Animation/Characters/Common/OutLevel/AS_CH_OutIdle_001.AS_CH_OutIdle_001

配置长路经时，加载接口不变，lua测依然使用 _MOE.AssetMgr:LoadAssetObject(AssetPath) 来加载对应资源。

如果一个资源配置的为长路径，就不需要生长AssetNameMapping.txt资源映射表，也能成功加载到对应资源。


# 随记
1.活动中心配置xlsx路径：D:\LetsGoEditor\Editor\letsgo_common\excel\xls
2.重点关注配置表：活动详细UI界面名
3.新增活动玩法
	活动中心配置表添加活动，包括各种字段
		配置完成后点击D:\LetsGoEditor\Editor\letsgo_common\excel\ClientExcelConverter-LetsGo.bat执行之后，选择需要导出的表格，执行导出命令
		![[Pasted image 20260706114149.png]]
		每当有新的表格创建，或者存量表格字段变更时，前端需要手动生成一次pb,生成pb的脚本为：【协议导表PB】【新】- LetsGo.bat
		![[Pasted image 20260706115442.png]]
		目前工程内提供了工具来生成表格的读取接口，对应的脚本工具为：letsgo_common\excel\一键更新生成Table的lua对象(关闭表格).bat
		![[Pasted image 20260706115603.png]]
	为什么需要导表的原因和作用
		原因：1.程序读不了Excel格式 2.必须保证前后端格式一致
		作用：1.把Excel文件转成程序能读的文件 2.自动同步配置更新 3