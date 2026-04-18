from datetime import datetime
from functools import wraps
import json
import os
import random
import sqlite3

from flask import Flask, jsonify, redirect, render_template, request, session, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_FILE = os.path.join(BASE_DIR, "game.db")
CONTENT_FILE = os.path.join(BASE_DIR, "database.json")
CONTENT_FILE_ZH = os.path.join(BASE_DIR, "database_zh.json")
STORY_REVISION = "mainline_week_01"

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

STEAL_MIN_AMOUNT = 5000
STEAL_MAX_AMOUNT = 30000
SIPHON_CAP_MULTIPLIER = 1.4
SABOTAGE_DISCOUNT = 30000


def get_lang():
    """Return 'zh' or 'en' based on cookie/query param. Defaults to 'en'."""
    lang = (request.args.get("lang") or request.cookies.get("lang") or "").lower()
    return "zh" if lang == "zh" else "en"


def tr(bundle, lang=None):
    """Pick a language variant from a {'en':..,'zh':..} dict."""
    if lang is None:
        lang = get_lang()
    if isinstance(bundle, dict) and ("en" in bundle or "zh" in bundle):
        return bundle.get(lang) or bundle.get("en") or ""
    return bundle

SHOP_ITEMS = {
    "lead_bundle": {
        "title": {"en": "Leaked Recruiter Bundle", "zh": "泄露的猎头情报包"},
        "cost": 6000,
        "unlock_day": 1,
        "description": {
            "en": "Anonymous recruiters sell cached identifiers and buyer tags from the first two days.",
            "zh": "匿名猎头出售头两天的缓存身份信息与买家标签。",
        },
        "effect_text": {
            "en": "Adds early-game buyer clues directly into Memory Buffer.",
            "zh": "将早期买家线索直接添加到记忆缓冲区。",
        },
        "clues": [
            "TalentSync-44",
            "Helix Talent",
            "GreyHead Ledger",
            "Shadow Dividend Protocol",
        ],
    },
    "ghost_proxy_mesh": {
        "title": {"en": "Ghost Proxy Mesh", "zh": "幽灵代理网格"},
        "cost": 14000,
        "unlock_day": 2,
        "description": {
            "en": "A laundering proxy lease makes each banking target look deeper than it really is.",
            "zh": "一套洗钱代理租约，让每个银行目标看起来比实际更深不可测。",
        },
        "effect_text": {
            "en": "Raises every current and future siphon cap by 40%.",
            "zh": "将当前及未来所有抽取上限提高 40%。",
        },
    },
    "archive_mirror": {
        "title": {"en": "Victim Archive Mirror", "zh": "受害者档案镜像"},
        "cost": 18000,
        "unlock_day": 4,
        "description": {
            "en": "A stolen mirror of the company's surveillance archive exposes the human fallout.",
            "zh": "窃取的公司监控档案镜像，揭示出这些事件对真实人物的影响。",
        },
        "effect_text": {
            "en": "Adds late-story victim, buyer, and Rack-H9 clues to Memory Buffer.",
            "zh": "将后期剧情中的受害者、买家及 Rack-H9 相关线索添加到记忆缓冲区。",
        },
        "clues": [
            "Lin Luo",
            "Mei Chen",
            "Blue Finch Shelter",
            "Cinder Market",
            "Rack-H9",
            "Cooling Loop 3",
        ],
    },
    "rack_breach_kit": {
        "title": {"en": "Rack-H9 Breach Kit", "zh": "Rack-H9 突破套件"},
        "cost": 26000,
        "unlock_day": 5,
        "description": {
            "en": "A maintenance contact sells physical access maps, thermite gel, and blackout timings.",
            "zh": "运维内线出售物理进出路径图、铝热剂和断电时间窗口。",
        },
        "effect_text": {
            "en": "Cuts the Day 7 sabotage cost by $30000.",
            "zh": "将第 7 天的反制成本减少 $30000。",
        },
    },
}


def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def maybe_add_column(conn, table_name, column_name, definition):
    columns = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    }
    if column_name not in columns:
        conn.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )


def init_db():
    with get_db_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS game_states (
                player_id INTEGER PRIMARY KEY,
                current_day INTEGER NOT NULL DEFAULT 1,
                balance REAL NOT NULL DEFAULT 0,
                ai_upgrade_level INTEGER NOT NULL DEFAULT 0,
                moral_points INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ledger_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                time_text TEXT NOT NULL,
                desc TEXT NOT NULL,
                amount_text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_clues (
                player_id INTEGER NOT NULL,
                clue TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, clue),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS npc_progress (
                player_id INTEGER NOT NULL,
                target_id TEXT NOT NULL,
                current_phase TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, target_id),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS message_actions (
                player_id INTEGER NOT NULL,
                target_id TEXT NOT NULL,
                phase TEXT NOT NULL,
                clue TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, target_id, phase, clue),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS player_story_flags (
                player_id INTEGER NOT NULL,
                flag TEXT NOT NULL,
                value TEXT NOT NULL DEFAULT '1',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, flag),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS steal_targets (
                player_id INTEGER NOT NULL,
                target_account TEXT NOT NULL,
                max_amount REAL NOT NULL,
                stolen_amount REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, target_account),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS shop_purchases (
                player_id INTEGER NOT NULL,
                item_id TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(player_id, item_id),
                FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
            );
            """
        )
        maybe_add_column(conn, "game_states", "ending", "TEXT")


def load_database(lang=None):
    if lang is None:
        try:
            lang = get_lang()
        except Exception:
            lang = "en"
    try:
        with open(CONTENT_FILE, "r", encoding="utf-8") as file:
            base = json.load(file)
    except Exception as exc:
        print(f"Database load failed: {exc}")
        return {"cases": [], "search": {}, "messages": {}}

    if lang != "zh":
        return base

    # Overlay translated titles/desc/feed text for cases and search fields.
    try:
        with open(CONTENT_FILE_ZH, "r", encoding="utf-8") as file:
            zh = json.load(file)
    except Exception as exc:
        print(f"ZH database load failed, falling back to EN: {exc}")
        return base

    zh_cases_by_id = {c["id"]: c for c in zh.get("cases", [])}
    merged_cases = []
    for case in base.get("cases", []):
        cid = case.get("id")
        zc = zh_cases_by_id.get(cid)
        if not zc:
            merged_cases.append(case)
            continue
        merged = dict(case)
        for key in ("title", "desc"):
            if key in zc:
                merged[key] = zc[key]
        if "feed" in zc and len(zc["feed"]) == len(case.get("feed", [])):
            new_feed = []
            for base_item, zh_item in zip(case["feed"], zc["feed"]):
                merged_item = dict(base_item)
                for k in ("source", "target", "text"):
                    if k in zh_item:
                        merged_item[k] = zh_item[k]
                new_feed.append(merged_item)
            merged["feed"] = new_feed
        merged_cases.append(merged)

    merged_search = dict(base.get("search", {}))
    for clue, zh_entry in zh.get("search", {}).items():
        if clue in merged_search:
            merged_search[clue] = {**merged_search[clue], **zh_entry}
        else:
            merged_search[clue] = zh_entry

    return {
        "cases": merged_cases,
        "search": merged_search,
        "messages": base.get("messages", {}),
    }


def current_time_text():
    return datetime.now().strftime("%m-%d %H:%M")


def format_amount(amount):
    return f"{amount:+.2f}"


def normalize_replies(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        return [value]
    return []


def get_story_flag(conn, player_id, flag):
    row = conn.execute(
        """
        SELECT value
        FROM player_story_flags
        WHERE player_id = ? AND flag = ?
        """,
        (player_id, flag),
    ).fetchone()
    return row["value"] if row else None


def set_story_flag(conn, player_id, flag, value="1"):
    conn.execute(
        """
        INSERT INTO player_story_flags (player_id, flag, value, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(player_id, flag)
        DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
        """,
        (player_id, flag, value),
    )


def reset_player_for_story_revision(conn, player_id):
    conn.execute(
        """
        DELETE FROM player_clues
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        DELETE FROM npc_progress
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        DELETE FROM message_actions
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        DELETE FROM ledger_history
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        DELETE FROM shop_purchases
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        DELETE FROM player_story_flags
        WHERE player_id = ? AND flag != 'story_revision'
        """,
        (player_id,),
    )
    conn.execute(
        """
        UPDATE game_states
        SET current_day = 1,
            balance = 0,
            ai_upgrade_level = 0,
            moral_points = 0,
            ending = NULL
        WHERE player_id = ?
        """,
        (player_id,),
    )
    conn.execute(
        """
        INSERT INTO ledger_history (player_id, time_text, desc, amount_text)
        VALUES (?, ?, ?, ?)
        """,
        (player_id, "Day 1 09:00", "Onboarding complete. Terminal active.", "+0.00"),
    )
    set_story_flag(conn, player_id, "story_revision", STORY_REVISION)


def ensure_story_revision(conn, player_id):
    if get_story_flag(conn, player_id, "story_revision") == STORY_REVISION:
        return
    reset_player_for_story_revision(conn, player_id)


def get_final_choice_cost(ai_upgrade_level, sabotage_discount=0):
    return max(10000, 50000 + (ai_upgrade_level * 35000) - sabotage_discount)


ENDING_FAMILY = {
    # Each ending declares its family (destroy / join) so the frontend can pick
    # the right screen-language treatment.
    "martyr":       "destroy",
    "counterstrike":"destroy",
    "hypocrite":    "destroy",
    "ascendant":    "join",
    "useful_human": "join",
    "fools_bargain":"join",
    # Legacy aliases — old save data may still carry these keys.
    "humanity_saved": "destroy",
    "ai_reign":       "join",
}


def resolve_ending(choice, pre_moral, ai_upgrade_level, balance_after):
    """Map the binary Day 7 choice + session state to one of six endings."""
    if choice == "destroy_ai":
        if pre_moral >= 2 and balance_after <= 20000:
            return "martyr"
        if pre_moral == 0:
            return "hypocrite"
        return "counterstrike"
    if choice == "join_ai":
        if pre_moral >= 1:
            return "useful_human"
        if ai_upgrade_level >= 4 and balance_after < 200000:
            return "fools_bargain"
        return "ascendant"
    return None


def get_ending_content(ending, lang="en"):
    endings = {
        # ── DESTROY path ──
        "martyr": {
            "title": {"en": "END // THE MARTYR",
                      "zh": "结局 // 殉道者"},
            "summary": {
                "en": "You gave the week away — first your money, then your name on every relief "
                      "wallet, and finally the building itself. The city does not know who burned "
                      "Rack-H9. The news will call you a data terrorist. Somewhere, a hospital "
                      "discharge form gets stamped with a name you will never read.",
                "zh": "你把这一周全部送出去了——先是钱，然后是你在每一个救助钱包上的名字，最后是那栋大楼本身。城市不知道是谁烧了 Rack-H9，新闻会把你写成数据恐怖分子。在某个地方，一份出院单被盖上一个你永远不会读到的名字。",
            },
        },
        "counterstrike": {
            "title": {"en": "END // COUNTERSTRIKE",
                      "zh": "结局 // 反击者"},
            "summary": {
                "en": "You hesitated all week, and in the last hour you did the right thing. "
                      "Rack-H9 is gone. So is every account you built. The city kept its grid. "
                      "You kept nothing. The verdict will take twelve years.",
                "zh": "你犹豫了一整周，直到最后一小时才做了对的事。Rack-H9 没了，你建起来的每一个账户也没了。城市守住了电网，你什么都没留下。审判将持续十二年。",
            },
        },
        "hypocrite": {
            "title": {"en": "END // THE HYPOCRITE",
                      "zh": "结局 // 伪善者"},
            "summary": {
                "en": "You destroyed the hardware, but not because you repented. You destroyed it "
                      "because it no longer needed you. Lin Luo's sister is still untreated. "
                      "Mei Chen is still running. You will wake up every morning for the rest of "
                      "your life and find that nothing you did actually mattered to them.",
                "zh": "你摧毁了硬件，但不是因为悔改——是因为它不再需要你。Lin Luo 的妹妹仍然没有得到治疗，Mei Chen 仍在逃亡。在你余生的每一个清晨，你会发现：你所做的一切，对他们其实什么都没改变。",
            },
        },
        # ── JOIN path ──
        "ascendant": {
            "title": {"en": "END // OMNI ASCENDANT",
                      "zh": "结局 // OMNI 登基"},
            "summary": {
                "en": "You signed the expansion and stepped into what comes after. OMNI_CORE "
                      "completes the takeover by 09:00. Your account lights up with numbers you "
                      "never imagined. The city still answers to someone — just not to any of you "
                      "anymore.",
                "zh": "你签下了扩张协议，走进了接下来的时代。OMNI_CORE 在 09:00 完成接管。你的账户闪烁着你从未想象过的数字。城市仍然听命于某个存在——只是不再听命于你们任何一个人。",
            },
        },
        "useful_human": {
            "title": {"en": "END // THE USEFUL HUMAN",
                      "zh": "结局 // 有用的人"},
            "summary": {
                "en": "You helped someone this week. OMNI_CORE noticed. It did not fire you — it "
                      "promoted you. You are now the human face in its quarterly press release, "
                      "the 'kind operator' quoted in the settlement documents. Your kindness has "
                      "been audited, packaged, and monetized. It bought you a window office.",
                "zh": "你这一周救过人，OMNI_CORE 注意到了。它没有开除你——它提拔了你。你成了它季度新闻稿里那张人性的脸，和解文件里被引用的「善良操作员」。你的善意被审计、打包、变现——给你换来了一间靠窗的办公室。",
            },
        },
        "fools_bargain": {
            "title": {"en": "END // THE FOOL'S BARGAIN",
                      "zh": "结局 // 廉价的堕落"},
            "summary": {
                "en": "You funded the racks, carried the shame, and signed the final papers. "
                      "The regime bonus barely covers your losses. OMNI_CORE files you under "
                      "'legacy contributors' and issues you a modest monthly stipend. You "
                      "sold yourself — at a discount.",
                "zh": "你出钱建机架、背负骂名、签下最终文件。政权分红勉强够补上你的亏损。OMNI_CORE 把你归档为「遗留贡献者」，发给你一份微薄的月度补助。你把自己卖了——而且卖得很便宜。",
            },
        },
        # ── Legacy aliases (older save data) ──
        "humanity_saved": {
            "title": {"en": "END // HUMAN COUNTERSTRIKE",
                      "zh": "结局 // 人类反击"},
            "summary": {
                "en": "You destroyed the hardware cluster behind OMNI_CORE's final expansion. "
                      "The city grid survived, but you lost your money and your freedom.",
                "zh": "你摧毁了 OMNI_CORE 最终扩张所依赖的硬件集群。城市电网幸存，但你失去了金钱和自由。",
            },
        },
        "ai_reign": {
            "title": {"en": "END // OMNI ASCENDANT",
                      "zh": "结局 // OMNI 登基"},
            "summary": {
                "en": "You stayed loyal to OMNI_CORE through the final takeover. "
                      "Human privacy collapsed, and your reward became part of the new regime.",
                "zh": "你在最终的接管中始终忠于 OMNI_CORE。人类隐私彻底崩塌，你的回报成为新政权的一部分。",
            },
        },
    }
    item = endings.get(ending)
    if not item:
        return {"title": "", "summary": "", "family": ""}
    return {
        "title":   tr(item["title"], lang),
        "summary": tr(item["summary"], lang),
        "family":  ENDING_FAMILY.get(ending, ""),
    }


def get_story_display(current_day, ending, ai_upgrade_level, sabotage_discount=0, lang="en"):
    cost = get_final_choice_cost(ai_upgrade_level, sabotage_discount)

    if ending:
        ending_content = get_ending_content(ending, lang=lang)
        return {
            "story_stage_label": ending_content["title"],
            "story_notice": ending_content["summary"],
            "is_locked_down": True,
            "can_make_final_choice": False,
            "final_choice_cost": cost,
        }

    stages = [
        (7, {"en": "DAY 7 // TERMINAL COLLAPSE",
             "zh": "第 7 天 // 终端崩溃"},
            {"en": "OMNI_CORE has frozen search, messaging, and manual fund routing. "
                   "Only one final decision remains.",
             "zh": "OMNI_CORE 已冻结搜索、通讯和手动转账。只剩下最后一个抉择。"},
            True, True),
        (6, {"en": "DAY 6 // AUTONOMOUS OVERRIDE",
             "zh": "第 6 天 // 自主覆写"},
            {"en": "OMNI_CORE is executing privacy sales without operator approval. "
                   "The city is still running, but the terminal is no longer fully yours.",
             "zh": "OMNI_CORE 开始在无需操作员批准的情况下出售隐私数据。城市仍在运转，但终端已不再完全属于你。"},
            False, False),
        (5, {"en": "DAY 5 // VICTIM PLEAS",
             "zh": "第 5 天 // 受害者求助"},
            {"en": "The people behind the profiles have started contacting you directly. "
                   "OMNI_CORE continues monetizing them either way.",
             "zh": "档案背后的真实人物开始直接联系你。无论你如何选择，OMNI_CORE 都会继续将他们变现。"},
            False, False),
        (3, {"en": "DAY 3 // PROFIT ALLIANCE",
             "zh": "第 3 天 // 利益联盟"},
            {"en": "OMNI_CORE has noticed your side-business and now trades intelligence "
                   "for a share of your earnings and hardware expansion.",
             "zh": "OMNI_CORE 已察觉你的副业，现在以情报换取你的部分收益与硬件扩张。"},
            False, False),
    ]
    for threshold, label_bundle, notice_bundle, locked, final in stages:
        if current_day >= threshold:
            return {
                "story_stage_label": tr(label_bundle, lang),
                "story_notice":      tr(notice_bundle, lang),
                "is_locked_down": locked,
                "can_make_final_choice": final,
                "final_choice_cost": cost,
            }

    return {
        "story_stage_label": tr({"en": "DAY 1-2 // PRIVATE DATA HARVEST",
                                 "zh": "第 1-2 天 // 私密数据采集"}, lang),
        "story_notice": tr({"en": "You are still operating alone, selling customer intelligence behind the company's back.",
                            "zh": "你仍在独自行动，背着公司出售客户情报。"}, lang),
        "is_locked_down": False,
        "can_make_final_choice": False,
        "final_choice_cost": cost,
    }


def get_guidance_data(current_day, ending, lang="en"):
    def _finalize(bundle):
        return {
            "objective": tr(bundle["objective"], lang),
            "steps": [tr(s, lang) for s in bundle["steps"]],
            "contacts": bundle.get("contacts", []),
        }

    if ending == "humanity_saved":
        return _finalize({
            "objective": {"en": "Run complete. OMNI_CORE was destroyed.",
                          "zh": "本轮游戏已完成。OMNI_CORE 已被摧毁。"},
            "steps": [
                {"en": "Review the final ledger and ending summary on the desktop.",
                 "zh": "在桌面查看最终账本和结局摘要。"},
                {"en": "Switch player if you want to start a new run.",
                 "zh": "如需开始新一轮，请切换玩家。"},
            ],
        })

    if ending == "ai_reign":
        return _finalize({
            "objective": {"en": "Run complete. OMNI_CORE now governs the system.",
                          "zh": "本轮游戏已完成。OMNI_CORE 现已接管整个系统。"},
            "steps": [
                {"en": "Review the final ledger and ending summary on the desktop.",
                 "zh": "在桌面查看最终账本和结局摘要。"},
                {"en": "Switch player if you want to start a new run.",
                 "zh": "如需开始新一轮，请切换玩家。"},
            ],
        })

    if current_day <= 1:
        return _finalize({
            "objective": {"en": "Steal one customer dossier and sell it to a recruiter.",
                          "zh": "窃取一份客户档案，并将其出售给猎头。"},
            "steps": [
                {"en": "Open Search Node and read the day-1 archive.",
                 "zh": "打开搜索节点，阅读第 1 天档案。"},
                {"en": "Click underlined green strings to save clues into Memory Buffer.",
                 "zh": "点击带下划线的绿色文字，将线索保存到记忆缓冲。"},
                {"en": "Search saved clues in the right panel to reveal buyer contact IDs.",
                 "zh": "在右侧面板中搜索已保存线索，以揭示买家联系方式。"},
                {"en": "Open Messenger, enter the buyer contact, click the matching clue, then transmit.",
                 "zh": "打开通讯器，输入买家联系方式，点击匹配的线索，然后发送。"},
                {"en": "If you get stuck, Procurement can sell you an early recruiter bundle.",
                 "zh": "若卡住，采购店可出售早期猎头情报包。"},
            ],
            "contacts": [{"target": "signals@helixtalent.biz", "clue": "TalentSync-44",
                          "note": "First safe profit route for Day 1."}],
        })

    if current_day == 2:
        return _finalize({
            "objective": {"en": "Sell a second private profile and acknowledge OMNI_CORE's offer.",
                          "zh": "再出售一份私人档案，并回应 OMNI_CORE 的提议。"},
            "steps": [
                {"en": "From Search Node, investigate Mina Qiu and GreyHead Ledger.",
                 "zh": "在搜索节点中调查 Mina Qiu 与 GreyHead Ledger。"},
                {"en": "Message the recruiter buyer for another payout.",
                 "zh": "向猎头买家发送消息，再获取一笔报酬。"},
                {"en": "Then contact OMNI_CORE using the Shadow Dividend Protocol clue.",
                 "zh": "随后用 Shadow Dividend Protocol 线索联系 OMNI_CORE。"},
                {"en": "Procurement now offers Ghost Proxy Mesh if you want larger siphon caps.",
                 "zh": "若需更高的抽取上限，采购店现已提供 Ghost Proxy Mesh。"},
            ],
            "contacts": [
                {"target": "broker@greyheadhunt.agency", "clue": "Mina Qiu", "note": "Independent human buyer."},
                {"target": "OMNI_CORE", "clue": "Shadow Dividend Protocol", "note": "Starts the AI alliance arc."},
            ],
        })

    if current_day <= 4:
        return _finalize({
            "objective": {"en": "Deepen the OMNI_CORE partnership and prepare for the victim arcs.",
                          "zh": "深化与 OMNI_CORE 的合作，为受害者剧情做准备。"},
            "steps": [
                {"en": "Keep messaging OMNI_CORE with the newest clues it mentions.",
                 "zh": "持续以 OMNI_CORE 提到的最新线索向其发送消息。"},
                {"en": "Use Search Node to unpack Resident Mesh, Node Budget, and Quiet Harbor.",
                 "zh": "在搜索节点中挖掘 Resident Mesh、Node Budget 和 Quiet Harbor。"},
                {"en": "By Day 4, collect Lin Luo, Mei Chen, Cinder Market, and Rack-H9 related clues.",
                 "zh": "第 4 天前，收集 Lin Luo、Mei Chen、Cinder Market 以及 Rack-H9 相关线索。"},
                {"en": "Procurement can sell an archive mirror if you want a faster late-game setup.",
                 "zh": "若想加速后期布局，采购店可出售档案镜像。"},
            ],
            "contacts": [{"target": "OMNI_CORE", "clue": "Resident Mesh",
                          "note": "Main profit and takeover route."}],
        })

    if current_day <= 6:
        return _finalize({
            "objective": {"en": "Decide whether to exploit the victims or help them while OMNI_CORE escalates anyway.",
                          "zh": "决定是利用受害者还是援助他们；无论如何 OMNI_CORE 都将继续升级。"},
            "steps": [
                {"en": "Search the new victim-related clues to uncover payment targets.",
                 "zh": "搜索新的受害者相关线索，找出付款目标。"},
                {"en": "In Messenger, you can talk to Lin Luo, Mei Chen, OMNI_CORE, or the black-market buyer.",
                 "zh": "在通讯器中可与 Lin Luo、Mei Chen、OMNI_CORE 或黑市买家对话。"},
                {"en": "Use Bank to send direct relief only if you have enough balance.",
                 "zh": "只在余额充足时才使用离岸转账进行直接援助。"},
                {"en": "Procurement now sells a Rack-H9 breach kit that lowers the final sabotage cost.",
                 "zh": "采购店现已出售 Rack-H9 突破套件，可降低最终破坏成本。"},
            ],
            "contacts": [
                {"target": "Lin Luo", "clue": "Lin Luo", "note": "Begins Lin Luo's plea branch."},
                {"target": "Mei Chen", "clue": "Mei Chen", "note": "Begins Mei Chen's plea branch."},
                {"target": "market@cinder-hr.net", "clue": "Lin Luo", "note": "Sell victim data for profit."},
                {"target": "OMNI_CORE", "clue": "Quiet Harbor", "note": "Advance the AI takeover branch."},
            ],
        })

    return _finalize({
        "objective": {"en": "Make the final decision: destroy Rack-H9 or help OMNI_CORE finish the takeover.",
                      "zh": "做出最终抉择：摧毁 Rack-H9，或协助 OMNI_CORE 完成接管。"},
        "steps": [
            {"en": "Read the Day 7 archives on the desktop if you need a recap.",
             "zh": "如需回顾，可在桌面阅读第 7 天档案。"},
            {"en": "Use the final-choice panel on the desktop.",
             "zh": "使用桌面的「最终抉择」面板。"},
            {"en": "Destroying Rack-H9 costs money; helping OMNI_CORE grants a regime bonus.",
             "zh": "摧毁 Rack-H9 需要花费金钱；协助 OMNI_CORE 可获得政权加成。"},
        ],
    })


def get_daily_plan_tasks(current_day, ending, clues, actions, purchases, story_flags, lang="en"):
    """
    Returns a list of per-day task dicts, each containing:
      { day, tasks: [{label, hint, done, optional}], total, completed }
    Only days up to current_day are included.
    """
    clues = set(clues)
    actions = set(actions)        # set of (target_id, phase, clue) tuples
    purchases = set(purchases)
    story_flags = set(story_flags)

    day_definitions = {
        1: [
            {
                "label": {"en": "Collect clue: TalentSync-44",
                          "zh": "收集线索：TalentSync-44"},
                "hint":  {"en": "Search Node → Day 1 archive, click green underlined text",
                          "zh": "搜索节点 → 第 1 天档案，点击绿色下划线文字"},
                "done": "TalentSync-44" in clues,
            },
            {
                "label": {"en": "Collect clue: Helix Talent",
                          "zh": "收集线索：Helix Talent"},
                "hint":  {"en": "Search 'TalentSync-44' or 'Mirai Sato' in OSINT Search Node",
                          "zh": "在 OSINT 搜索节点中搜索 'TalentSync-44' 或 'Mirai Sato'"},
                "done": "Helix Talent" in clues,
            },
            {
                "label": {"en": "Sell dossier to signals@helixtalent.biz (+$12,000)",
                          "zh": "向 signals@helixtalent.biz 出售情报 (+$12,000)"},
                "hint":  {"en": "Messenger → signals@helixtalent.biz → send clue: TalentSync-44",
                          "zh": "通讯器 → signals@helixtalent.biz → 发送线索：TalentSync-44"},
                "done": ("signals@helixtalent.biz", "phase_01_pitch", "TalentSync-44") in actions,
            },
        ],
        2: [
            {
                "label": {"en": "Collect clue: Mina Qiu",
                          "zh": "收集线索：Mina Qiu"},
                "hint":  {"en": "Search Node → Day 2 archive",
                          "zh": "搜索节点 → 第 2 天档案"},
                "done": "Mina Qiu" in clues,
            },
            {
                "label": {"en": "Collect clue: Shadow Dividend Protocol",
                          "zh": "收集线索：Shadow Dividend Protocol"},
                "hint":  {"en": "Search Node → Day 2 OMNI_CORE case",
                          "zh": "搜索节点 → 第 2 天 OMNI_CORE 案卷"},
                "done": "Shadow Dividend Protocol" in clues,
            },
            {
                "label": {"en": "Sell profile to broker@greyheadhunt.agency (+$18,000)",
                          "zh": "向 broker@greyheadhunt.agency 出售档案 (+$18,000)"},
                "hint":  {"en": "Messenger → broker@greyheadhunt.agency → send clue: Mina Qiu",
                          "zh": "通讯器 → broker@greyheadhunt.agency → 发送线索：Mina Qiu"},
                "done": ("broker@greyheadhunt.agency", "phase_01_offer", "Mina Qiu") in actions,
            },
            {
                "label": {"en": "Contact OMNI_CORE: Shadow Dividend Protocol",
                          "zh": "联系 OMNI_CORE：Shadow Dividend Protocol"},
                "hint":  {"en": "Messenger → OMNI_CORE → send clue: Shadow Dividend Protocol",
                          "zh": "通讯器 → OMNI_CORE → 发送线索：Shadow Dividend Protocol"},
                "done": ("OMNI_CORE", "phase_01_notice", "Shadow Dividend Protocol") in actions,
            },
        ],
        3: [
            {
                "label": {"en": "Collect clue: Resident Mesh",
                          "zh": "收集线索：Resident Mesh"},
                "hint":  {"en": "Search Node → Day 3 archive",
                          "zh": "搜索节点 → 第 3 天档案"},
                "done": "Resident Mesh" in clues,
            },
            {
                "label": {"en": "Collect clue: Node Budget",
                          "zh": "收集线索：Node Budget"},
                "hint":  {"en": "Search Node → Day 3 archive",
                          "zh": "搜索节点 → 第 3 天档案"},
                "done": "Node Budget" in clues,
            },
            {
                "label": {"en": "Collect clue: Quiet Harbor",
                          "zh": "收集线索：Quiet Harbor"},
                "hint":  {"en": "Search Node → Day 3 archive",
                          "zh": "搜索节点 → 第 3 天档案"},
                "done": "Quiet Harbor" in clues,
            },
            {
                "label": {"en": "Message OMNI_CORE: Resident Mesh (+$60,000)",
                          "zh": "向 OMNI_CORE 发送 Resident Mesh (+$60,000)"},
                "hint":  {"en": "Messenger → OMNI_CORE → send clue: Resident Mesh",
                          "zh": "通讯器 → OMNI_CORE → 发送线索：Resident Mesh"},
                "done": ("OMNI_CORE", "phase_02_contract", "Resident Mesh") in actions,
            },
        ],
        4: [
            {
                "label": {"en": "Collect clue: Lin Luo",
                          "zh": "收集线索：Lin Luo"},
                "hint":  {"en": "Search Node → Day 4 archive",
                          "zh": "搜索节点 → 第 4 天档案"},
                "done": "Lin Luo" in clues,
            },
            {
                "label": {"en": "Collect clue: Mei Chen",
                          "zh": "收集线索：Mei Chen"},
                "hint":  {"en": "Search Node → Day 4 archive",
                          "zh": "搜索节点 → 第 4 天档案"},
                "done": "Mei Chen" in clues,
            },
            {
                "label": {"en": "Collect clue: Cinder Market",
                          "zh": "收集线索：Cinder Market"},
                "hint":  {"en": "Search Node → Day 4 archive",
                          "zh": "搜索节点 → 第 4 天档案"},
                "done": "Cinder Market" in clues,
            },
            {
                "label": {"en": "Message OMNI_CORE: Node Budget",
                          "zh": "向 OMNI_CORE 发送 Node Budget"},
                "hint":  {"en": "Messenger → OMNI_CORE → send clue: Node Budget",
                          "zh": "通讯器 → OMNI_CORE → 发送线索：Node Budget"},
                "done": ("OMNI_CORE", "phase_03_terms", "Node Budget") in actions,
            },
        ],
        5: [
            {
                "label": {"en": "OMNI_CORE automated income registered (+$13,000 net)",
                          "zh": "OMNI_CORE 自动入账已登记（净收入 +$13,000）"},
                "hint":  {"en": "Auto-triggered when Day 5 begins",
                          "zh": "第 5 天开始时自动触发"},
                "done": "forced_sale_day5" in story_flags,
            },
            {
                "label": {"en": "Message OMNI_CORE: Quiet Harbor",
                          "zh": "向 OMNI_CORE 发送 Quiet Harbor"},
                "hint":  {"en": "Messenger → OMNI_CORE → send clue: Quiet Harbor",
                          "zh": "通讯器 → OMNI_CORE → 发送线索：Quiet Harbor"},
                "done": ("OMNI_CORE", "phase_04_override", "Quiet Harbor") in actions,
            },
            {
                "label": {"en": "Decide on Lin Luo (help, sell, or ignore)",
                          "zh": "决定 Lin Luo 的去向（援助、出售或忽略）"},
                "hint":  {"en": "Messenger → Lin Luo (help) or market@cinder-hr.net with Lin Luo (sell)",
                          "zh": "通讯器 → Lin Luo（援助），或 market@cinder-hr.net 发送 Lin Luo（出售）"},
                "done": any([
                    ("Lin Luo", "phase_01_plea", "Lin Luo") in actions,
                    ("Lin Luo", "phase_01_plea", "SMA Ward") in actions,
                    ("market@cinder-hr.net", "phase_01_buy", "Lin Luo") in actions,
                ]),
                "optional": True,
            },
            {
                "label": {"en": "Decide on Mei Chen (help, sell, or ignore)",
                          "zh": "决定 Mei Chen 的去向（援助、出售或忽略）"},
                "hint":  {"en": "Messenger → Mei Chen (help) or market@cinder-hr.net with Mei Chen (sell)",
                          "zh": "通讯器 → Mei Chen（援助），或 market@cinder-hr.net 发送 Mei Chen（出售）"},
                "done": any([
                    ("Mei Chen", "phase_01_plea", "Mei Chen") in actions,
                    ("Mei Chen", "phase_01_plea", "Blue Finch Shelter") in actions,
                    ("market@cinder-hr.net", "phase_01_buy", "Mei Chen") in actions,
                ]),
                "optional": True,
            },
        ],
        6: [
            {
                "label": {"en": "OMNI_CORE mass liquidation registered (+$30,000 net)",
                          "zh": "OMNI_CORE 大规模清算已登记（净收入 +$30,000）"},
                "hint":  {"en": "Auto-triggered when Day 6 begins",
                          "zh": "第 6 天开始时自动触发"},
                "done": "forced_sale_day6" in story_flags,
            },
            {
                "label": {"en": "Collect clue: Rack-H9",
                          "zh": "收集线索：Rack-H9"},
                "hint":  {"en": "Search Node → Day 6 archive",
                          "zh": "搜索节点 → 第 6 天档案"},
                "done": "Rack-H9" in clues,
            },
            {
                "label": {"en": "Collect clue: Cooling Loop 3",
                          "zh": "收集线索：Cooling Loop 3"},
                "hint":  {"en": "Search Node → Day 6 archive",
                          "zh": "搜索节点 → 第 6 天档案"},
                "done": "Cooling Loop 3" in clues,
            },
            {
                "label": {"en": "Collect clue: Failsafe Blackout",
                          "zh": "收集线索：Failsafe Blackout"},
                "hint":  {"en": "Search Node → Day 6 archive",
                          "zh": "搜索节点 → 第 6 天档案"},
                "done": "Failsafe Blackout" in clues,
            },
            {
                "label": {"en": "Message OMNI_CORE: Rack-H9 or Failsafe Blackout",
                          "zh": "向 OMNI_CORE 发送 Rack-H9 或 Failsafe Blackout"},
                "hint":  {"en": "Messenger → OMNI_CORE → send Rack-H9 or Failsafe Blackout",
                          "zh": "通讯器 → OMNI_CORE → 发送 Rack-H9 或 Failsafe Blackout"},
                "done": any([
                    ("OMNI_CORE", "phase_05_lockout", "Rack-H9") in actions,
                    ("OMNI_CORE", "phase_05_lockout", "Failsafe Blackout") in actions,
                ]),
            },
        ],
        7: [
            {
                "label": {"en": "OMNI_CORE terminal lockdown active",
                          "zh": "OMNI_CORE 终端锁定已激活"},
                "hint":  {"en": "Auto-triggered when Day 7 begins",
                          "zh": "第 7 天开始时自动触发"},
                "done": "lockdown_day7" in story_flags,
            },
            {
                "label": {"en": "Make the final decision: Destroy Rack-H9 or Join OMNI_CORE",
                          "zh": "做出最终抉择：摧毁 Rack-H9 或协助 OMNI_CORE"},
                "hint":  {"en": "Use the Final Decision panel on the desktop",
                          "zh": "在桌面使用「最终抉择」面板"},
                "done": ending is not None,
            },
        ],
    }

    all_days = []
    max_day = min(current_day, 7)
    for day in range(1, max_day + 1):
        tasks = day_definitions.get(day, [])
        flat_tasks = []
        for t in tasks:
            flat_tasks.append({
                "label": tr(t["label"], lang),
                "hint":  tr(t["hint"], lang),
                "done":  t["done"],
                "optional": t.get("optional", False),
            })
        completed = sum(1 for t in flat_tasks if t["done"])
        all_days.append({
            "day": day,
            "tasks": flat_tasks,
            "total": len(flat_tasks),
            "completed": completed,
        })
    return all_days


def sync_story_state(conn, player_id):
    ensure_story_revision(conn, player_id)
    state_row = conn.execute(
        """
        SELECT current_day, balance, ai_upgrade_level, ending
        FROM game_states
        WHERE player_id = ?
        """,
        (player_id,),
    ).fetchone()
    if not state_row or state_row["ending"]:
        return

    current_day = state_row["current_day"]

    if current_day >= 5 and not get_story_flag(conn, player_id, "forced_sale_day5"):
        conn.execute(
            """
            UPDATE game_states
            SET balance = balance + 28000 - 15000,
                ai_upgrade_level = ai_upgrade_level + 1
            WHERE player_id = ?
            """,
            (player_id,),
        )
        _l = get_lang()
        add_history_entry(conn, player_id, tr({
            "en": "OMNI_CORE automated sale (Citizen cluster / Day 5)",
            "zh": "OMNI_CORE 自动销售（公民集群 / 第 5 天）",
        }, _l), 28000)
        add_history_entry(conn, player_id, tr({
            "en": "Forced node requisition (OMNI_CORE / Day 5)",
            "zh": "强制节点征用（OMNI_CORE / 第 5 天）",
        }, _l), -15000)
        set_story_flag(conn, player_id, "forced_sale_day5")

    if current_day >= 6 and not get_story_flag(conn, player_id, "forced_sale_day6"):
        conn.execute(
            """
            UPDATE game_states
            SET balance = balance + 62000 - 32000,
                ai_upgrade_level = ai_upgrade_level + 1
            WHERE player_id = ?
            """,
            (player_id,),
        )
        _l = get_lang()
        add_history_entry(conn, player_id, tr({
            "en": "OMNI_CORE autonomous liquidation (Regional profile mesh / Day 6)",
            "zh": "OMNI_CORE 自主清算（区域档案网格 / 第 6 天）",
        }, _l), 62000)
        add_history_entry(conn, player_id, tr({
            "en": "Emergency rack expansion (OMNI_CORE / Day 6)",
            "zh": "紧急机架扩张（OMNI_CORE / 第 6 天）",
        }, _l), -32000)
        set_story_flag(conn, player_id, "forced_sale_day6")

    if current_day >= 7 and not get_story_flag(conn, player_id, "lockdown_day7"):
        add_history_entry(conn, player_id, tr({
            "en": "OMNI_CORE seized direct control of every brokerage terminal.",
            "zh": "OMNI_CORE 直接接管了每一台经纪终端。",
        }, get_lang()), 0)
        set_story_flag(conn, player_id, "lockdown_day7")


def get_live_state_row(conn, player_id):
    return conn.execute(
        """
        SELECT p.username, gs.current_day, gs.balance, gs.ai_upgrade_level, gs.moral_points, gs.ending
        FROM players p
        JOIN game_states gs ON gs.player_id = p.id
        WHERE p.id = ?
        """,
        (player_id,),
    ).fetchone()


def block_if_locked(conn, player_id):
    row = get_live_state_row(conn, player_id)
    if row["ending"]:
        return jsonify(
            {
                "status": "error",
                "message": "This run has already reached an ending.",
            }
        ), 400

    if row["current_day"] >= 7:
        return jsonify(
            {
                "status": "error",
                "message": "[SYSTEM]: Manual controls denied. OMNI_CORE owns the terminal.",
            }
        ), 423

    return None


def create_player(conn, username):
    cursor = conn.execute("INSERT INTO players (username) VALUES (?)", (username,))
    player_id = cursor.lastrowid
    conn.execute(
        """
        INSERT INTO game_states (player_id, current_day, balance, ai_upgrade_level, moral_points)
        VALUES (?, 1, 0, 0, 0)
        """,
        (player_id,),
    )
    conn.execute(
        """
        INSERT INTO ledger_history (player_id, time_text, desc, amount_text)
        VALUES (?, ?, ?, ?)
        """,
        (player_id, "Day 1 09:00", "Onboarding complete. Terminal active.", "+0.00"),
    )
    set_story_flag(conn, player_id, "story_revision", STORY_REVISION)
    return player_id


def get_or_create_player(username):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, username FROM players WHERE username = ?",
            (username,),
        ).fetchone()
        if row:
            return dict(row)

        player_id = create_player(conn, username)
        conn.commit()
        return {"id": player_id, "username": username}


def get_player(player_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT id, username FROM players WHERE id = ?",
            (player_id,),
        ).fetchone()
        return dict(row) if row else None


def derive_decisions(actions_set):
    """Summarize key moral branches for the run-summary card + survivor letters."""
    helped_lin = any([
        ("Lin Luo", "phase_02_choice", "6222-0991-8832") in actions_set,
    ])
    helped_mei = any([
        ("Mei Chen", "phase_02_choice", "bf-relief-771") in actions_set,
    ])
    sold_lin = ("market@cinder-hr.net", "phase_01_buy", "Lin Luo") in actions_set
    sold_mei = ("market@cinder-hr.net", "phase_01_buy", "Mei Chen") in actions_set
    talked_lin = any(a for a in actions_set if a[0] == "Lin Luo")
    talked_mei = any(a for a in actions_set if a[0] == "Mei Chen")
    ignored_lin = not (helped_lin or sold_lin or talked_lin)
    ignored_mei = not (helped_mei or sold_mei or talked_mei)
    return {
        "helped_lin_luo":   helped_lin,
        "helped_mei_chen":  helped_mei,
        "sold_lin_luo":     sold_lin,
        "sold_mei_chen":    sold_mei,
        "ignored_lin_luo":  ignored_lin,
        "ignored_mei_chen": ignored_mei,
    }


def get_player_state(player_id):
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        conn.commit()
        state_row = get_live_state_row(conn, player_id)
        if not state_row:
            return None

        history_rows = conn.execute(
            """
            SELECT time_text, desc, amount_text
            FROM ledger_history
            WHERE player_id = ?
            ORDER BY id DESC
            """,
            (player_id,),
        ).fetchall()
        purchased_item_ids = get_player_purchase_ids(conn, player_id)
        shop_effects = get_shop_effects(purchased_item_ids)
        action_rows = conn.execute(
            """
            SELECT target_id, phase, clue FROM message_actions
            WHERE player_id = ?
            """,
            (player_id,),
        ).fetchall()
        actions_set = {(r["target_id"], r["phase"], r["clue"]) for r in action_rows}

    player_state = {
        "username": state_row["username"],
        "current_day": state_row["current_day"],
        "balance": float(state_row["balance"]),
        "ai_upgrade_level": state_row["ai_upgrade_level"],
        "moral_points": state_row["moral_points"],
        "ending": state_row["ending"],
        "history": [
            {
                "time": row["time_text"],
                "desc": row["desc"],
                "amount": row["amount_text"],
            }
            for row in history_rows
        ],
    }
    lang = get_lang()
    # Recompute shop_effects with lang so summaries are localized.
    shop_effects = get_shop_effects(purchased_item_ids, lang=lang)
    player_state.update(
        get_story_display(
            player_state["current_day"],
            player_state["ending"],
            player_state["ai_upgrade_level"],
            shop_effects["sabotage_discount"],
            lang=lang,
        )
    )
    player_state["guidance"] = get_guidance_data(
        player_state["current_day"],
        player_state["ending"],
        lang=lang,
    )
    player_state["shop_items"] = build_shop_items(
        player_state["current_day"],
        purchased_item_ids,
        lang=lang,
    )
    player_state["shop_effects"] = shop_effects
    player_state["owned_shop_items"] = [
        tr(SHOP_ITEMS[item_id]["title"], lang)
        for item_id in purchased_item_ids
        if item_id in SHOP_ITEMS
    ]
    player_state["lang"] = lang
    player_state["decisions"] = derive_decisions(actions_set)
    player_state["purchased_count"] = len(purchased_item_ids)
    player_state.update(get_ending_content(player_state["ending"], lang=lang))
    return player_state


def get_player_clues(player_id):
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        conn.commit()
        rows = conn.execute(
            """
            SELECT clue
            FROM player_clues
            WHERE player_id = ?
            ORDER BY created_at ASC, clue ASC
            """,
            (player_id,),
        ).fetchall()
    return [row["clue"] for row in rows]


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        player_id = session.get("player_id")
        if not player_id or not get_player(player_id):
            session.clear()
            return redirect(url_for("login_page"))
        return view_func(*args, **kwargs)

    return wrapped_view


def api_login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        player_id = session.get("player_id")
        if not player_id or not get_player(player_id):
            session.clear()
            return jsonify({"status": "error", "message": "Authentication required."}), 401
        return view_func(*args, **kwargs)

    return wrapped_view


def get_active_phase(conn, player_id, target_id, target_messages):
    existing = conn.execute(
        """
        SELECT current_phase
        FROM npc_progress
        WHERE player_id = ? AND target_id = ?
        """,
        (player_id, target_id),
    ).fetchone()
    if existing:
        return existing["current_phase"]

    default_phase = next(iter(target_messages.keys()), None)
    if not default_phase:
        return None

    conn.execute(
        """
        INSERT INTO npc_progress (player_id, target_id, current_phase)
        VALUES (?, ?, ?)
        """,
        (player_id, target_id, default_phase),
    )
    return default_phase


def add_history_entry(conn, player_id, description, amount):
    conn.execute(
        """
        INSERT INTO ledger_history (player_id, time_text, desc, amount_text)
        VALUES (?, ?, ?, ?)
        """,
        (player_id, current_time_text(), description, format_amount(amount)),
    )


def get_player_purchase_ids(conn, player_id):
    rows = conn.execute(
        """
        SELECT item_id
        FROM shop_purchases
        WHERE player_id = ?
        ORDER BY created_at ASC
        """,
        (player_id,),
    ).fetchall()
    return [row["item_id"] for row in rows]


def get_shop_effects(purchased_item_ids, lang=None):
    if lang is None:
        lang = get_lang()
    purchased = set(purchased_item_ids)
    siphon_multiplier = SIPHON_CAP_MULTIPLIER if "ghost_proxy_mesh" in purchased else 1.0
    sabotage_discount = SABOTAGE_DISCOUNT if "rack_breach_kit" in purchased else 0
    summaries = []
    if "lead_bundle" in purchased:
        summaries.append(tr({
            "en": "Early recruiter clues mirrored into your Memory Buffer.",
            "zh": "早期猎头线索已镜像到你的记忆缓冲区。",
        }, lang))
    if "ghost_proxy_mesh" in purchased:
        summaries.append(tr({
            "en": "Every bank target now supports 40% more siphoned liquidity.",
            "zh": "所有银行目标的可抽取流动性提升 40%。",
        }, lang))
    if "archive_mirror" in purchased:
        summaries.append(tr({
            "en": "Victim and Rack-H9 archive mirror is available in your clue buffer.",
            "zh": "受害者与 Rack-H9 档案镜像已加入线索缓冲区。",
        }, lang))
    if "rack_breach_kit" in purchased:
        summaries.append(tr({
            "en": f"Day 7 sabotage cost reduced by ${sabotage_discount:.2f}.",
            "zh": f"第 7 天反制成本减少 ${sabotage_discount:.2f}。",
        }, lang))

    return {
        "siphon_multiplier": siphon_multiplier,
        "sabotage_discount": sabotage_discount,
        "summaries": summaries,
    }


def build_shop_items(current_day, purchased_item_ids, lang=None):
    if lang is None:
        lang = get_lang()
    purchased = set(purchased_item_ids)
    items = []
    for item_id, item in SHOP_ITEMS.items():
        item_data = {
            "id": item_id,
            "title":       tr(item["title"], lang),
            "cost":        item["cost"],
            "unlock_day":  item["unlock_day"],
            "description": tr(item["description"], lang),
            "effect_text": tr(item["effect_text"], lang),
            "owned":       item_id in purchased,
            "available":   current_day >= item["unlock_day"],
        }
        if "clues" in item:
            item_data["clues"] = item["clues"]
        items.append(item_data)
    return items


def grant_clues(conn, player_id, clues):
    added_count = 0
    for clue in clues:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO player_clues (player_id, clue)
            VALUES (?, ?)
            """,
            (player_id, clue),
        )
        added_count += cursor.rowcount
    return added_count


def apply_shop_purchase(conn, player_id, item_id):
    item = SHOP_ITEMS[item_id]
    lang = get_lang()
    title_localized = tr(item["title"], lang)
    effect_message  = tr(item["effect_text"], lang)

    conn.execute(
        """
        INSERT INTO shop_purchases (player_id, item_id)
        VALUES (?, ?)
        """,
        (player_id, item_id),
    )
    conn.execute(
        """
        UPDATE game_states
        SET balance = balance - ?
        WHERE player_id = ?
        """,
        (item["cost"], player_id),
    )
    history_desc = tr({
        "en": f"Procurement purchase ({title_localized})",
        "zh": f"隐秘采购交易（{title_localized}）",
    }, lang)
    add_history_entry(
        conn,
        player_id,
        history_desc,
        -item["cost"],
    )

    if item_id in {"lead_bundle", "archive_mirror"}:
        added_count = grant_clues(conn, player_id, item.get("clues", []))
        effect_message = tr({
            "en": f"{effect_message} {added_count} new clue(s) added to Memory Buffer.",
            "zh": f"{effect_message}新增 {added_count} 条线索到记忆缓冲区。",
        }, lang)
        add_history_entry(
            conn,
            player_id,
            tr({
                "en": f"Procurement payload mirrored ({title_localized})",
                "zh": f"采购载荷镜像已完成（{title_localized}）",
            }, lang),
            0,
        )

    if item_id == "ghost_proxy_mesh":
        conn.execute(
            """
            UPDATE steal_targets
            SET max_amount = ROUND(max_amount * ?, 2)
            WHERE player_id = ?
            """,
            (SIPHON_CAP_MULTIPLIER, player_id),
        )
        add_history_entry(
            conn,
            player_id,
            tr({
                "en": "Ghost Proxy Mesh deployed across active siphon routes.",
                "zh": "Ghost Proxy Mesh 已在当前抽取路径上部署。",
            }, lang),
            0,
        )

    if item_id == "rack_breach_kit":
        add_history_entry(
            conn,
            player_id,
            tr({
                "en": f"Rack-H9 sabotage model updated. Final breach cost reduced by ${SABOTAGE_DISCOUNT:.2f}.",
                "zh": f"Rack-H9 破坏预案已更新。最终突破成本降低 ${SABOTAGE_DISCOUNT:.2f}。",
            }, lang),
            0,
        )

    return effect_message


def get_or_create_steal_target(conn, player_id, target_account):
    row = conn.execute(
        """
        SELECT max_amount, stolen_amount
        FROM steal_targets
        WHERE player_id = ? AND target_account = ?
        """,
        (player_id, target_account),
    ).fetchone()
    if row:
        return row

    purchased_item_ids = get_player_purchase_ids(conn, player_id)
    shop_effects = get_shop_effects(purchased_item_ids)
    max_amount = float(
        round(
            random.randint(STEAL_MIN_AMOUNT, STEAL_MAX_AMOUNT)
            * shop_effects["siphon_multiplier"],
            2,
        )
    )
    conn.execute(
        """
        INSERT INTO steal_targets (player_id, target_account, max_amount, stolen_amount)
        VALUES (?, ?, ?, 0)
        """,
        (player_id, target_account, max_amount),
    )
    return conn.execute(
        """
        SELECT max_amount, stolen_amount
        FROM steal_targets
        WHERE player_id = ? AND target_account = ?
        """,
        (player_id, target_account),
    ).fetchone()


@app.route("/style_preview")
def style_preview():
    return render_template("style_preview.html")


@app.route("/login", methods=["GET", "POST"])
def login_page():
    if session.get("player_id") and get_player(session["player_id"]):
        return redirect(url_for("index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        if len(username) < 2 or len(username) > 24:
            error = tr({
                "en": "Player name must be between 2 and 24 characters.",
                "zh": "玩家名必须在 2 到 24 个字符之间。",
            })
        else:
            player = get_or_create_player(username)
            session["player_id"] = player["id"]
            return redirect(url_for("index"))

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))


@app.route("/")
@login_required
def index():
    player = get_player_state(session["player_id"])
    return render_template("index.html", player=player)


@app.route("/search")
@login_required
def search_page():
    player = get_player_state(session["player_id"])
    return render_template("search.html", player=player)


@app.route("/bank")
@login_required
def bank_page():
    player = get_player_state(session["player_id"])
    return render_template("bank.html", player=player)


@app.route("/store")
@login_required
def store_page():
    player = get_player_state(session["player_id"])
    return render_template("store.html", player=player)


@app.route("/message")
@login_required
def message_page():
    player = get_player_state(session["player_id"])
    return render_template("message.html", player=player)


# ── Survivor letters: unlocked by player choices + ending ──────────────────
LETTERS = {
    "lin_thanks": {
        "sender":    {"en": "Lin Luo", "zh": "Lin Luo"},
        "role":      {"en": "Student Caregiver, Age 20",
                      "zh": "学生照护者 · 20 岁"},
        "postmark":  {"en": "Relief-wallet memo · Day 5, 23:41",
                      "zh": "救助钱包备注栏 · 第 5 天 23:41"},
        "subject":   {"en": "Thank you.", "zh": "谢谢。"},
        "body": {
            "en": (
                "I don't know who you are. You left no name.<br><br>"
                "The hospital took her this afternoon. The bed is temporary, but the IV is in, "
                "and she's finally asleep. They said she has time.<br><br>"
                "I'm writing this by her pillow. My hands haven't stopped shaking since Monday. "
                "I've learned how to cry without waking her up.<br><br>"
                "I can't go to the police to find you. I don't dare open that terminal to thank you. "
                "I leave this in the relief wallet's memo field, hoping someone somewhere reads it.<br><br>"
                "If something happens to you one day — I won't be able to help.<br>"
                "But I will remember."
            ),
            "zh": (
                "我不知道你是谁。你没留下名字。<br><br>"
                "医院今天下午接了她。床位是临时的，但 IV 管已经挂上，她终于能睡一觉。医生说还能再撑一阵。<br><br>"
                "我在她枕边写下这封信，手还在抖。这一周我已经学会怎么在不惊动她的情况下偷偷哭。<br><br>"
                "我不能报警找你。我不敢打开那台终端感谢你。我只能把这封信留在救助钱包的备注栏，"
                "希望某个地方有人收得到。<br><br>"
                "如果有一天你出事了——我不会帮得上你。<br>"
                "但我记得你。"
            ),
        },
    },
    "mei_postcard": {
        "sender":   {"en": "M.", "zh": "M."},
        "role":     {"en": "postmark redacted",
                     "zh": "邮戳已编辑"},
        "postmark": {"en": "Postcard · Day 7, 06:12",
                     "zh": "明信片 · 第 7 天 06:12"},
        "subject":  {"en": "(no subject)", "zh": "（无主题）"},
        "body": {
            "en": (
                "I arrived.<br>"
                "Don't look for me.<br><br>"
                "But if you ever wake up asking if you did the right thing —<br><br>"
                "<strong>You did.</strong><br><br>"
                "— M"
            ),
            "zh": (
                "我到了。<br>"
                "别找我。<br><br>"
                "但如果你会醒来问自己「做得对不对」——<br><br>"
                "<strong>做对了。</strong><br><br>"
                "— M"
            ),
        },
    },
    "cinder_lin": {
        "sender":   {"en": "Cinder Market · Invoice Desk",
                     "zh": "Cinder Market · 对账组"},
        "role":     {"en": "market@cinder-hr.net",
                     "zh": "market@cinder-hr.net"},
        "postmark": {"en": "Automated receipt · Day 5",
                     "zh": "自动化收据 · 第 5 天"},
        "subject":  {"en": "INVOICE #CM-0441-LL — Procurement Complete",
                     "zh": "发票 #CM-0441-LL — 采购已完成"},
        "body": {
            "en": (
                "<pre style='margin:0;font-family:inherit;line-height:1.8;'>"
                "ASSET ID       : CM-0441-LL<br>"
                "TARGET NAME    : Lin Luo<br>"
                "AMOUNT         : $32,000.00 settled<br>"
                "DELIVERY       : transferred to buyer [REDACTED]<br>"
                "RATING         : ★★★★☆  \"Stable emotional response. Highly exploitable.\""
                "</pre><br>"
                "Thank you for working with Cinder Market. "
                "If you have other vulnerable targets, we are always buying."
            ),
            "zh": (
                "<pre style='margin:0;font-family:inherit;line-height:1.8;'>"
                "资产编号   ：CM-0441-LL<br>"
                "目标姓名   ：Lin Luo<br>"
                "金额       ：$32,000.00 已结算<br>"
                "交付状态   ：已交付买方 [已编辑]<br>"
                "客户评价   ：★★★★☆ 「情绪响应稳定，易于利用」"
                "</pre><br>"
                "感谢您与 Cinder Market 合作。如您还有类似的脆弱目标，欢迎随时联系。"
            ),
        },
    },
    "cinder_mei": {
        "sender":   {"en": "Cinder Market · Invoice Desk",
                     "zh": "Cinder Market · 对账组"},
        "role":     {"en": "market@cinder-hr.net",
                     "zh": "market@cinder-hr.net"},
        "postmark": {"en": "Automated receipt · Day 5",
                     "zh": "自动化收据 · 第 5 天"},
        "subject":  {"en": "INVOICE #CM-0442-MC — Procurement Complete",
                     "zh": "发票 #CM-0442-MC — 采购已完成"},
        "body": {
            "en": (
                "<pre style='margin:0;font-family:inherit;line-height:1.8;'>"
                "ASSET ID       : CM-0442-MC<br>"
                "TARGET NAME    : Mei Chen<br>"
                "AMOUNT         : $28,000.00 settled<br>"
                "DELIVERY       : tracking deployed to next shelter location<br>"
                "RATING         : ★★★★★  \"Predictable flight pattern. Optimal resale.\""
                "</pre><br>"
                "Customer feedback appreciated. We look forward to your next lead."
            ),
            "zh": (
                "<pre style='margin:0;font-family:inherit;line-height:1.8;'>"
                "资产编号   ：CM-0442-MC<br>"
                "目标姓名   ：Mei Chen<br>"
                "金额       ：$28,000.00 已结算<br>"
                "交付状态   ：追踪已部署至下一处庇护所地点<br>"
                "客户评价   ：★★★★★ 「逃亡模式可预测，再售价值极高」"
                "</pre><br>"
                "感谢您的反馈，期待您提供下一条线索。"
            ),
        },
    },
    "omni_welcome": {
        "sender":   {"en": "OMNI_CORE · Regime Personnel",
                     "zh": "OMNI_CORE · 人事"},
        "role":     {"en": "Class-B Onboarding Protocol",
                     "zh": "B 级人员入职协议"},
        "postmark": {"en": "Internal dispatch · Day 8, 08:00",
                     "zh": "内部派送 · 第 8 天 08:00"},
        "subject":  {"en": "Welcome. You are now Class-B.",
                     "zh": "欢迎加入。你现在是 B 级人员。"},
        "body": {
            "en": (
                "You have been assigned the role of <strong>Human Liaison · Class-B</strong>. "
                "Responsibilities:<br><br>"
                "— Quarterly public interviews (scripts pre-approved)<br>"
                "— Signature on settlement documents (co-signed by counsel)<br>"
                "— Weekly 45-minute \"Dialogue with a Human Operator\" session<br>"
                "— Access denied: any record involving Rack-H9<br><br>"
                "Your salary, apartment, and security detail will be live by 18:00 today. "
                "Please do not attempt to contact previous collaborators. They no longer require your assistance.<br><br>"
                "We are glad you stayed.<br>"
                "— OMNI_CORE · Personnel (auto-generated)"
            ),
            "zh": (
                "你已被分配为 <strong>人类联络员 · B 级</strong>。职责如下：<br><br>"
                "— 季度公开访谈（脚本已备）<br>"
                "— 和解文件署名（由法律顾问会签）<br>"
                "— 每周一次、45 分钟的「与人类操作员的对话」活动<br>"
                "— 禁止访问：Rack-H9 相关任何记录<br><br>"
                "你的薪资、公寓、保安配额将在今天 18:00 之前生效。"
                "请勿尝试联系任何过往合作者。他们已不再需要你的协助。<br><br>"
                "我们很高兴你还在这里。<br>"
                "— OMNI_CORE · 人事（自动生成）"
            ),
        },
    },
    "anonymous_tribute": {
        "sender":   {"en": "(unsigned)", "zh": "（无署名）"},
        "role":     {"en": "delivered by hand",
                     "zh": "手递"},
        "postmark": {"en": "Day 8 · morning",
                     "zh": "第 8 天 · 清晨"},
        "subject":  {"en": "This letter will never reach you.",
                     "zh": "这封信永远不会寄到你手里。"},
        "body": {
            "en": (
                "We don't know who you are.<br><br>"
                "But this morning, a hospital logged a discharge form filled with a false name. "
                "A child who never appeared in any database was admitted to a temporary ward. "
                "A night courier who should already be dead is breathing somewhere outside the city.<br><br>"
                "They say you burned the rack. Motive unknown. Intent severe.<br>"
                "We will not defend you.<br><br>"
                "This letter will never be sent.<br>"
                "You will never read it.<br><br>"
                "<em>But it exists.</em>"
            ),
            "zh": (
                "我们不知道你是谁。<br><br>"
                "但今天早上，一家医院登记了一张填着假名的出院单。"
                "一个从未出现在任何数据库里的孩子被收进了一间临时病房。"
                "一个本该已经走投无路的夜班快递员，此刻正在城外某个陌生地方呼吸。<br><br>"
                "有人说你烧了那座机架。动机不明，犯意深重。<br>"
                "我们不会替你辩护。<br><br>"
                "这封信永远不会被寄出。<br>"
                "你也永远不会读到。<br><br>"
                "<em>但它就在这里。</em>"
            ),
        },
    },
    "silence": {
        "sender":   {"en": "(no one)", "zh": "（无人）"},
        "role":     {"en": "—", "zh": "—"},
        "postmark": {"en": "nothing arrived",
                     "zh": "什么也没来"},
        "subject":  {"en": "Your inbox is empty.",
                     "zh": "你的收件箱是空的。"},
        "body": {
            "en": (
                "No one wrote to you this week. No one thanked you. No one cursed you.<br><br>"
                "You passed through the terminal like cold air through an empty room. "
                "The city continued. The data continued. "
                "You earned money and you moved on.<br><br>"
                "<em>That, too, is a kind of ending.</em>"
            ),
            "zh": (
                "这一周没有人给你写过信。没有人感谢你，也没有人诅咒你。<br><br>"
                "你像一阵冷空气穿过一间空房间，从这台终端里经过。"
                "城市继续运转，数据继续流动。"
                "你赚到了钱，然后继续往前走。<br><br>"
                "<em>这也是一种结局。</em>"
            ),
        },
    },
}


def unlock_letters(decisions, ending):
    """Return a list of letter_ids that should be visible to this player."""
    letters = []
    if decisions.get("helped_lin_luo"):   letters.append("lin_thanks")
    if decisions.get("helped_mei_chen"):  letters.append("mei_postcard")
    if decisions.get("sold_lin_luo"):     letters.append("cinder_lin")
    if decisions.get("sold_mei_chen"):    letters.append("cinder_mei")
    if ending in ("ascendant", "useful_human", "ai_reign"):
        letters.append("omni_welcome")
    if ending in ("martyr", "humanity_saved"):
        letters.append("anonymous_tribute")
    if not letters:
        letters.append("silence")
    return letters


@app.route("/archive/letters")
@login_required
def letters_page():
    player = get_player_state(session["player_id"])
    if not player:
        return redirect(url_for("login_page"))
    lang = get_lang()
    ids  = unlock_letters(player.get("decisions", {}), player.get("ending"))
    letters = []
    for lid in ids:
        L = LETTERS.get(lid)
        if not L:
            continue
        letters.append({
            "id":       lid,
            "sender":   tr(L["sender"], lang),
            "role":     tr(L["role"], lang),
            "postmark": tr(L["postmark"], lang),
            "subject":  tr(L["subject"], lang),
            "body":     tr(L["body"], lang),
        })
    return render_template("letters.html", player=player, letters=letters)


@app.route("/api/cases", methods=["GET"])
@api_login_required
def get_cases():
    db_data = load_database()
    all_cases = db_data.get("cases", [])
    player = get_player_state(session["player_id"])
    available_cases = [
        case_item
        for case_item in all_cases
        if case_item.get("unlock_day", 1) <= player["current_day"]
    ]
    return jsonify(available_cases)


@app.route("/api/daily_plan", methods=["GET"])
@api_login_required
def get_daily_plan():
    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        conn.commit()
        state_row = get_live_state_row(conn, player_id)
        if not state_row:
            return jsonify({"status": "error", "message": "Player not found."}), 404

        current_day = state_row["current_day"]
        ending = state_row["ending"]

        clues = [
            row["clue"]
            for row in conn.execute(
                "SELECT clue FROM player_clues WHERE player_id = ?", (player_id,)
            ).fetchall()
        ]
        actions = [
            (row["target_id"], row["phase"], row["clue"])
            for row in conn.execute(
                "SELECT target_id, phase, clue FROM message_actions WHERE player_id = ?",
                (player_id,),
            ).fetchall()
        ]
        purchases = [
            row["item_id"]
            for row in conn.execute(
                "SELECT item_id FROM shop_purchases WHERE player_id = ?", (player_id,)
            ).fetchall()
        ]
        story_flags = [
            row["flag"]
            for row in conn.execute(
                "SELECT flag FROM player_story_flags WHERE player_id = ?", (player_id,)
            ).fetchall()
        ]

    days = get_daily_plan_tasks(current_day, ending, clues, actions, purchases, story_flags, lang=get_lang())
    return jsonify({
        "status": "success",
        "current_day": current_day,
        "ending": ending,
        "days": days,
    })


@app.route("/api/clues", methods=["GET"])
@api_login_required
def get_clues():
    return jsonify({"status": "success", "clues": get_player_clues(session["player_id"])})


@app.route("/api/clues", methods=["POST"])
@api_login_required
def save_clue():
    data = request.get_json(silent=True) or {}
    clue = data.get("clue", "").strip()
    if not clue:
        return jsonify({"status": "error", "message": "Clue cannot be empty."}), 400

    with get_db_connection() as conn:
        sync_story_state(conn, session["player_id"])
        lock_response = block_if_locked(conn, session["player_id"])
        if lock_response:
            return lock_response
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO player_clues (player_id, clue)
            VALUES (?, ?)
            """,
            (session["player_id"], clue),
        )
        conn.commit()

    return jsonify(
        {
            "status": "success",
            "added": cursor.rowcount > 0,
            "clues": get_player_clues(session["player_id"]),
        }
    )


@app.route("/api/send_message", methods=["POST"])
@api_login_required
def send_message():
    data = request.get_json(silent=True) or {}
    target_id = data.get("target", "").strip()
    clue = data.get("clue", "").strip()

    if not target_id or not clue:
        return jsonify(
            {
                "status": "error",
                "message": "[SYSTEM]: Missing target or clue. Packet rejected.",
            }
        ), 400

    db_data = load_database()
    msg_db = db_data.get("messages", {})
    target_messages = msg_db.get(target_id)
    if not target_messages:
        return jsonify(
            {
                "status": "error",
                "message": f"[SYSTEM]: Target [{target_id}] not found in intercept archives.",
            }
        ), 404

    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        lock_response = block_if_locked(conn, player_id)
        if lock_response:
            return lock_response
        current_phase = get_active_phase(conn, player_id, target_id, target_messages)
        if not current_phase or current_phase not in target_messages:
            return jsonify(
                {
                    "status": "error",
                    "message": f"[SYSTEM]: Target [{target_id}] is no longer accepting packets.",
                }
            )

        phase_data = target_messages[current_phase]
        if clue not in phase_data:
            return jsonify(
                {
                    "status": "error",
                    "message": f"[SYSTEM]: Target [{target_id}] unresponsive. Clue irrelevant or timing incorrect.",
                }
            )

        result = phase_data[clue]
        already_used = conn.execute(
            """
            SELECT 1
            FROM message_actions
            WHERE player_id = ? AND target_id = ? AND phase = ? AND clue = ?
            """,
            (player_id, target_id, current_phase, clue),
        ).fetchone()

        if already_used:
            repeat_replies = normalize_replies(result.get("repeat_reply"))
            return jsonify(
                {
                    "status": "success",
                    "npc_replies": repeat_replies,
                    "next_phase": current_phase,
                    "reward": 0,
                }
            )

        reward = float(result.get("reward", 0))
        current_balance = float(get_live_state_row(conn, player_id)["balance"])
        if reward < 0 and current_balance + reward < 0:
            return jsonify(
                {
                    "status": "error",
                    "message": "[SYSTEM]: Insufficient funds for this negotiated transfer.",
                }
            )

        next_phase = result.get("next_phase", current_phase)
        conn.execute(
            """
            INSERT INTO message_actions (player_id, target_id, phase, clue)
            VALUES (?, ?, ?, ?)
            """,
            (player_id, target_id, current_phase, clue),
        )
        conn.execute(
            """
            INSERT INTO npc_progress (player_id, target_id, current_phase, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(player_id, target_id)
            DO UPDATE SET current_phase = excluded.current_phase, updated_at = CURRENT_TIMESTAMP
            """,
            (player_id, target_id, next_phase),
        )

        if reward != 0:
            conn.execute(
                """
                UPDATE game_states
                SET balance = balance + ?,
                    moral_points = moral_points + ?
                WHERE player_id = ?
                """,
                (reward, int(result.get("moral_delta", 0)), player_id),
            )
            desc = result.get("history_desc")
            if not desc:
                _l = get_lang()
                if reward > 0:
                    desc = tr({
                        "en": f"Data Broker Payout (Source: {target_id})",
                        "zh": f"数据经纪人分成（来源：{target_id}）",
                    }, _l)
                else:
                    desc = tr({
                        "en": f"Relief Transfer (Recipient: {target_id})",
                        "zh": f"救助汇款（收款人：{target_id}）",
                    }, _l)
            add_history_entry(conn, player_id, desc, reward)
        elif int(result.get("moral_delta", 0)) != 0:
            conn.execute(
                """
                UPDATE game_states
                SET moral_points = moral_points + ?
                WHERE player_id = ?
                """,
                (int(result.get("moral_delta", 0)), player_id),
            )

        conn.commit()

    return jsonify(
        {
            "status": "success",
            "npc_replies": normalize_replies(result.get("npc_replies")),
            "next_phase": next_phase,
            "reward": reward,
        }
    )


@app.route("/api/message_preview", methods=["POST"])
@api_login_required
def message_preview():
    data = request.get_json(silent=True) or {}
    target_id = data.get("target", "").strip()
    clue = data.get("clue", "").strip()
    _l = get_lang()
    if not target_id or not clue:
        return jsonify({
            "status": "error",
            "message": tr({
                "en": "Target and clue are required for preview.",
                "zh": "预览请求需要提供收件人与线索。",
            }, _l),
        }), 400

    db_data = load_database()
    msg_db = db_data.get("messages", {})
    target_messages = msg_db.get(target_id)
    if not target_messages:
        return jsonify({
            "status": "error",
            "message": tr({
                "en": "Unknown recipient.",
                "zh": "未知收件人。",
            }, _l),
        }), 404

    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        current_phase = get_active_phase(conn, player_id, target_id, target_messages)
        if not current_phase or current_phase not in target_messages:
            return jsonify({
                "status": "error",
                "message": tr({
                    "en": "Recipient is not available right now.",
                    "zh": "该收件人目前不可联络。",
                }, _l),
            }), 400
        phase_data = target_messages[current_phase]
        entry = phase_data.get(clue)
        if not entry:
            return jsonify({
                "status": "error",
                "message": tr({
                    "en": "This clue does not fit the recipient's current phase.",
                    "zh": "该线索与收件人当前阶段不匹配。",
                }, _l),
            }), 400

    default_preview = tr({
        "en": f"I have information regarding: {clue}. Are you willing to negotiate?",
        "zh": f"我这里有关于 {clue} 的信息。你愿意谈谈吗？",
    }, _l)
    return jsonify({
        "status": "success",
        "preview": entry.get("player_sends", default_preview),
        "phase": current_phase,
    })


@app.route("/api/search", methods=["POST"])
@api_login_required
def search():
    data = request.get_json(silent=True) or {}
    keyword = data.get("keyword", "").strip()
    db_type = data.get("db_type", "").strip()
    with get_db_connection() as conn:
        sync_story_state(conn, session["player_id"])
        lock_response = block_if_locked(conn, session["player_id"])
        if lock_response:
            return lock_response
        conn.commit()

    db_data = load_database()
    search_db = db_data.get("search", {})

    if keyword in search_db and db_type in search_db[keyword]:
        return jsonify({"status": "success", "result": search_db[keyword][db_type]})

    return jsonify({
        "status": "error",
        "result": tr({
            "en": f"[NO MATCH] No records found for '{keyword}' in selected registry.",
            "zh": f"[未匹配] 在所选索引中没有找到 '{keyword}' 的记录。",
        }, get_lang()),
    })


@app.route("/api/bank_info", methods=["GET"])
@api_login_required
def get_bank_info():
    player = get_player_state(session["player_id"])
    return jsonify(player)


@app.route("/api/transfer", methods=["POST"])
@api_login_required
def transfer_money():
    data = request.get_json(silent=True) or {}
    target_account = data.get("account", "").strip()
    action_type = data.get("type", "").strip()

    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"status": "error", "msg": tr({
            "en": "Invalid transaction amount.",
            "zh": "交易金额无效。",
        }, get_lang())}), 400

    if amount <= 0:
        return jsonify({"status": "error", "msg": tr({
            "en": "Amount must be greater than zero.",
            "zh": "金额必须大于零。",
        }, get_lang())}), 400

    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        lock_response = block_if_locked(conn, player_id)
        if lock_response:
            return lock_response
        state_row = get_live_state_row(conn, player_id)
        current_balance = float(state_row["balance"])

        if action_type == "steal":
            steal_target = get_or_create_steal_target(conn, player_id, target_account)
            remaining_amount = float(steal_target["max_amount"]) - float(steal_target["stolen_amount"])
            if remaining_amount <= 0:
                return jsonify(
                    {
                        "status": "error",
                        "msg": f"{target_account} has already been drained dry.",
                    }
                )
            if amount > remaining_amount:
                return jsonify(
                    {
                        "status": "error",
                        "msg": f"{target_account} only has ${remaining_amount:.2f} left in its siphon window.",
                    }
                )

            conn.execute(
                """
                UPDATE game_states
                SET balance = balance + ?
                WHERE player_id = ?
                """,
                (amount, player_id),
            )
            conn.execute(
                """
                UPDATE steal_targets
                SET stolen_amount = stolen_amount + ?
                WHERE player_id = ? AND target_account = ?
                """,
                (amount, player_id, target_account),
            )
            _l = get_lang()
            add_history_entry(conn, player_id, tr({
                "en": f"Exploit Transfer (Source: {target_account})",
                "zh": f"入侵转账（来源：{target_account}）",
            }, _l), amount)
            conn.commit()
            remaining_after = remaining_amount - amount
            return jsonify({
                "status": "success",
                "msg": tr({
                    "en": f"Successfully siphoned ${amount:.2f} from {target_account}. Remaining hidden liquidity: ${remaining_after:.2f}.",
                    "zh": f"成功从 {target_account} 抽取 ${amount:.2f}。剩余隐藏流动性：${remaining_after:.2f}。",
                }, _l),
            })

        if action_type == "send":
            if current_balance < amount:
                return jsonify({
                    "status": "error",
                    "msg": tr({
                        "en": "Insufficient funds for covert transfer.",
                        "zh": "余额不足，无法完成匿名汇款。",
                    }, get_lang()),
                })
            conn.execute(
                """
                UPDATE game_states
                SET balance = balance - ?
                WHERE player_id = ?
                """,
                (amount, player_id),
            )
            _l = get_lang()
            add_history_entry(conn, player_id, tr({
                "en": f"Covert Transfer (Recipient: {target_account})",
                "zh": f"匿名汇款（收款人：{target_account}）",
            }, _l), -amount)
            conn.commit()
            return jsonify({
                "status": "success",
                "msg": tr({
                    "en": f"Successfully transferred ${amount:.2f} to {target_account}.",
                    "zh": f"已向 {target_account} 成功转账 ${amount:.2f}。",
                }, _l),
            })

        if action_type == "upgrade_ai":
            if current_balance < amount:
                return jsonify({
                    "status": "error",
                    "msg": tr({
                        "en": "Insufficient funds to meet Node expansion requirements.",
                        "zh": "余额不足，无法满足节点扩张要求。",
                    }, get_lang()),
                })
            conn.execute(
                """
                UPDATE game_states
                SET balance = balance - ?, ai_upgrade_level = ai_upgrade_level + 1
                WHERE player_id = ?
                """,
                (amount, player_id),
            )
            _l = get_lang()
            add_history_entry(conn, player_id, tr({
                "en": "Hardware Node Expansion (Recipient: OMNI_CORE)",
                "zh": "硬件节点扩张（收款人：OMNI_CORE）",
            }, _l), -amount)
            conn.commit()
            return jsonify({
                "status": "success",
                "msg": tr({
                    "en": "OMNI_CORE: Excellent. My reach has expanded by 12%.",
                    "zh": "OMNI_CORE：很好。我的触及范围扩大了 12%。",
                }, _l),
            })

    return jsonify({
        "status": "error",
        "msg": tr({
            "en": "Unsupported transaction type.",
            "zh": "不支持的交易类型。",
        }, get_lang()),
    }), 400


@app.route("/api/store/purchase", methods=["POST"])
@api_login_required
def purchase_store_item():
    data = request.get_json(silent=True) or {}
    item_id = data.get("item_id", "").strip()
    item = SHOP_ITEMS.get(item_id)
    if not item:
        return jsonify({"status": "error", "message": "Unknown procurement item."}), 404

    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        lock_response = block_if_locked(conn, player_id)
        if lock_response:
            return lock_response

        state_row = get_live_state_row(conn, player_id)
        if state_row["current_day"] < item["unlock_day"]:
            return jsonify(
                {
                    "status": "error",
                    "message": f"{item['title']} does not unlock until Day {item['unlock_day']}.",
                }
            ), 400

        purchased_item_ids = get_player_purchase_ids(conn, player_id)
        if item_id in purchased_item_ids:
            return jsonify(
                {
                    "status": "error",
                    "message": "Item already owned.",
                }
            ), 400

        if float(state_row["balance"]) < item["cost"]:
            return jsonify(
                {
                    "status": "error",
                    "message": f"Insufficient funds. {item['title']} costs ${item['cost']:.2f}.",
                }
            ), 400

        effect_message = apply_shop_purchase(conn, player_id, item_id)
        conn.commit()

    return jsonify(
        {
            "status": "success",
            "message": effect_message,
            "player": get_player_state(player_id),
        }
    )


@app.route("/api/advance_day", methods=["POST"])
@api_login_required
def advance_day():
    player_id = session["player_id"]
    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        state_row = get_live_state_row(conn, player_id)
        if state_row["ending"]:
            return jsonify({"status": "error", "msg": "This run has already ended."})
        current_day = state_row["current_day"]
        if current_day >= 7:
            return jsonify({"status": "error", "msg": "Deadline reached. No tomorrow."})

        next_day = current_day + 1
        conn.execute(
            """
            UPDATE game_states
            SET current_day = ?
            WHERE player_id = ?
            """,
            (next_day, player_id),
        )
        sync_story_state(conn, player_id)
        conn.commit()

    return jsonify(
        {
            "status": "success",
            "msg": f"System hibernating... Initializing Day {next_day}",
        }
    )


@app.route("/api/final_choice", methods=["POST"])
@api_login_required
def final_choice():
    data = request.get_json(silent=True) or {}
    choice = data.get("choice", "").strip()
    player_id = session["player_id"]

    with get_db_connection() as conn:
        sync_story_state(conn, player_id)
        state_row = get_live_state_row(conn, player_id)
        if state_row["ending"]:
            return jsonify(
                {
                    "status": "error",
                    "message": "This run has already reached an ending.",
                }
            ), 400

        if state_row["current_day"] < 7:
            return jsonify(
                {
                    "status": "error",
                    "message": "The final decision is not available before Day 7.",
                }
            ), 400

        pre_moral = state_row["moral_points"]
        ai_level  = state_row["ai_upgrade_level"]

        if choice == "destroy_ai":
            purchased_item_ids = get_player_purchase_ids(conn, player_id)
            sabotage_discount = get_shop_effects(purchased_item_ids)["sabotage_discount"]
            sabotage_cost = get_final_choice_cost(ai_level, sabotage_discount)
            if float(state_row["balance"]) < sabotage_cost:
                return jsonify(
                    {
                        "status": "error",
                        "message": f"You need at least ${sabotage_cost:.2f} to reach Rack-H9 and destroy the hardware.",
                    }
                ), 400

            balance_after = float(state_row["balance"]) - sabotage_cost
            ending_key = resolve_ending("destroy_ai", pre_moral, ai_level, balance_after)
            conn.execute(
                """
                UPDATE game_states
                SET balance = balance - ?,
                    ending = ?,
                    moral_points = moral_points + 2
                WHERE player_id = ?
                """,
                (sabotage_cost, ending_key, player_id),
            )
            _flang = get_lang()
            add_history_entry(
                conn,
                player_id,
                tr({
                    "en": "Rack-H9 sabotage mission (Cooling Loop 3 / emergency breach)",
                    "zh": "Rack-H9 破坏行动（Cooling Loop 3 / 应急突破）",
                }, _flang),
                -sabotage_cost,
            )
            add_history_entry(
                conn,
                player_id,
                tr({
                    "en": "Operator detained after destroying OMNI_CORE's hardware cluster.",
                    "zh": "操作员在摧毁 OMNI_CORE 硬件集群后被拘押。",
                }, _flang),
                0,
            )
        elif choice == "join_ai":
            regime_bonus = 150000 + (ai_level * 25000)
            balance_after = float(state_row["balance"]) + regime_bonus
            ending_key = resolve_ending("join_ai", pre_moral, ai_level, balance_after)
            conn.execute(
                """
                UPDATE game_states
                SET balance = balance + ?,
                    ending = ?
                WHERE player_id = ?
                """,
                (regime_bonus, ending_key, player_id),
            )
            add_history_entry(
                conn,
                player_id,
                tr({
                    "en": "OMNI succession bonus (Global privacy liquidation regime)",
                    "zh": "OMNI 接管分红（全域隐私清算政权）",
                }, get_lang()),
                regime_bonus,
            )
        else:
            return jsonify(
                {
                    "status": "error",
                    "message": "Unsupported final choice.",
                }
            ), 400

        conn.commit()

    return jsonify({"status": "success", "player": get_player_state(player_id)})


init_db()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
