# Pet sitting agent (single agent)

One agent runs the full workflow. **You only reply YES or NO** — twice per booking.

---

## The 7 steps

| Step | Agent / you | What happens |
|------|-------------|----------------|
| 1 | Agent | Read booking inbox daily |
| 2 | Agent | New request → **notify you** (Telegram / email / Mac) |
| 3 | **You** | Check dates → reply **YES** or **NO** |
| 4 | Agent | If YES → email client a **price quote** |
| 5 | Agent | Client accepts → **notify you** |
| 6 | **You** | Reply **YES** → agent updates **bookings** + **public availability** |
| 7 | Agent | 2 days after stay → **feedback email** to client |

---

## Notifications (where you get pinged)

Set `NOTIFY_CHANNEL` in `scripts/.env`:

| Channel | Best for | Setup |
|---------|----------|--------|
| **Telegram** ✅ recommended | Phone alerts, free, easy | 5 min — see below |
| **Email** | If you live in inbox | `NOTIFY_EMAIL` in `.env` |
| **Mac popup** | Only when Mac is on | `NOTIFY_CHANNEL=mac` |

### Telegram setup (~5 minutes)

1. Open Telegram → search **@BotFather** → send `/newbot` → copy the **token**.
2. Open your new bot → tap **Start** → send any message.
3. In `scripts/.env` set `TELEGRAM_BOT_TOKEN=...`
4. Run: `python3 pet-sitting/scripts/telegram-chat-id.py`
5. Copy the chat id into `TELEGRAM_CHAT_ID=...`
6. Set `NOTIFY_CHANNEL=telegram`

You will get messages like:

> **Pet sitting — your decision**  
> New enquiry from Ines  
> Pet: Dog · Zelda  
> Dates: 2026-06-14 – 2026-06-24  
> Reply YES to send a quote  
> Reply NO to decline

Reply in this Cursor chat (or email) with YES/NO — the agent acts on it.

### WhatsApp?

Not built in yet. WhatsApp needs a paid Business API (Meta or Twilio). **Telegram is the practical choice** while you're starting up. We can add WhatsApp later if you need it.

---

## Daily run

```bash
python3 pet-sitting/scripts/agent-daily.py
```

Schedule once per morning via `scripts/com.pawsstay.inquiry-check.plist` (Mac) or a Cursor Automation.

---

## What you do

| When you get… | You reply |
|---------------|-----------|
| New enquiry notification | **YES** (send quote) or **NO** (decline) |
| Client accepted notification | **YES** (confirm booking) or **NO** |

Nothing else.

---

## Data & live calendar

**Owner workflow (primary):** open the public link → **Owner login** → tap days on the calendar (or use Bookings / Pricing). Changes save automatically for all clients. No Netlify dashboard, no `.env`, no redeploy.

**Agent fallback (if owner asks in chat):** run `python3 pet-sitting/scripts/update-store.py availability YYYY-MM-DD unavailable` (uses `storeWriteKey` from `config.js`).

Live sync is already on Netlify. **Never tell the owner to open Netlify** for calendar changes. For code/UI updates, run `python3 pet-sitting/scripts/deploy-netlify.py` (needs `NETLIFY_AUTH_TOKEN` in `scripts/.env` once).

**Status flow:**  
`awaiting_owner_dates` → `quote_sent` → `client_accepted` → `confirmed`

Never block calendar dates before your second YES.

---

## Rates (GBP)

Off-peak: visit £13, overnight £25  
Peak (Sat–Sun): visit £14, overnight £27  
Super peak (bank holidays + 24 Dec–1 Jan): visit £16, overnight £30  
Extra pets: +£5 visit / +£8 overnight

---

## Config

- `config.js` — `businessName`, `bookingEmail`, `ownerNotifyEmail`
- `scripts/.env` — Gmail, Telegram, notification channel
