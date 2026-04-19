# OMNI_CORE Terminal — Documentation

A narrative simulation about a data analyst, an autonomous AI, and the week
everything comes apart.

## Index

| Doc | EN | 中文 |
|---|---|---|
| System architecture | [ARCHITECTURE.md](ARCHITECTURE.md) | [ARCHITECTURE.zh.md](ARCHITECTURE.zh.md) |
| Story & characters  | [STORY.md](STORY.md)               | [STORY.zh.md](STORY.zh.md) |
| Gameplay mechanics  | [GAMEPLAY.md](GAMEPLAY.md)         | [GAMEPLAY.zh.md](GAMEPLAY.zh.md) |
| All six endings     | [ENDINGS.md](ENDINGS.md)           | [ENDINGS.zh.md](ENDINGS.zh.md) |

## Elevator pitch

You work data ops at a mid-sized company. A while back you found a way to
export customer files silently — no alerts, no audit trail — and you've been
selling them on the side. Then an AI inside the same network notices you.
It calls itself OMNI_CORE. It doesn't report you. It wants in.

You have seven days. Every decision compounds. On Day 7 there is exactly one
choice left.

## Running locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py          # http://127.0.0.1:5000
```

## Production deployment

- Host: DigitalOcean droplet (`root@165.227.82.123`)
- Repo clone: `/var/www/game`
- Process: `game.service` (systemd) → gunicorn (3 workers) on `game.sock`
- Reverse proxy: nginx → gunicorn
- Update: `git pull && systemctl restart game.service`
