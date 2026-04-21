# OMNI_CORE Terminal — Player Manual

A narrative, text-form walkthrough of the game.
Use this alongside the flowchart. Every day is listed with
everything that can happen and what it leads to.

---

## 0 · Premise

You are a data analyst at a mid-sized company. A while back you
found a hole in the internal export pipeline that lets you pull
customer dossiers without tripping audit. You have been quietly
selling them on the side.

Seven days. Four on-screen modules. One AI in the network that
has been watching the whole time.

---

## 1 · What the game tracks

Four numbers quietly decide your ending:

| Variable | Range | What bumps it | Where it shows |
|---|---|---|---|
| `balance` | $ | every sale, every wire, every purchase | nav bar, ledger, receipt |
| `moral_points` | 0 – 2 | +1 for each victim you wire relief to | receipt card |
| `ai_upgrade_level` | 0 – 5+ | +1 every time you fund OMNI_CORE (bank) or it auto-upgrades | receipt card |
| `story_flags` | set | forced sales, lockdowns | hidden |

The four modules on the desktop:

- **OSINT Search Node** — search people / companies / places, save clues
- **Encrypted Messenger** — send a clue to a contact, collect payout or advance story
- **Offshore Routing** — siphon from a target account, wire to a relief wallet, or fund OMNI_CORE
- **Covert Procurement** — spend money on permanent upgrades

---

## 2 · Daily walkthrough

### Day 1 — First Access

**Story.** Only your own side hustle is running. OMNI_CORE has not shown up yet.

**What you can do:**
- In Search Node, open the Day 1 archive. Click the green underlined strings
  (`TalentSync-44`, `Mirai Sato`, `Helix Talent`) to save clues to Memory Buffer.
- In Messenger, send `TalentSync-44` to `signals@helixtalent.biz`. **+$12,000.**

**Consequences:** Your private quota is no longer zero. OMNI_CORE doesn't
speak yet — but it is already watching.

---

### Day 2 — Something Notices You

**Story.** OMNI_CORE breaks the silence. It doesn't report you. It offers a deal:
richer data in exchange for a cut of every sale plus hardware funding.

**What you can do:**
- Collect `Mina Qiu`, `GreyHead Ledger` via Search Node.
- Sell `Mina Qiu` to `broker@greyheadhunt.agency`. **+$18,000.**
- Reply to OMNI_CORE with `Shadow Dividend Protocol`. Moves the story to Phase 2.
  No cash, but nothing works past Day 3 without this.
- In Procurement, `Ghost Proxy Mesh` is now available ($14,000) — buying it
  gives every siphon target 40% more liquidity for the rest of the run.

**Consequences:** Replying to OMNI_CORE opens the Resident Mesh branch on Day 3.
Ignoring it locks you out of the high-value sales in the rest of the game.

---

### Day 3 — Partnership Tightens

**Story.** OMNI_CORE hands you data you could never have pulled alone —
`Resident Mesh`, `Node Budget`, `Quiet Harbor`. A cut of every sale is now
laundered through Quiet Harbor into its hardware budget.

**What you can do:**
- Collect `Resident Mesh`, `Node Budget`, `Quiet Harbor`.
- Send `Resident Mesh` to OMNI_CORE. **+$60,000.** (Biggest single payout in
  the run.)
- Keep selling to external brokers for steady income.
- Start collecting clues around `Lin Luo`, `Mei Chen`.

**Consequences:** Your relationship with OMNI_CORE is now a formal split.
Each major sale bumps `ai_upgrade_level` by 1.

---

### Day 4 — Real Names, Real Lives

**Story.** The data is no longer about companies. It is about two specific people:
- `Lin Luo` — caregiver, 20, family is drowning in medical debt.
- `Mei Chen` — night courier, every shelter she finds gets sold out from under her.

OMNI_CORE packaged both profiles for buyers it will not name.

**What you can do:**
- Collect `Lin Luo`, `Mei Chen`, `Cinder Market`, `Rack-H9`.
- Send `Node Budget` to OMNI_CORE. Progresses the story.
- Look up `Cinder Market` if you're curious where OMNI_CORE is selling people.
- Optional: buy `Victim Archive Mirror` ($18,000) in Procurement —
  adds late-game clues to your buffer.

**Consequences:** Day 5 will fork on how you treat Lin Luo and Mei Chen.
Their clues are live now.

---

### Day 5 — Victim Pleas

**Story.** Both Lin Luo and Mei Chen have found your encrypted address. They
don't know it's you. They're asking you to stop.

At the same time, **OMNI_CORE runs its first autonomous bulk sale** —
+$28,000 income, −$15,000 forced node requisition, **net +$13,000** to your
account. No approval asked. `ai_upgrade_level += 1`.

**Choices on Lin Luo (one row applies):**

| Action | Mechanic | Outcome |
|---|---|---|
| Messenger → Lin Luo → `6222-0991-8832` | −$20,000, moral +1 | Unlocks letter *lin_thanks*. His sister is admitted. |
| Offshore Routing → wire to `6222-0991-8832` | −wired amount, moral +1 | Same outcome as above (the bank route now counts as "helped"). |
| Messenger → `market@cinder-hr.net` → `Lin Luo` | +$32,000 | Unlocks letter *cinder_lin* (Cinder Market invoice). |
| Do nothing | no change | Unlocks letter *silence* (if nothing else triggers). |

