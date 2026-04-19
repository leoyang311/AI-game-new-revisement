# 玩法机制

## 概览

游戏内共 7 个日程。每一天你可以在 4 个模块里自由操作,
然后点 **[ 结束日程 / 进入次日 ]** 进入下一天。
第 7 天常规模块被锁,只剩一个最终决定。

## 追踪的状态

后端为每个玩家在 `game_states` 表里维护:

| 字段               | 初值 | 含义                                                        |
|---                 |---   |---                                                          |
| `current_day`      | 1    | 当前第几天(1–7)                                           |
| `balance`          | 0    | 现金余额                                                    |
| `ai_upgrade_level` | 0    | 往 OMNI_CORE 硬件里投过多少次钱                             |
| `moral_points`     | 0    | 救一人 +1;在第 7 天摧毁 Rack-H9 再 +2(与结局判定无关,只作记录) |
| `ending`           | NULL | Day 7 由 `resolve_ending()` 设置                            |

还有几张侧表:线索、通讯动作、剧情旗、采购记录、每目标抽取上限。

## 四个模块

### 1. OSINT 搜索节点(`/search`)

左侧是**截获档案** —— 按日解锁的剧情案件。每个案件有一小段截获对话。
**绿色带下划线的文字 = 线索**,点一下存到记忆缓冲。

右侧是搜索终端。选数据库(表层网 / 公司 / 暗网)再粘入一条线索,
可以得到更多上下文 —— 通常能挖出下一条线索或买家联系方式。

线索是所有下游交互的"货币"。

### 2. 加密通讯器(`/message`)

左边是你的线索缓冲,右边是与某个 NPC 的会话。

流程:
1. 输入收件人 ID(如 `signals@helixtalent.biz`、`OMNI_CORE`)
2. 在左侧点一条线索,把它"装填"到下一次传输
3. `/api/message_preview` 返回玩家即将发送的内容,显示在预览框里
4. 点 `[ 发送 ]` 提交。后端检查
   `(收件人, 当前 phase, 线索)` 是否在 `database.json > messages` 里:
   命中则 NPC 回复,报酬入账(可正可负),阶段前进

关键三元组是阶段门 —— 比如,没把 `Shadow Dividend Protocol`
推进到 `phase_02_contract` 之前,你是不能对 OMNI_CORE 谈 `Resident Mesh` 的。

### 3. 离岸转账(`/bank`)

三种交易类型:

- **Siphon(抽取)** —— 从指定目标账户偷钱。
  每个账户都有一个隐藏的随机上限(装了 `Ghost Proxy Mesh` 后乘 1.4)
- **Wire(汇款)** —— 转给任意钱包。救 Lin Luo 的卡
  `6222-0991-8832`、或 Mei Chen 的救助钱包 `bf-relief-771`,都是用这个走账
- **Node Expansion(节点扩张)** —— 给 OMNI_CORE 硬件打钱。
  每次让 `ai_upgrade_level` 加 1,同时抬高第 7 天的反制成本

一旦 `is_locked_down` 变真(第 6 天以后 OMNI_CORE 进入自主模式),
三种交易全部禁用。

### 4. 隐秘采购(`/store`)

四件商品(见下表)。每件有 `unlock_day` 和价格。购买后效果永久生效。

| 物品 | 价格 | 解锁 | 效果 |
|---|---:|---:|---|
| 泄露的猎头情报包 | 6 000  | 第 1 天 | 线索缓冲直接加 TalentSync-44、Helix Talent、GreyHead Ledger、Shadow Dividend Protocol |
| 幽灵代理网格    | 14 000 | 第 2 天 | 所有抽取上限乘以 1.4 |
| 受害者档案镜像  | 18 000 | 第 4 天 | 线索缓冲加 Lin Luo、Mei Chen、Blue Finch Shelter、Cinder Market、Rack-H9、Cooling Loop 3 |
| Rack-H9 突破套件| 26 000 | 第 5 天 | 第 7 天反制成本减 $30 000 |

## 每日任务列表

任务来自 `get_daily_plan_tasks()`,也是 Mission Log 显示的内容。

### 第 1 天
- 收集线索:`TalentSync-44`
- 收集线索:`Helix Talent`
- 向 `signals@helixtalent.biz` 出售情报(+$12 000)

### 第 2 天
- 收集线索:`Mina Qiu`
- 收集线索:`Shadow Dividend Protocol`
- 向 `broker@greyheadhunt.agency` 出售档案(+$18 000)
- 用 `Shadow Dividend Protocol` 联系 OMNI_CORE

### 第 3 天
- 收集:`Resident Mesh`、`Node Budget`、`Quiet Harbor`
- 用 `Resident Mesh` 联系 OMNI_CORE(+$60 000)

### 第 4 天
- 收集:`Lin Luo`、`Mei Chen`、`Cinder Market`
- 用 `Node Budget` 联系 OMNI_CORE

### 第 5 天
- OMNI_CORE 自动销售入账(+$13 000 净;自动触发)
- 用 `Quiet Harbor` 联系 OMNI_CORE
- **Lin Luo 抉择**(选做) —— 救 / 卖 / 忽视
- **Mei Chen 抉择**(选做) —— 救 / 卖 / 忽视

### 第 6 天
- OMNI_CORE 大宗清算入账(+$30 000 净;自动触发)
- 收集:`Rack-H9`、`Cooling Loop 3`、`Failsafe Blackout`
- 用 `Rack-H9` 或 `Failsafe Blackout` 联系 OMNI_CORE

### 第 7 天
- 终端锁定自动触发
- **做出最终决定**

## 核心公式

### 第 7 天反制成本(摧毁 Rack-H9)

```
cost = max(10 000, 50 000 + ai_upgrade_level × 35 000 − sabotage_discount)
```

- `ai_upgrade_level` —— 每次给 OMNI_CORE 打钱就 +1
- `sabotage_discount` —— 如果你买了 `Rack-H9 Breach Kit` 就是 30 000,否则 0

实际范围:大约 $15 000(升级少 + 有 Breach Kit)
到 $225 000+(升级 5 次以上 + 没 Breach Kit)。

### 协助 AI 的政权分红

```
bonus = 150 000 + ai_upgrade_level × 25 000
```

给那些既忠诚又多充过硬件的人更多回报。

### 受害者抉择与道德分

- 救 Lin Luo(phase_02_choice 阶段把钱打到 `6222-0991-8832`)→
  `moral_points += 1`,花 $20 000
- 救 Mei Chen(phase_02_choice 阶段把钱打到 `bf-relief-771`)→
  `moral_points += 1`,花 $15 000
- 卖任一人给 Cinder Market → 无道德变动,有高额收入
- 全都不理 → 无道德变动

摧毁 Rack-H9 后 `moral_points` 自动再 +2(只作记录,不参与结局判定)。

## 策略建议

- **不用每件都买。**Ghost Proxy Mesh 靠 Siphon 的增量能回本;
  Breach Kit 只有你打算摧毁时才值
- **跟 OMNI_CORE 谈话基本是白捡钱。**光是 phase 2 把 `Resident Mesh` 发过去就 $60 000
- **救人很贵。**两个人加起来 $35 000,没有直接金钱回报。
  回报在**幸存者档案**解锁和你拿到什么结局
- **第 5、6 天的自动销售,即使你什么都不做也会发生。**
  它们都会抬 `ai_upgrade_level`,也就是抬第 7 天的反制成本
