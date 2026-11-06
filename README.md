# P2P Telegram bot

The bot has language selection in Russian, English, and Chinese. `/start` opens the menu after language selection; `/language` changes it. The selection is saved in SQLite. The bot loads a custom emoji from `theopenemojis` at startup, with a Unicode fallback if Telegram does not allow it.

Original MP4 animations for the welcome screen, balance, and deal creation are stored in `assets/` and sent as Telegram animations. The other 16 observed custom emoji are embedded in message captions and text by Telegram emoji ID. Long deal captions are split into an animation and a text message so the animation is still shown.

Inline buttons use Telegram's green, red, and blue button styles and the observed custom emoji icons. The welcome message uses two quote blocks; balance and deal notices use bold formatting.

The P2P flow creates a deal by role, item type, payment method, amount, and description. For international card payments it also collects a country and payment details. The creator gets a deep link for the other participant. The creator can cancel an open deal; participants can exchange text via `/message DEAL_ID text`. The buyer confirms payment, the seller marks the item as handed to a manager, and a manager approves receipt. The seller is credited the deal amount less a 1% fee in the bot's virtual ledger. Users can save TON wallet and card/phone details. Menus and form choices are available in Russian, English, and Chinese.

The bot records buyer payment claims and virtual balances only; it cannot verify an external bank transfer or move money or assets. A manager's approval credits the seller 99% of the deal amount and notifies both parties. The balance history is additive and never replaces earlier credits. Withdrawals are disabled until a payout provider is connected.

Requires Python 3.9 or newer; no external packages.

```bash
export BOT_TOKEN='your-bot-token'
python3 main.py
```

For background operation use `bash botctl.sh start`; use `status`, `restart`, or `stop` to manage the process. Logs go to `bot.log`.

Set `BOT_TOKEN` and `ADMIN_IDS` in a private `.env` file or environment. Set `MANAGER_IDS` separately for the users who approve receipt of goods. `/mainteam` is available to every user; it grants verified status and credits 50,000 RUB once per ID. Managers receive approval requests and can list pending approvals with `/pending`. A manager must open the bot at least once before Telegram permits the bot to send them messages. The menu uses this bot's username when creating deal links.

Run workflow checks with `python3 -m unittest -v test_main.py`.

## Save a Telegram user session

Install Telethon 1.x (`python3 -m pip install 'telethon>=1.40,<2'`). Create an app at [my.telegram.org](https://my.telegram.org) to obtain your API ID and API hash, then run:

```bash
python3 save_session.py
```

The script asks for your phone, Telegram login code, and 2FA password when needed. It saves `.secrets/telegram_user.session` locally with owner-only permissions. Do not send this file to anyone or commit it; it grants access to your account.