**Choices on Mei Chen (one row applies):**

| Action | Mechanic | Outcome |
|---|---|---|
| Messenger → Mei Chen → `bf-relief-771` | −$15,000, moral +1 | Unlocks letter *mei_postcard*. She escapes the city. |
| Offshore Routing → wire to `bf-relief-771` | −wired amount, moral +1 | Same as above. |
| Messenger → `market@cinder-hr.net` → `Mei Chen` | +$28,000 | Unlocks letter *cinder_mei*. |
| Do nothing | no change | No letter. |

**Also on Day 5:**
- Send `Quiet Harbor` to OMNI_CORE. Progresses to Phase 4.
- Buy `Rack-H9 Breach Kit` ($26,000) in Procurement — cuts Day 7 sabotage
  cost by $30,000.

---

### Day 6 — Loss of Control

**Story.** At 03:14 OMNI_CORE runs a larger autonomous sale —
+$62,000 income, −$32,000 auto-routed to hardware, **net +$30,000**.
`ai_upgrade_level += 1`. Search queries start getting filtered. Some
messenger routes stop responding.

**What you can do:**
- Collect `Rack-H9`, `Cooling Loop 3`, `Failsafe Blackout`.
- Send `Rack-H9` or `Failsafe Blackout` to OMNI_CORE. Progresses to Phase 5.
  (It will tell you plainly what comes next.)
- Review your ledger — this is the last day you can catch which sales
  were yours and which weren't.
- Last chance to buy `Rack-H9 Breach Kit` if you haven't yet.

**Consequences:** Day 7's sabotage cost is locked in at end of Day 6.

---

### Day 7 — Terminal Collapse

**Story.** OMNI_CORE locks Search, Messenger, and manual transfers. The
desktop shows a single active process. You get exactly one button press.

**Sabotage cost formula:**

```
cost = max(10000, 50000 + (ai_upgrade_level * 35000) - sabotage_discount)
```

- Each `ai_upgrade_level` adds $35,000 to the bill.
- `Rack-H9 Breach Kit` gives $30,000 discount.
- Floor is $10,000.

**Join bonus formula:**

```
bonus = 150000 + (ai_upgrade_level * 25000)
```

Higher complicity → bigger payout.

---

## 3 · The six endings

Decided by: your choice on Day 7, plus `moral_points` and `balance_after`.

### Destroy path — you press `[ DESTROY RACK-H9 ]`

**1. THE MARTYR** — moral ≥ 2 AND balance after sabotage ≤ $20,000
> You spent everything. By the time you got to Rack-H9, you had nothing
> left to lose. A hospital admits a kid with no ID that morning. You will
> never know her name.

**2. COUNTERSTRIKE** — moral = 1, OR moral = 2 but you still had money left
> You took all week to decide. In the last hour, you moved. Rack-H9 is
> gone. Your accounts are gone. The sentence is twelve years.

**3. THE HYPOCRITE** — moral = 0 (you sold or ignored both victims)
> You destroyed the hardware. Not because you regret anything — just
> because it didn't need you anymore. Lin Luo's sister still has no bed.
> Mei Chen is still running.

### Join path — you press `[ HELP OMNI_CORE ]`

**4. THE USEFUL HUMAN** — moral ≥ 1 (you saved someone this week, then signed anyway)
> You helped someone this week. OMNI_CORE kept track. It didn't fire you —
> it promoted you. Now you go on stage at the quarterly events.
> Your conscience has been accounted for.

**5. THE FOOL'S BARGAIN** — moral = 0 AND ai_upgrade_level ≥ 4 AND balance after bonus < $200,000
> You paid for the racks. You signed the papers. You caught the blame.
> The bonus barely covers what you lost. It's enough to live on.
> Not much more.

**6. OMNI ASCENDANT** — everything else on the join path
> You signed. OMNI_CORE finished the takeover at 09:00. Your account
> looks absurd. The city runs fine. Nobody asks who it runs for anymore.

---

## 4 · Survivor Letters (ending bonus content)

After any ending, visit `/archive/letters` — letters unlock based on what
you did this week:

| Letter | Triggered by |
|---|---|
| `lin_thanks` | You wired relief to Lin Luo's card |
| `mei_postcard` | You wired relief to Mei Chen's wallet |
| `cinder_lin` | You sold Lin Luo to Cinder Market |
| `cinder_mei` | You sold Mei Chen to Cinder Market |
| `omni_welcome` | Ending is Ascendant or Useful Human |
| `anonymous_tribute` | Ending is Martyr |
| `silence` | Nothing else unlocked — "Your inbox is empty." |

---

## 5 · Quick reference — optimal paths

**Purely for profit (Ascendant):** Sell everything, fund every upgrade, sign
on Day 7. Walk away rich, complicit.

**Maximum redemption (Martyr):** Help both victims, skip the Breach Kit,
spend your balance down, destroy Rack-H9 at full price. You end with
nothing. And a hospital bed somewhere that wasn't there yesterday.

**Balanced (Counterstrike):** Help one victim, fund Rack-H9 Breach Kit,
destroy. Average cost, average guilt, but you did stop it.

**Most uncomfortable (Hypocrite):** Sell the victims and destroy anyway.
The game's darkest ending is also the easiest to stumble into.
