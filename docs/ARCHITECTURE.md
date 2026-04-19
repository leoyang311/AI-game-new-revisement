# System Architecture

## Stack

- **Backend:** Python 3, Flask, SQLite (file: `game.db`)
- **Frontend:** vanilla HTML / CSS / JS, no build step
- **Content:** static JSON (`database.json` + `database_zh.json`)
- **Prod:** gunicorn (3 sync workers) behind nginx, managed by `systemd`

No frameworks, no bundler, no JS dependencies beyond one CDN import
(`html2canvas` used to render the ending receipt as a PNG).

## Repository layout

```
.
├── app.py                    Flask app: routes, game logic, DB, content dicts
├── database.json             Cases, search entries, NPC scripts (source of truth, EN)
├── database_zh.json          ZH overlay for the above (merged into base at load time)
├── requirements.txt          Flask + gunicorn
├── Procfile                  For one-click PaaS
├── game.db                   SQLite (created on first boot, gitignored)
├── templates/
│   ├── _theme.html           Shared partial — VS-light theme + toggle button
│   ├── _i18n.html            Shared partial — I18N dict + t()/applyI18n() helpers
│   ├── login.html
│   ├── index.html            Main desktop: Day briefing, Mission Log, endings overlay
│   ├── search.html           OSINT Search Node
│   ├── bank.html             Offshore Routing
│   ├── message.html          Encrypted Messenger
│   ├── store.html            Covert Procurement
│   ├── letters.html          Survivor Archive
│   └── style_preview.html    Design mock (dev-only)
└── docs/                     This directory
```

## Request flow

```
browser  ──────►  nginx :80  ─────►  gunicorn (unix:game.sock)
                                       │
                                       ▼
                                     Flask (app.py)
                                       │
                          ┌────────────┼────────────┐
                          ▼            ▼            ▼
                      sqlite        JSON load     session cookie
                      game.db    database*.json  (player_id, lang)
```

## Data flow for a page view

```
GET /                                  (browser)
  └─► Flask index() → get_player_state(player_id)
        ├─► SQLite: game_states, ledger_history, message_actions, shop_purchases
        ├─► get_lang() reads cookie `lang` → "en" or "zh"
        ├─► get_story_display() — per-day stage label + notice (bilingual)
        ├─► get_guidance_data()  — per-day objective + steps (bilingual)
        ├─► build_shop_items()   — unlocked items + pricing (bilingual)
        ├─► derive_decisions()   — helped/sold/ignored flags
        └─► get_ending_content() — if ending is set, adds title/summary/family
  └─► render_template("index.html", player=...)
        └─► index.html includes _theme.html + _i18n.html at top of <body>
              ├─► _theme.html applies data-theme="light" before paint
              └─► _i18n.html applies data-i18n attributes after DOMContentLoaded
```

## SQLite schema

| Table                | Purpose                                              |
|---                   |---                                                   |
| `players`            | Username → id mapping                                |
| `game_states`        | Per-player: `current_day`, `balance`, `ai_upgrade_level`, `moral_points`, `ending` |
| `ledger_history`     | Every transaction (`time_text`, `desc`, `amount_text`) |
| `player_clues`       | Collected clue names                                 |
| `npc_progress`       | Per-NPC current phase                                |
| `message_actions`    | `(target_id, phase, clue)` tuples the player has sent |
| `player_story_flags` | Event-completion flags (`forced_sale_day5`, …)       |
| `steal_targets`      | Per-player siphon-target caps and drained amounts    |
| `shop_purchases`     | Item IDs the player has bought                       |

The DB is created on first boot by `init_db()`. There is one forward-compatible
`maybe_add_column()` helper for adding new columns in later revisions.

## Route list

Page routes (HTML):

| Method | Path              | Template           | Notes                                    |
|---     |---                |---                 |---                                       |
| GET    | `/style_preview`  | style_preview.html | Design mock                              |
| GET    | `/login`          | login.html         | Player name gate (no password)           |
| POST   | `/login`          | login.html         | Creates or resumes a player              |
| GET    | `/logout`         | —                  | Clears session                           |
| GET    | `/`               | index.html         | Main desktop                             |
| GET    | `/search`         | search.html        | OSINT Search Node                        |
| GET    | `/bank`           | bank.html          | Offshore Routing                         |
| GET    | `/message`        | message.html       | Encrypted Messenger                      |
| GET    | `/store`          | store.html         | Covert Procurement                       |
| GET    | `/archive/letters`| letters.html       | Post-ending Survivor Archive             |

