完整的三层架构设计
![[Pasted image 20260806111259.png|431]]
1.数据驱动层：数据来源主要是两类配置表数据，以及热更数据
	配置表数据：由excel根据proto协议结构转成pbin结构，再有PushFaceTable进行合表读取。绝大多数拍脸配置是稳定的，随版本打包即可，加载快、不依赖网络
	热更数据：当需要紧急上线/下线某个拍脸时，不用等发版，改 KV 配置即可实时生效

PushFaceTable的作用：
```lua
① 读静态配表
   PushFace.pbin（P_拍脸.xlsx 导出的数据，结构定义在 ResPushFace.proto）
   → 提供 GetPushFaceData()（合表）/ GetPushFaceDataById(id)（查单行）/ GetPushFaceData_TotalConfig()（单分表）

② 融合动态配置
   LoadWebConfig() 从 KV 系统异步拉线上配置（触发精度 id=10001000）存成 WebConfig
   → 在场景查询时合并进去，和静态表一视同仁

③ 给拍脸系统提供两个业务查询
   GetPushfaceConfigBySceneId(场景id) → 返回该场景所有候选拍脸项数组（静态+动态融合）
   GetPushfaceConfigByActivityId(活动id) → 按活动 id 直查某一行
```
