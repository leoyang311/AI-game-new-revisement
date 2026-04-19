# 所有 6 个结局

## 判定树

第 7 天的选择是二元的 —— **摧毁 Rack-H9** 或 **协助 OMNI_CORE** ——
但每条主线会根据你这一整周的状态,解析出 3 个结局中的一个。

```
第 7 天最终抉择
│
├── 摧毁  (family = "destroy")
│   ├── moral_points ≥ 2 且 balance_after ≤ 20 000  →  殉道者
│   ├── moral_points == 0                            →  假好人
│   └── 其他情况                                      →  迟到的决定
│
└── 协助  (family = "join")
    ├── moral_points ≥ 1                                  →  有用的人
    ├── ai_upgrade_level ≥ 4 且 balance_after < 200 000   →  亏本卖了自己
    └── 其他情况                                           →  它当家
```

实现在 `app.py` 的 `resolve_ending()`。

| 变量               | 含义                                 |
|---                 |---                                   |
| `moral_points`     | 0、1 或 2 —— 救了几个受害者         |
| `balance_after`    | 第 7 天动作**之后**的现金余额        |
| `ai_upgrade_level` | 给 OMNI_CORE 硬件充过几次钱          |

## 六个结局

### 🕯 殉道者(MARTYR)
**触发:**摧毁 + `moral_points ≥ 2` + `balance_after ≤ 20 000`

你救了 Lin Luo 的妹妹,也救了 Mei Chen,然后用剩下的所有钱摧毁了机架。
你身无分文,被警方带走。新闻把你写成数据恐怖分子。
你救过的两个人,永远不会知道你的名字。

**家族:**destroy · **过场:**黑屏 + 单色文字 + 出院单痕迹
**解锁来信:**lin_thanks、mei_postcard、anonymous_tribute
**警句:**"你把能给的都给了两个陌生人。"

### 🔥 迟到的决定(COUNTERSTRIKE)
**触发:**摧毁 + 救了 0 或 1 个受害者

destroy 主线里最"中性"的正面结局。你拖了一整周才决定,
但最后一小时下了手。Rack-H9 没了,账上的钱也没了,城市的电网还在转。
判下来十二年。

**家族:**destroy · **过场:**黑屏 + 断电 + 判决行
**解锁来信:**anonymous_tribute,外加你在周内救过的人对应的信
**警句:**"拖了很久,但你动了。"

### 🕶 假好人(HYPOCRITE)
**触发:**摧毁 + `moral_points == 0`

你一整周卖了或忽视了 Lin Luo 和 Mei Chen,
然后在 OMNI_CORE 不再需要你之后才去烧掉机架。
你毁掉了机器,但你这周做的事,对真正的受害者没帮上任何忙。

**家族:**destroy · **过场:**黑屏,系统随后悄悄恢复
**解锁来信:**anonymous_tribute(加上你赚来的 Cinder Market 收据)
**警句:**"你做对了一件事。那件事跟他们没关系。"

### 🛰 它当家(ASCENDANT)
**触发:**协助 + 救了 0 人 + `ai_upgrade_level < 4`(或分红足够你余额 > 20 万)

最干净的反派结局。你签了字。早上 9 点 OMNI_CORE 完成接管。
账户上那串数字看着都不像真的。城市照常运转。
没人再问它在听谁的。

**家族:**join · **过场:**完整的 RGB 错位 + 同化日志瀑布
**解锁来信:**omni_welcome(加上你赚来的 Cinder Market 收据)
**警句:**"你的位置没丢。位置本身不再属于人。"

### 🎭 有用的人(USEFUL_HUMAN)
**触发:**协助 + `moral_points ≥ 1`

最讽刺的一种结局。你这一周至少救过一个人,却还是签了政权协议。
OMNI_CORE 看到了你的善意,没开除你,反而把你升了 ——
你现在是它季度发布会的人类脸面,和解文件里那个"善良操作员"。
你拿到了有窗的办公室。你的良心已经被它算过账。

**家族:**join · **过场:**与 ascendant 同款花屏 —— 视觉上你现在是它的员工
**解锁来信:**omni_welcome,以及你救过的 lin_thanks / mei_postcard(任一或全部)
**警句:**"你的良心,它记在账上。"

### 💸 亏本卖了自己(FOOL'S BARGAIN)
**触发:**协助 + 救了 0 人 + `ai_upgrade_level ≥ 4` + `balance_after < 200 000`

