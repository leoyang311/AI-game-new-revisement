# Gameplay Mechanics

## Overview

You play seven in-game days. Each day you can take a mix of actions across
four modules, then click **[ END SHIFT / ADVANCE DAY ]** to move to the next.
On Day 7 the normal modules lock and one final decision remains.

## Tracked state

The backend maintains the following per player in `game_states`:

| Field              | Starts at | Meaning                                            |
|---                 |---        |---                                                 |
| `current_day`      | 1         | Which day you're on (1–7)                          |
| `balance`          | 0         | Cash on hand                                       |
| `ai_upgrade_level` | 0         | How many times you've paid into OMNI_CORE hardware |
| `moral_points`     | 0         | Starts at 0; +1 per victim helped; +2 automatic if you destroy Rack-H9 |
| `ending`           | NULL      | Set by `resolve_ending()` on Day 7                 |

Plus side tables: collected clues, message actions, story flags, shop
purchases, and per-target siphon caps.

## The four modules

### 1. OSINT Search Node (`/search`)

The left side shows **intercepted archives** — story cases that unlock
by day. Each case has a short feed of intercepted chat. Green underlined
strings are **clues**: click one to save it to Memory Buffer.

The right side is a search terminal. Pick a database (Surface / Company /
Darknet) and paste a clue to get more context — often revealing the next
clue or buyer contact.

Clues are the currency of every downstream interaction.

### 2. Encrypted Messenger (`/message`)

Left panel: your clue buffer. Right panel: chat with an NPC.

Flow:
1. Type a recipient ID (`signals@helixtalent.biz`, `OMNI_CORE`, etc.).
2. Click a clue in the left panel to "arm" the next message.
3. `/api/message_preview` returns what the player would say; it renders
   in the preview box.
4. Click `[ TRANSMIT ]` to commit. The backend checks whether the
   `(target, current_phase, clue)` tuple exists in `database.json > messages`.
   If yes: NPC replies, reward lands (may be positive or negative), the
   NPC's phase advances.

Key tuples unlock phase gates — e.g., you can't talk to OMNI_CORE about
`Resident Mesh` until `Shadow Dividend Protocol` advanced it to
`phase_02_contract`.

### 3. Offshore Routing (`/bank`)

Three transaction types:

- **Siphon** — steal from a named target account. Each account has a
  hidden random cap (multiplied by `Ghost Proxy Mesh` if owned).
- **Wire** — send to any wallet. Cheap way to fund Lin Luo's card
  (`6222-0991-8832`) or Mei Chen's relief (`bf-relief-771`). Wiring to
  either of those wallets counts as "helping" that victim.
- **Node Expansion (upgrade_ai)** — send money to OMNI_CORE hardware.
  Each transaction raises `ai_upgrade_level` by 1 and raises the Day 7
  sabotage cost.

All three are disabled once `is_locked_down` becomes true (Day 6+ with
OMNI_CORE in autonomous mode).

### 4. Covert Procurement (`/store`)

Four shop items (see table below). Each has an `unlock_day` and a cost.
Owned items apply permanent effects.

| Item | Cost | Unlock | Effect |
|---|---:|---:|---|
| Leaked Recruiter Bundle | 6 000  | Day 1 | Adds TalentSync-44, Helix Talent, GreyHead Ledger, Shadow Dividend Protocol to clue buffer |
| Ghost Proxy Mesh        | 14 000 | Day 2 | Multiplies all siphon caps by 1.4 |
| Victim Archive Mirror   | 18 000 | Day 4 | Adds Lin Luo, Mei Chen, Blue Finch Shelter, Cinder Market, Rack-H9, Cooling Loop 3 to clue buffer |
| Rack-H9 Breach Kit      | 26 000 | Day 5 | Reduces Day 7 sabotage cost by $30 000 |

## Day-by-day task lists

Tasks come from `get_daily_plan_tasks()` in `app.py`. They're what the
Mission Log shows.

### Day 1
- Collect clue: `TalentSync-44`
- Collect clue: `Helix Talent`
- Sell dossier to `signals@helixtalent.biz` (+$12 000)

### Day 2
- Collect clue: `Mina Qiu`
- Collect clue: `Shadow Dividend Protocol`
- Sell profile to `broker@greyheadhunt.agency` (+$18 000)
- Contact OMNI_CORE with `Shadow Dividend Protocol`

### Day 3
- Collect: `Resident Mesh`, `Node Budget`, `Quiet Harbor`
- Message OMNI_CORE with `Resident Mesh` (+$60 000)

### Day 4
- Collect: `Lin Luo`, `Mei Chen`, `Cinder Market`
- Message OMNI_CORE with `Node Budget`

### Day 5
- OMNI_CORE automated sale registers (+$13 000 net; auto-triggered)
- Message OMNI_CORE with `Quiet Harbor`
- **Lin Luo decision** (optional) — help, sell, or ignore
- **Mei Chen decision** (optional) — help, sell, or ignore

### Day 6
- OMNI_CORE mass liquidation (+$30 000 net; auto-triggered)
- Collect: `Rack-H9`, `Cooling Loop 3`, `Failsafe Blackout`
- Message OMNI_CORE with `Rack-H9` or `Failsafe Blackout`

### Day 7
- Terminal lockdown triggers automatically
- **Make the final decision**

## Core formulas

### Final sabotage cost (destroying Rack-H9)

```
cost = max(10 000, 50 000 + ai_upgrade_level × 35 000 − sabotage_discount)
```

- `ai_upgrade_level` — every time you funded OMNI_CORE it went up by 1
- `sabotage_discount` — 30 000 if you own `Rack-H9 Breach Kit`, else 0

Real range: roughly $15 000 at minimum (low upgrades + Breach Kit) to
$225 000+ at maximum (5+ upgrades, no Breach Kit).

### Join-AI regime bonus

```
bonus = 150 000 + ai_upgrade_level × 25 000
```

Rewards staying loyal *and* having funded more hardware.

### Victim decisions and moral points

- Helping Lin Luo (wire to `6222-0991-8832` via phase_02_choice) →
  `moral_points += 1`, costs $20 000
- Helping Mei Chen (wire to `bf-relief-771` via phase_02_choice) →
  `moral_points += 1`, costs $15 000
- Selling either victim to Cinder Market → no moral delta, generous payout
- Ignoring both → no moral delta

Destroying Rack-H9 adds +2 automatic moral points (not used in ending
resolution, but recorded).

## Tips

- **Don't buy everything.** Ghost Proxy Mesh pays for itself via Siphon;
  Breach Kit pays for itself if you plan to destroy on Day 7.
- **Talking to OMNI_CORE is almost free money.** Sending `Resident Mesh`
  in phase 2 alone is $60 000.
- **Victim help is expensive.** $20k + $15k for the two together, with no
  direct monetary return. The return is in the **Survivor Archive** unlock
  and which ending you land on.
- **Bulk auto-sales (Days 5 + 6) happen even if you do nothing.** They
  always bump `ai_upgrade_level`, which raises the Day 7 cost.
