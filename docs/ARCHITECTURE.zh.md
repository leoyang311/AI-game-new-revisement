# 系统架构

## 技术栈

- **后端:** Python 3、Flask、SQLite(文件 `game.db`)
- **前端:** 原生 HTML / CSS / JS,无构建
- **内容:** 静态 JSON(`database.json` + `database_zh.json`)
- **生产环境:** gunicorn(3 个同步 worker)经 nginx 反代,由 systemd 管理

没有框架,没有打包器。前端外部依赖只有一个 CDN 引入
(`html2canvas`,用于把结局凭证卡导出为 PNG)。

## 仓库结构

```
.
├── app.py                    Flask 应用:路由、游戏逻辑、数据库、内容字典
├── database.json             案件/搜索/NPC 对白(英文源)
├── database_zh.json          中文覆盖层,加载时合并到英文源
├── requirements.txt          Flask + gunicorn
├── Procfile                  PaaS 一键部署
├── game.db                   SQLite(首次启动时创建,git 忽略)
├── templates/
│   ├── _theme.html           共享分片 — VS 浅色主题 + 切换按钮
│   ├── _i18n.html            共享分片 — I18N 字典 + t()/applyI18n() 助手
│   ├── login.html
│   ├── index.html            主桌面:每日简报、任务日志、结局过场
│   ├── search.html           OSINT 搜索节点
│   ├── bank.html             离岸转账
│   ├── message.html          加密通讯器
│   ├── store.html            隐秘采购
│   ├── letters.html          幸存者档案
│   └── style_preview.html    设计稿(仅开发用)
└── docs/                     本目录
```

## 请求流程

```
浏览器 ──────►  nginx :80  ─────►  gunicorn (unix:game.sock)
                                       │
                                       ▼
                                     Flask (app.py)
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                       sqlite       JSON 加载      会话 cookie
                       game.db    database*.json   (player_id, lang)
```

## 一次页面访问的数据流

```
GET /                                   (浏览器)
  └─► Flask index() → get_player_state(player_id)
        ├─► SQLite: game_states、ledger_history、message_actions、shop_purchases
        ├─► get_lang() 读 cookie `lang` → "en" 或 "zh"
        ├─► get_story_display() — 当天阶段标题 + 通告(双语)
        ├─► get_guidance_data()  — 当天目标 + 步骤(双语)
        ├─► build_shop_items()   — 已解锁物品 + 价格(双语)
        ├─► derive_decisions()   — 救 / 卖 / 忽视 三种标志位
        └─► get_ending_content() — 若结局已定,追加 title/summary/family
  └─► render_template("index.html", player=...)
        └─► index.html 在 <body> 顶部包含 _theme.html + _i18n.html
              ├─► _theme.html 在页面绘制前设置 data-theme="light"
              └─► _i18n.html 在 DOMContentLoaded 后替换 data-i18n 属性
```

## SQLite 表结构

| 表                   | 用途                                                  |
|---                   |---                                                    |
| `players`            | 用户名 → id                                           |
| `game_states`        | 每个玩家的 `current_day`、`balance`、`ai_upgrade_level`、`moral_points`、`ending` |
| `ledger_history`     | 所有交易记录(`time_text`、`desc`、`amount_text`)     |
| `player_clues`       | 已收集的线索                                          |
| `npc_progress`       | 每个 NPC 当前所处阶段                                 |
| `message_actions`    | 玩家已发送的 `(target_id, phase, clue)` 三元组        |
| `player_story_flags` | 剧情事件完成标志(`forced_sale_day5` 等)             |
| `steal_targets`      | 每玩家的抽取目标账户上限与已抽金额                    |
| `shop_purchases`     | 已购物品 ID                                           |

首次启动时由 `init_db()` 创建。`maybe_add_column()` 助手用于向后兼容地加列。

## 路由清单

页面路由(HTML):

| 方法   | 路径              | 模板               | 说明                                     |
|---    |---                |---                 |---                                       |
| GET   | `/style_preview`  | style_preview.html | 设计稿                                   |
| GET   | `/login`          | login.html         | 玩家名登记(无密码)                     |
| POST  | `/login`          | login.html         | 创建或恢复玩家                           |
| GET   | `/logout`         | —                  | 清除会话                                 |
| GET   | `/`               | index.html         | 主桌面                                   |
| GET   | `/search`         | search.html        | OSINT 搜索节点                           |
| GET   | `/bank`           | bank.html          | 离岸转账                                 |
| GET   | `/message`        | message.html       | 加密通讯器                               |
| GET   | `/store`          | store.html         | 隐秘采购                                 |
| GET   | `/archive/letters`| letters.html       | 结局后的幸存者档案                       |

