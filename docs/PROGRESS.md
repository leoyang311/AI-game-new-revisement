# OMNI_CORE Terminal · Development Progress and Optimization Report

> A record of the technical evolution from the initial MVP to the current release-ready build, with a focus on **player-facing UI and experience** improvements.

---

## 0 · Executive Summary (drop-in paragraphs)

OMNI_CORE Terminal is a seven-day narrative simulation that puts the player in the role of a corporate data analyst running a side-business selling customer records. Built on Flask + SQLite with a vanilla HTML/JS frontend, the project was delivered in four calendar days across eight commits, growing from a 6,000-line MVP to a 10,800-line polished release.

The second and third days of development focused entirely on the player-facing experience. We introduced a complete **bilingual (English / Simplified Chinese) content layer** that translates every piece of game text — endings, daily guidance, ledger descriptions, API messages, and UI chrome — driven by a single language cookie and surfaced through a deliberately hidden easter-egg toggle in the navigation bar. A secondary **VS 2017 C++ Light theme** was added for players uncomfortable with the signature dark-green CRT aesthetic, persisted per-browser and applied before first paint to avoid any flash of unstyled content.

On top of the core gameplay loop, we layered a four-step onboarding wizard, a daily story briefing modal, a persistent Mission Log task tracker, inline SVG illustrations for every shop item (from a recruiter portal to the Rack-H9 server room floor plan), NPC contact cards with threat-level indicators, two stylistically opposite ending cinematics (a monochrome blackout sequence for the destruction path, an OMNI_CORE "assimilation log" glitch cascade for the collaboration path), a shareable PNG receipt card of the player's final run, and a post-ending Survivor Archive of seven letters that unlock based on specific moral choices. Typography was enlarged globally, line-height relaxed, and key numbers (balance, stage label) scaled up to preserve the terminal aesthetic while dramatically reducing eye strain.

The result is a game that still reads as a hostile AI terminal, yet is now approachable to players who prefer light mode, don't read English, need onboarding, or simply want to share their ending. The full system is deployed at http://165.227.82.123/ behind nginx + gunicorn + systemd, with `git pull && systemctl restart` as the complete update cycle.

---

## 1 · Development Timeline

Eight commits in four days — an expansion from **6,000 to 10,800 lines** of code. Every change is aimed at either "lowering the barrier to entry" or "deepening the emotional arc."

| Commit    | Date             | Contribution                                                   |
| --------- | ---------------- | -------------------------------------------------------------- |
| `b0a7aa6` | 04-18 11:35      | Initial commit — OMNI_CORE Terminal game skeleton                |
| `306790e` | 04-18 13:09      | **Bilingual i18n system + VS 2017 C++ Light theme**              |
| `90b8d0c` | 04-18 13:38      | **Chinese content layer (bilingual JSON merge)**                 |
| `643641f` | 04-18 18:41      | **Ending receipt card + cinematic + survivor letters**           |
| `c0ee868` | 04-18 21:16      | Text polish (EN / ZH tone calibration)                           |
| `b191ae1` | 04-19 14:05      | Full architecture / gameplay / story / endings / manual docs     |
| `54f2a90` | 04-19 20:40      | Bug fix: empty receipt card + wire transfer not counted as help  |
| `2bc20ba` | 04-21 18:22      | Stage label in the header now tracks the actual current day      |

---

## 2 · UI / Experience Improvements

### 2.1 Typography and Layout (global)

The first release ran mostly on `12-13px` body text — on-brand for a terminal, but punishing after any length of time. Across `306790e` and `643641f`:

- Body text lifted from `13-14px` to `14-16px`
- Key information: `stage-line` now `18px`; `balance-amount` rendered at `40px`
- Line-height relaxed from `1.55` to `1.8`, giving mixed CJK / Latin text proper breathing room

### 2.2 Light Theme (`306790e`)

A **friendly alternative** for players uncomfortable with the dark-green CRT aesthetic:

- Full VS 2017 C++ Light palette: `#007acc` blue, `#ffffff` white background, `#a31515` red, `#008000` green
- Theme is applied **before first paint** from `localStorage` to eliminate any flash of unstyled content (FOUC)
- Shared `_theme.html` partial included on every page — one toggle flips the whole site
- Key emotional beats (the ending cinematics) **deliberately stay dark** — the design note: *"a glitch collapse in a bright IDE would lose impact"*

The toggle button auto-injects into each page's nav — no per-page markup needed.

### 2.3 Easter Egg: EN / ZH Language Toggle (`306790e` + `90b8d0c`)

**The toggle is intentionally hidden** — `#nav-lang`'s color, background, and border are all set to the nav background (`#000d00`), making it effectively invisible but still clickable. Finding it is the easter egg.

Three layers are wired together:

- **Frontend:** `_i18n.html` declares a `window.I18N` object with ~140 EN and ZH strings each; `applyI18n()` walks `[data-i18n]` / `[data-i18n-html]` / `[data-i18n-ph]` / `[data-i18n-title]` attributes and swaps in place
- **Backend:** `tr({"en": ..., "zh": ...})` helper + `lang` cookie. Endings, stage labels, guidance, shop items, daily plan tasks, ledger descriptions, and API error messages all flow through one translator
- **Content:** `database_zh.json` carries only translated fields; `load_database(lang)` deep-merges at load time — logic keys (`next_phase / reward / moral_delta`) live only in the English source to prevent drift