JSON API:

| Method | Path                    | Returns / does                            |
|---     |---                      |---                                        |
| GET    | `/api/cases`            | Cases the player can currently see        |
| GET    | `/api/daily_plan`       | Per-day tasks with `done` status          |
| GET    | `/api/clues`            | Player's clue buffer                      |
| POST   | `/api/clues`            | Append a clue to the buffer               |
| GET    | `/api/bank_info`        | Current player state (balance + history)  |
| POST   | `/api/transfer`         | Siphon / Wire / Upgrade_AI                |
| POST   | `/api/search`           | Look up a clue in a database              |
| POST   | `/api/message_preview`  | Generate the outgoing message preview     |
| POST   | `/api/send_message`     | Commit a send; may change phase / reward  |
| POST   | `/api/store/purchase`   | Buy a shop item                           |
| POST   | `/api/advance_day`      | End current day → next                    |
| POST   | `/api/final_choice`     | Day 7: `destroy_ai` or `join_ai`          |

All `/api/*` routes require a valid session (`@api_login_required`).

## Internationalization (i18n)

Two-layer system (frontend + backend), driven by a single `lang` cookie.

**Frontend — `templates/_i18n.html`:**
- Declares `window.I18N` with `en` / `zh` string tables.
- `t(key)` returns the current-language string.
- `tFmt(key, vars)` supports `{placeholder}` substitution.
- `applyI18n()` walks the DOM and replaces `[data-i18n]`, `[data-i18n-html]`,
  `[data-i18n-ph]`, `[data-i18n-title]` attributes in-place.
- Hidden language toggle button is auto-injected into the nav.
- `I18N.setLang()` saves to `localStorage`, writes the `lang` cookie, then
  `location.reload()` so server-rendered strings refresh too.

**Backend — `app.py`:**
- `get_lang()` reads `request.cookies["lang"]` → "en" or "zh".
- `tr(bundle)` accepts `{"en": "…", "zh": "…"}` and picks the right one.
- Endings, guidance, story stages, shop items, daily plan tasks, history
  descriptions, and API error messages all go through `tr()`.

**Content — `database.json` + `database_zh.json`:**
- `load_database(lang)` merges the two files at load time. The ZH file only
  needs to carry translated fields — logic keys (`next_phase`, `reward`,
  `moral_delta`) stay in the base file.

## Theme system

- Default theme: "terminal" — dark green, CRT look.
- Alternate theme: "light" — VS 2017 C++ Light palette.
- Toggle stored in `localStorage.game_theme`, read before paint to avoid FOUC.
- Mechanism: `<html data-theme="light">` + a dark-to-light override stylesheet
  shipped as `_theme.html`. Every page includes this partial, so switching on
  one page affects all pages immediately.

## Ending cinematic

Triggered by `POST /api/final_choice` success. The browser:
1. Adds `class="family-{destroy|join}"` to `#ending-overlay`.
2. For **join** family: injects an OMNI_CORE "assimilation" log cascade with
   RGB-split glitch + scan lines. After ~5 s, the ending title + summary fade
   in over a red radial vignette.
3. For **destroy** family: renders black with sequential monochrome lines
   (`> terminal offline`, `> rack-H9 destroyed at 06:14:22`, and one
   ending-specific closing line).
4. `[ CONTINUE ]` button triggers `location.reload()`; the desktop then shows
   the Receipt Card and unlocks `/archive/letters`.

## Deployment

Target: a 1-vCPU / 512 MB DigitalOcean droplet running Ubuntu 24.

```
/var/www/game/           clone of this repo
/var/www/game/venv/      Python virtualenv with Flask + gunicorn
/etc/systemd/system/game.service
/etc/nginx/sites-enabled/default   → proxies to unix:/var/www/game/game.sock
```

Update cycle:

```bash
ssh root@165.227.82.123 \
  "cd /var/www/game && git pull && systemctl restart game.service"
```

Gunicorn does **not** hot-reload — always restart the service after pulling.
