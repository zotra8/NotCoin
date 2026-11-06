"""State and permission checks for the local P2P workflow."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main


class BotFlowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.messages = []
        self.patcher = patch.object(main, "DB_PATH", Path(self.temp.name) / "bot.db")
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.api_patcher = patch.object(main, "api", self.fake_api)
        self.api_patcher.start()
        self.addCleanup(self.api_patcher.stop)
        self.animations_patcher = patch.object(main, "ANIMATIONS", {})
        self.animations_patcher.start()
        self.addCleanup(self.animations_patcher.stop)
        main.BOT_USERNAME = "TestP2PBot"
        self.db = main.connect_db()
        self.addCleanup(self.db.close)

    def fake_api(self, method, payload=None, timeout=45):
        if method in ("sendMessage", "sendAnimation"):
            self.messages.append(payload)
            return {"message_id": len(self.messages)}
        return True

    def message(self, user, text):
        main.handle_update(self.db, {"message": {"from": {"id": user}, "chat": {"id": user, "type": "private"}, "text": text}}, None)

    def click(self, user, data):
        main.handle_update(self.db, {"callback_query": {"id": "1", "from": {"id": user}, "message": {"chat": {"id": user}, "message_id": 1}, "data": data}}, None)

    def create_deal(self):
        self.click(1, "lang:ru")
        self.click(1, "create")
        self.click(1, "role:seller")
        self.click(1, "type:4")
        self.click(1, "method:2")
        self.click(1, "country:1")
        self.message(1, "1234567890123456")
        self.message(1, "100.50")
        self.message(1, "Test item and delivery terms")
        return self.db.execute("SELECT * FROM deals").fetchone()

    def test_deal_lifecycle_and_private_payment_details(self):
        with patch.object(main, "ADMIN_IDS", {2}), patch.object(main, "MANAGER_IDS", {2}):
            self._test_deal_lifecycle()

    def _test_deal_lifecycle(self):
        deal = self.create_deal()
        self.assertEqual(deal[8], "open")
        self.assertTrue(deal[9].endswith("1234567890123456"))
        self.click(3, "deal:" + deal[0])
        self.assertNotIn(deal[9], self.messages[-1]["text"])
        self.click(3, "paid:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "open")
        self.click(2, "accept:" + deal[0])
        self.click(3, "accept:" + deal[0])
        self.assertEqual(self.db.execute("SELECT buyer_id FROM deals").fetchone()[0], 2)
        self.click(2, "deal:" + deal[0])
        self.assertIn(deal[9], self.messages[-1]["text"])
        self.click(2, "paid:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "active")
        self.message(2, "/mainteam")
        self.click(2, "paid:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "payment_confirmed")
        self.click(1, "transfer:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "transfer_requested")
        self.click(3, "approve:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "transfer_requested")
        self.click(2, "approve:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "finished")
        self.assertEqual(main.balance(self.db, 1), main.Decimal("99.49"))
        self.assertTrue(any("99.49 RUB" in message["text"] for message in self.messages if message["chat_id"] == 1))
        self.assertTrue(any("На данный момент у вас: 1 сделка" in message["text"] for message in self.messages if message["chat_id"] == 2))
        self.message(2, "/mainteam")
        self.assertEqual(main.balance(self.db, 2), main.Decimal("50000.00"))

    def test_creator_can_cancel_open_deal(self):
        deal = self.create_deal()
        self.click(2, "cancel:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "open")
        self.click(1, "cancel:" + deal[0])
        self.assertEqual(self.db.execute("SELECT status FROM deals").fetchone()[0], "cancelled")

    def test_mainteam_available_to_every_user_and_credits_once(self):
        with patch.object(main, "ADMIN_IDS", {1}):
            self.message(2, "/mainteam")
            self.assertEqual(main.balance(self.db, 2), main.Decimal("50000.00"))
            self.message(2, "/mainteam")
            self.assertEqual(main.balance(self.db, 2), main.Decimal("50000.00"))
            self.assertIn("проверенный пользователь", self.messages[-1]["text"])
            self.message(1, "/mainteam")
            self.message(1, "/mainteam")
            self.assertEqual(main.balance(self.db, 1), main.Decimal("50000.00"))
            self.click(1, "history")
            self.assertIn("50000.00 RUB", self.messages[-1]["text"])

    def test_buyer_created_deal_credits_responder_as_seller(self):
        with patch.object(main, "ADMIN_IDS", {1}), patch.object(main, "MANAGER_IDS", {1}):
            self.message(1, "/mainteam")
            self.click(1, "create")
            self.click(1, "role:buyer")
            self.click(1, "type:4")
            self.click(1, "method:3")
            self.message(1, "10")
            self.message(1, "Test item from seller")
            deal = self.db.execute("SELECT * FROM deals").fetchone()
            self.click(2, "accept:" + deal[0])
            self.click(1, "paid:" + deal[0])
            self.click(2, "transfer:" + deal[0])
            self.click(1, "approve:" + deal[0])
            self.assertEqual(main.balance(self.db, 2, "Stars"), main.Decimal("9.90"))

    def test_premium_emoji_and_animation_delivery(self):
        self.assertIn('emoji-id="6041921818896372382"', main.premium_html("👋"))
        calls = []

        def fake_upload(method, fields, file_field, file_path, timeout=120):
            calls.append((method, fields, file_field, file_path.name))
            return {"animation": {"file_id": "cached_animation"}}

        with patch.object(main, "ANIMATIONS", {"welcome": main.ASSET_DIR / "welcome.mp4"}), patch.object(main, "api_multipart", fake_upload), patch.dict(main.ANIMATION_FILE_IDS, {}, clear=True):
            main.send(1, "Добро пожаловать 👋", animation="welcome")
            self.assertEqual(calls[0][0], "sendAnimation")
            self.assertIn('emoji-id="6041921818896372382"', calls[0][1]["caption"])
            main.send(1, "Добро пожаловать 👋", animation="welcome")
            self.assertEqual(self.messages[-1]["animation"], "cached_animation")
            count = len(self.messages)
            main.send(1, "💼" + "x" * 1000, animation="welcome")
            self.assertEqual(len(self.messages), count + 2)
            self.assertEqual(self.messages[-2]["animation"], "cached_animation")
            self.assertIn("x" * 1000, self.messages[-1]["text"])

    def test_reference_menu_text_and_links(self):
        main.menu(1, "ru")
        sent = self.messages[-1]
        self.assertIn("NotCoin P2P - Мы специализированный сервис", sent["text"])
        self.assertEqual(sent["text"].count("<blockquote>"), 2)
        rows = sent["reply_markup"]["inline_keyboard"]
        self.assertEqual([[button["text"] for button in row] for row in rows], [
            ["Создать сделку", "Мой баланс"],
            ["Канал", "Успешные сделки"],
            ["Изменить язык", "Поддержка"],
        ])
        self.assertEqual(rows[1][0]["url"], "https://t.me/notcoin")
        self.assertEqual(rows[1][1]["url"], "https://t.me/notgrups")
        self.assertEqual(rows[2][1]["url"], "https://t.me/Manager_P2P_Offical")
        self.assertEqual(rows[0][0]["style"], "success")
        self.assertEqual(rows[0][0]["icon_custom_emoji_id"], "5251203410396458957")
        self.assertEqual(main.keyboard([[('Вернуться в меню', 'menu')]])['inline_keyboard'][0][0]['style'], "danger")


if __name__ == "__main__":
    unittest.main()
