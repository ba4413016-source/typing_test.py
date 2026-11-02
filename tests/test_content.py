from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FrontendContractTests(unittest.TestCase):
    def setUp(self):
        self.html = (ROOT / "static/index.html").read_text()

    def test_exactly_five_bottom_tabs_and_matching_pages(self):
        tabs = re.findall(r'data-page="([^"]+)"', self.html)
        self.assertEqual(tabs, ["home", "bot", "community", "messages", "settings"])
        for tab in tabs:
            self.assertIn(f'id="page-{tab}"', self.html)

    def test_brand_and_cairo_remain(self):
        self.assertIn("mr.typing", self.html)
        self.assertIn("Cairo", self.html)
        self.assertNotIn("Typing Master Pro", self.html)

    def test_viewport_does_not_disable_user_zoom(self):
        viewport = re.search(
            r'<meta\s+name="viewport"\s+content="([^"]+)"', self.html
        ).group(1)
        self.assertIn("viewport-fit=cover", viewport)
        self.assertNotIn("user-scalable=no", viewport)
        self.assertNotIn("maximum-scale=1", viewport)
        self.assertNotIn("autofocus", self.html)

    def test_composers_and_target_have_stable_unique_nodes(self):
        for element in (
            "botInput",
            "messageInput",
            "targetText",
            "botLog",
            "messageLog",
        ):
            self.assertEqual(self.html.count(f'id="{element}"'), 1)
        self.assertRegex(self.html, r'id="targetText"[^>]*dir="auto"')

    def test_no_coming_soon_disabled_account_placeholder(self):
        self.assertNotIn("Coming soon", self.html)
        self.assertNotIn("قيد التجهيز", self.html)
        self.assertIn('id="authForm"', self.html)
        self.assertIn('src="/static/app.js"', self.html)

    def test_account_deletion_and_message_policy_are_visible_in_settings(self):
        script = (ROOT / "static/app.js").read_text()
        self.assertIn('data-form="delete-account"', script)
        self.assertIn('method: "DELETE"', script)
        self.assertIn('confirm_username: fd.get("confirm_username")', script)
        self.assertIn("الرسائل التي أرسلتها أو استقبلتها", script)

    def test_social_assets_are_local_valid_svg(self):
        for network in ("instagram", "snapchat", "x"):
            content = (ROOT / f"static/icons/{network}.svg").read_text()
            self.assertIn("<svg", content)
            self.assertNotIn("<script", content.lower())


if __name__ == "__main__":
    unittest.main()