JSON 接口:

| 方法   | 路径                    | 返回 / 行为                               |
|---    |---                      |---                                        |
| GET   | `/api/cases`            | 当前可见的案件列表                        |
| GET   | `/api/daily_plan`       | 每日任务及完成状态                        |
| GET   | `/api/clues`            | 玩家的线索缓冲                            |
| POST  | `/api/clues`            | 追加一条线索                              |
| GET   | `/api/bank_info`        | 当前玩家状态(余额 + 历史)               |
| POST  | `/api/transfer`         | Siphon / Wire / Upgrade_AI                |
| POST  | `/api/search`           | 在选定数据库里查一条线索                  |
| POST  | `/api/message_preview`  | 生成发送预览                              |
| POST  | `/api/send_message`     | 实际发送;可能推进阶段或发放报酬          |
| POST  | `/api/store/purchase`   | 购买物品                                  |
| POST  | `/api/advance_day`      | 结束当天,进入下一天                      |
| POST  | `/api/final_choice`     | 第 7 天:`destroy_ai` 或 `join_ai`         |

所有 `/api/*` 都需要会话(`@api_login_required`)。

## 国际化(i18n)

前端 + 后端两层,靠同一个 `lang` cookie 驱动。

**前端 — `templates/_i18n.html`:**
- 声明 `window.I18N`,包含 `en` / `zh` 两套字符串表
- `t(key)` 返回当前语言的字符串
- `tFmt(key, vars)` 支持 `{占位符}` 替换
- `applyI18n()` 遍历 DOM,就地替换 `[data-i18n]` / `[data-i18n-html]` /
  `[data-i18n-ph]` / `[data-i18n-title]` 属性
- 隐藏的语言切换按钮自动注入到导航栏
- `I18N.setLang()` 写入 `localStorage`、`lang` cookie,然后
  `location.reload()` 让服务端渲染的文本也刷新

**后端 — `app.py`:**
- `get_lang()` 读 `request.cookies["lang"]`,返回 "en" 或 "zh"
- `tr(bundle)` 接受 `{"en": "…", "zh": "…"}`,按当前语言取值
- 结局、指南、剧情阶段、商品、每日任务、账本描述、API 错误信息
  全部经 `tr()` 输出

**内容 — `database.json` + `database_zh.json`:**
- `load_database(lang)` 加载时合并两份文件。中文文件只需携带
  翻译字段;逻辑键(`next_phase`、`reward`、`moral_delta`)保留在英文源中

## 主题系统

- 默认主题 "terminal":暗绿色终端风,带 CRT 扫描线
- 备选主题 "light":VS 2017 C++ Light 配色
- 选择保存在 `localStorage.game_theme`,绘制前就读取,避免闪烁
- 实现:`<html data-theme="light">` 加一份覆盖样式表,打包在 `_theme.html` 里
- 每个页面都包含这份分片,任意一页切换立刻全站生效

## 结局过场动画

由 `POST /api/final_choice` 成功后触发。浏览器侧:
1. 给 `#ending-overlay` 加 `class="family-{destroy|join}"`
2. **join** 家族:注入 OMNI_CORE 同化日志瀑布,配合 RGB 错位 glitch + 扫描线。
   约 5 秒后,结局标题 + 摘要在红色径向光晕上淡入
3. **destroy** 家族:黑屏 + 单色文字逐行出
   (`> terminal offline`、`> rack-H9 destroyed at 06:14:22`,
   以及一行当前结局专属的结尾)
4. 点 `[ CONTINUE ]` 按钮触发 `location.reload()`,桌面显示凭证卡,
   同时解锁 `/archive/letters`

## 部署

目标:一台 1 vCPU / 512 MB 的 DigitalOcean 实例,Ubuntu 24

```
/var/www/game/           本仓库克隆
/var/www/game/venv/      Python 虚拟环境,含 Flask + gunicorn
/etc/systemd/system/game.service
/etc/nginx/sites-enabled/default   反代到 unix:/var/www/game/game.sock
```

更新流程:

```bash
ssh root@165.227.82.123 \
  "cd /var/www/game && git pull && systemctl restart game.service"
```

gunicorn **不会**热重载 — 每次 pull 后都要重启服务。