### 2.4 Onboarding + Daily Briefing (`643641f`)

Onboarding graduated from "drop the player at the desktop" to a **three-phase cinematic intro**:

- **Intro Wizard (4 steps, first-launch only):** Identity → The Deal → Your Toolkit → Final Warning. Each slide has a fade animation, a narrative quote, and a warning box
- **Daily Briefing Modal:** every new day opens with a situation report explaining what just happened and what to do today. Written twice in full EN and ZH (`DAY_BRIEFINGS_EN` / `DAY_BRIEFINGS_ZH`)
- **Mission Log** (📋): an always-available task tracker with collapsible per-day progress bars and live `done / total` counts

All three use `localStorage` flags to suppress repeats, but Mission Log and Story Archive stay accessible from the desktop for review.

### 2.5 Illustrations and Scene SVGs (`643641f`)

To replace bare text cards, every shop item was given an **inline SVG scene**:

- **Leaked Recruiter Bundle** → a recruiter portal with a candidate avatar, export button, and buyer tags
- **Ghost Proxy Mesh** → funds routing through Frankfurt / Singapore / Reykjavik / Cayman relay nodes, with packet dots in flight
- **Victim Archive Mirror** → two CCTV panels tracking Lin Luo / Mei Chen, plus an export progress panel on the right
- **Rack-H9 Breach Kit** → a server-room floor plan with Rack-H9 highlighted in red and the breach route drawn with a dashed path + thermite annotation

A CRT scanline overlay adds the apocalyptic-terminal feel. **Locked items** automatically get a translucent `— CLASSIFIED — UNLOCK ON DAY N —` banner.

Search Node and Messenger also gained avatars (via the **DiceBear pixel-art API**). The NPC contact card shows a threat bar, response-time badge, and entity classification (AI / BROKER / HUMAN / ANONYMOUS).

### 2.6 Ending Receipt Card + Cinematics (`643641f`)

The ending used to be a paragraph of text. It is now **two stylistically opposite cinematics**:

- **Destroy family** (blow up Rack-H9): blackout + monochrome lines surfacing every 0.9s — `> terminal offline` → `> rack-H9 destroyed at 06:14:22` → an ending-specific closing line
- **Join family** (side with OMNI): red radial vignette + scanlines + RGB-split glitch + a cascading `[OMNI] ABSORBING OPERATOR` log, followed after ~4.5s by the ending title (also glitching)

After the cinematic, the player sees a **Receipt Card** — operator name, final balance, moral credit, AI funding count, a three-way decision checklist (✓ / ✗ / ·), and the ending's signature epitaph. A `[ SAVE IMAGE ]` button uses `html2canvas` to produce a PNG, so **players can share their ending**.

### 2.7 Survivor Archive (`643641f`)

After any ending, `/archive/letters` surfaces three to five of seven possible letters, based on what the player did that week:

- Lin Luo's thank-you note (saved him)
- M.'s postcard (saved Mei Chen)
- A Cinder Market invoice (sold either victim)
- OMNI_CORE HR's Class-B promotion letter (join path)
- An anonymous tribute (martyr)
- The Silence letter (you did nothing)

This is the **emotional coda** — abstract game state translated into letters written by actual (fictional) people.

---

## 3 · Backend and Infrastructure Improvements

| Change                                                      | Value                                                                                         |
| ----------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `STORY_REVISION` content-versioning                         | Storyline rewrites trigger an automatic reset for affected saves, preventing data drift       |
| `maybe_add_column()` migration helper                       | Additive schema changes stay backward-compatible — existing players don't need a rebuild      |
| `sync_story_state()` idempotent forced events               | Day 5/6 auto-sales and Day 7 lockdown fire exactly once, regardless of how many API calls hit |
| `RELIEF_WALLETS` bank-wire dispatch (`54f2a90`)             | Bank wires to Lin's card / Mei's wallet count as "helped"; PRIMARY KEY prevents double-count  |
| Ending resolved from `(choice, moral, ai_level, balance)`   | A binary Day-7 choice explodes into 6 differentiated endings                                  |
| Legacy alias endings (`humanity_saved` / `ai_reign`)        | Older saves keep working after the ending system was expanded                                 |
| Deployment pipeline                                         | systemd + gunicorn + nginx — a single `git pull && systemctl restart` ships a new build       |

---

## 4 · Player-Visible Journey

From "just opened the tab" to "ending screen saved":

```
Login       → 4-step onboarding wizard          [NEW]
Day 1       → Opening situation report modal    [NEW]
Desktop     → Operation timeline + Mission Log  [NEW]
            → One-click Light theme             [NEW, optional]
            → Hidden EN / ZH easter-egg toggle  [NEW, easter egg]
Store       → Inline SVG scene illustrations    [NEW]
Each day    → Briefing + stage label            [NEW]
Ending     → Family-specific cinematic         [NEW]
            → Shareable receipt card PNG        [NEW]
            → Survivor Letters archive          [NEW]
```

Every addition was either **"reduce friction"** or **"deepen emotion"** — no feature was added purely to show off technique.

---

## 5 · Future Directions

- **itch.io static build** — port Flask + SQLite logic to pure frontend + localStorage, ship as an HTML5 project for wider reach
- **Linux AppImage / Windows exe** — `pyinstaller` bundle for non-technical players who want an offline launcher
- **More branching storylines / Week 2** — extend through the existing `STORY_REVISION` mechanism without breaking old saves

---

*Document version: 2026-04-21*
