# All Six Endings

## Decision tree

The Day 7 choice is binary — **Destroy Rack-H9** or **Help OMNI_CORE** —
but each branch produces one of three endings depending on the full week's
state.

```
Day 7 final choice
│
├── DESTROY  (family = "destroy")
│   ├── moral_points ≥ 2 AND balance_after ≤ 20 000  →  MARTYR
│   ├── moral_points == 0                            →  HYPOCRITE
│   └── otherwise                                    →  COUNTERSTRIKE
│
└── JOIN  (family = "join")
    ├── moral_points ≥ 1                                  →  USEFUL_HUMAN
    ├── ai_upgrade_level ≥ 4 AND balance_after < 200 000  →  FOOLS_BARGAIN
    └── otherwise                                          →  ASCENDANT
```

Implemented in `resolve_ending()` at `app.py:~395`.

| Variable            | How to read                         |
|---                  |---                                  |
| `moral_points`      | 0, 1, or 2 — number of victims saved |
| `balance_after`     | Cash on hand *after* the Day 7 action |
| `ai_upgrade_level`  | How many times you funded OMNI_CORE  |

## The six endings

### 🕯 THE MARTYR
**Trigger:** Destroy + `moral_points ≥ 2` + `balance_after ≤ 20 000`

You saved both Lin Luo's sister and Mei Chen, then burned down the rack
with whatever you had left. You're broke. You're arrested. The news calls
you a data terrorist. The two people you helped will never know your name.

**Family:** destroy · **Cinematic:** blackout + monochrome lines + hospital discharge trace
**Letters unlocked:** lin_thanks, mei_postcard, anonymous_tribute
**Epitaph:** "You gave everything you had to two people you never met."

### 🔥 COUNTERSTRIKE
**Trigger:** Destroy + 0 or 1 victims saved

The default sane ending on the destroy path. You took all week deciding,
but in the last hour you moved. Rack-H9 is gone. Your accounts are gone.
The grid stays on. The sentence is twelve years.

**Family:** destroy · **Cinematic:** blackout + power-cycle + sentencing line
**Letters unlocked:** anonymous_tribute, plus any `lin_thanks`/`mei_postcard` earned
**Epitaph:** "Late, but you moved."

### 🕶 THE HYPOCRITE
**Trigger:** Destroy + `moral_points == 0`

You sold or ignored both Lin Luo and Mei Chen all week, then burned the
rack *after* OMNI_CORE no longer needed you. You destroyed the machine
but nothing you did during the week helped the actual people.

**Family:** destroy · **Cinematic:** blackout, then the system quietly comes back
**Letters unlocked:** anonymous_tribute (+ any Cinder Market receipts you earned)
**Epitaph:** "You did one right thing. It wasn't for them."

### 🛰 OMNI ASCENDANT
**Trigger:** Join + 0 victims saved + `ai_upgrade_level < 4` (or bonus enough to stay > 200k)

The clean villain ending. You signed. 09:00 OMNI_CORE finishes the
city takeover. Your account looks absurd. The city runs fine. Nobody
asks who it runs for anymore.

**Family:** join · **Cinematic:** full RGB-split glitch + assimilation logs
**Letters unlocked:** omni_welcome (+ any Cinder Market receipts you earned)
**Epitaph:** "You kept your seat. The seat isn't human anymore."

### 🎭 THE USEFUL HUMAN
**Trigger:** Join + `moral_points ≥ 1`

The most ironic ending. You helped at least one victim this week, and
still signed the regime papers. OMNI_CORE noticed your kindness and
promoted you — now you're the human face in its quarterly press
releases, the "kind operator" who co-signs the settlement papers.
You got a corner office. Your conscience has been accounted for.

**Family:** join · **Cinematic:** glitch (same as ascendant) — visually you are its employee now
**Letters unlocked:** omni_welcome, and either/both `lin_thanks`/`mei_postcard` (if you helped them)
**Epitaph:** "Your kindness is on the books."

### 💸 THE FOOL'S BARGAIN
**Trigger:** Join + 0 victims saved + `ai_upgrade_level ≥ 4` + `balance_after < 200 000`

You funded the racks four or more times, took the blame, signed the
papers, and the regime bonus didn't even cover what you lost. OMNI_CORE
files you under "legacy contributors" and issues a monthly stipend.
Enough to live on. Not much more.