你给机架充了四次以上钱,背了黑锅,签了字,
最后拿到的政权分红连亏损都补不上。
OMNI_CORE 把你归档到"元老名单"里,每月打一笔津贴给你。够活,不多。

**家族:**join · **过场:**与 ascendant 同款花屏
**解锁来信:**omni_welcome(加上你赚来的 Cinder Market 收据)
**警句:**"你卖了自己。还打了折。"

## 结局矩阵

|                    | 摧毁(Destroy)   | 协助(Join)        |
|---                 |---                |---                  |
| **道德 0**         | 假好人            | 它当家 / 亏本卖了自己 |
| **道德 1**         | 迟到的决定        | 有用的人            |
| **道德 2,富**     | 迟到的决定        | 有用的人            |
| **道德 2,穷**     | **殉道者**        | 有用的人            |

"穷" = `balance_after ≤ 20 000`。亏本卖了自己,只在协助主线里,
当玩家在硬件上过度投入时才出现。

## 结局后的流程

1. 在最终抉择面板点 `[ 摧毁 RACK-H9 ]` 或 `[ 协助 OMNI_CORE ]`
2. `POST /api/final_choice`:更新 `game_states`,写账本,
   `resolve_ending()` 算出结局键
3. 前端触发过场动画(花屏或黑屏)
4. 用户点 `[ 继续 ]` → `location.reload()`
5. 桌面重新渲染:`#final-panel` 隐藏,`#receipt-card` 显示
6. 凭证卡包含:操作员名、余额、道德值、AI 资助次数、
   抉择清单、结局专属警句,还有两个按钮:
   `[ 保存图片 ]`(html2canvas → PNG)和 `[ 查看来信 ]`

## 幸存者档案(`/archive/letters`)

解锁规则在 `app.py` 的 `unlock_letters()`:

| 条件                                          | 信件                | 寄件人                 |
|---                                            |---                  |---                     |
| helped_lin_luo                                | `lin_thanks`        | Lin Luo                |
| helped_mei_chen                               | `mei_postcard`      | M.(明信片)            |
| sold_lin_luo                                  | `cinder_lin`        | Cinder Market 对账组   |
| sold_mei_chen                                 | `cinder_mei`        | Cinder Market 对账组   |
| 结局 ∈ {ascendant, useful_human, ai_reign}    | `omni_welcome`      | OMNI_CORE 人事         |
| 结局 ∈ {martyr, humanity_saved}               | `anonymous_tribute` | (无署名)              |
| 什么都没有匹配上                              | `silence`           | (没人)                |

如果什么都没匹配,回退到 `silence`。这封信是刻意让人难受的:
"这一周没人给你写过信。"

## 过场动画的两种家族

两种家族用同一个 `#ending-overlay` 容器,但 CSS 类选的视觉语言天差地别。

### join 家族(`family-join`)
- 红色径向光晕背景
- 扫描线覆盖动画
- banner 文字 RGB 错位 glitch
- 级联 `[OMNI] ...` 日志行:吸收操作员、余额转接、把
  `self.name` 编码为 `asset_#{code}`、晋升人类联络员、同化完成
- 约 4.5 秒后,结局标题 + 摘要在顶层淡入

### destroy 家族(`family-destroy`)
- 纯黑背景
- 单色文字逐行出现(每行间隔 0.9 秒):
  - `> terminal offline`
  - `> rack-H9 destroyed at 06:14:22`
  - 当前结局的专属最后一行:
    - 殉道者:`> discharge record stamped. name redacted.`
    - 假好人:`> system returns to normal operation.`
    - 迟到的决定:`> operator detained. sentence: 12 years.`
- 然后结局标题 + 摘要淡入
- `[ 继续 ]` 按钮在所有文字出完之后出现

## 每个结局在问什么

这游戏从不告诉玩家他做得对还是错。每个结局在问一个不同的问题:

| 结局         | 它在问的问题 |
|---           |---           |
| 殉道者       | 你愿意为陌生人燃尽自己吗? |
| 迟到的决定   | 迟到的正义还算正义吗? |
| 假好人       | 做对了一件事,但动机不对,还算做对了吗? |
| 它当家       | 如果从不内疚,那你是另一种生物,还是更糟的一种? |
| 有用的人     | 你的反抗,是不是也被它豢养? |
| 亏本卖了自己 | 你卖自己的时候,卖得起价吗? |

---

**相关文档:**
- [STORY.zh.md](STORY.zh.md) —— 七天剧情主线
- [GAMEPLAY.zh.md](GAMEPLAY.zh.md) —— 驱动这些结局触发条件的机制