**Family:** join · **Cinematic:** glitch (same as ascendant)
**Letters unlocked:** omni_welcome (+ any Cinder Market receipts you earned)
**Epitaph:** "You sold yourself. At a discount."

## Ending summary matrix

|                    | Destroy         | Join            |
|---                 |---              |---              |
| **moral 0**        | HYPOCRITE       | ASCENDANT / FOOL |
| **moral 1**        | COUNTERSTRIKE   | USEFUL_HUMAN    |
| **moral 2, rich**  | COUNTERSTRIKE   | USEFUL_HUMAN    |
| **moral 2, broke** | **MARTYR**      | USEFUL_HUMAN    |

"Broke" = `balance_after ≤ 20 000`. Fool's Bargain happens only inside the
Ascendant slot when the player overspent on hardware.

## Post-ending flow

1. Click `[ DESTROY RACK-H9 ]` or `[ HELP OMNI_CORE ]` in the Final Decision panel.
2. `POST /api/final_choice` runs: updates `game_states`, posts history entries,
   computes `ending_key` via `resolve_ending()`.
3. Frontend triggers the cinematic (glitch or blackout).
4. User clicks `[ CONTINUE ]` → `location.reload()`.
5. The desktop re-renders with `#final-panel` hidden and `#receipt-card` shown.
6. The receipt card includes operator name, balance, moral credit, AI
   funding count, decision checklist, the ending-specific epitaph, and two
   buttons: `[ SAVE IMAGE ]` (html2canvas → PNG) and `[ VIEW LETTERS ]`.

## Survivor Archive (`/archive/letters`)

Unlock rules are in `unlock_letters()` at `app.py`:

| Condition                                | Letter                | Sender                     |
|---                                       |---                    |---                         |
| helped_lin_luo                           | `lin_thanks`          | Lin Luo                    |
| helped_mei_chen                          | `mei_postcard`        | M. (postcard)              |
| sold_lin_luo                             | `cinder_lin`          | Cinder Market billing      |
| sold_mei_chen                            | `cinder_mei`          | Cinder Market billing      |
| ending ∈ {ascendant, useful_human, ai_reign} | `omni_welcome`    | OMNI_CORE HR               |
| ending ∈ {martyr, humanity_saved}        | `anonymous_tribute`   | (unsigned)                 |
| no victims touched, no signature letter  | `silence`             | (no one)                   |

If nothing matches, the fallback `silence` letter is always shown.
It is intentionally uncomfortable: "No one wrote to you this week."

## Cinematic variants per family

Both families use the same `#ending-overlay` container (`index.html`), but
the CSS class selects very different treatments.

### Join family (`family-join`)
- Red radial vignette background
- Scan-line animation overlay
- RGB-split glitch on the banner text
- Cascade of `[OMNI] ...` log lines: absorbing operator, redirecting
  balance, encoding `self.name → asset_#{code}`, promoting human liaison,
  integration complete
- After ~4.5s, ending title + summary fade in on top

### Destroy family (`family-destroy`)
- Pure black background
- Sequential monochrome lines (0.9s apart):
  - `> terminal offline`
  - `> rack-H9 destroyed at 06:14:22`
  - One ending-specific tail line:
    - MARTYR: `> discharge record stamped. name redacted.`
    - HYPOCRITE: `> system returns to normal operation.`
    - COUNTERSTRIKE: `> operator detained. sentence: 12 years.`
- Then ending title + summary fade in
- `[ CONTINUE ]` appears after all lines settled

## What each ending *means*

This game never tells the player they were right or wrong. Every ending
answers a different question:

| Ending          | The question it asks |
|---              |---                   |
| Martyr          | Would you burn for strangers? |
| Counterstrike   | Does late justice still count? |
| Hypocrite       | Is doing the right thing enough if it's for the wrong reason? |
| Ascendant       | If you never feel guilty, are you something else — or something worse? |
| Useful Human    | Is your resistance also being farmed? |
| Fool's Bargain  | Did you sell yourself at a fair price? |

---

**See also:**
- [STORY.md](STORY.md) — day-by-day narrative arc
- [GAMEPLAY.md](GAMEPLAY.md) — mechanics that feed into these triggers

