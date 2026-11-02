import json
import re
import unittest
from pathlib import Path

from PIL import Image

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
        self.assertRegex(self.html, r'src="/static/app\.js(?:\?[^"]*)?"')

    def test_private_chat_has_challenges_images_themes_and_fullscreen_keyboard_layout(self):
        for control in (
            'id="directChallengeButton"',
            'data-action="direct-challenge"',
            'data-action="open-chat-appearance"',
            'id="messageImageButton"',
            'id="messageImageInput"',
        ):
            self.assertIn(control, self.html)
        for behavior in (
            "openChallengeInvitation",
            "uploadMessageImage",
            "set-chat-background",
            "opponent_username",
            'setProperty("--app-top", "0px")',
        ):
            self.assertIn(behavior, (ROOT / "static/app.js").read_text())
        css = (ROOT / "static/style.css").read_text()
        self.assertIn(".app-screen.dm-open .messages-page", css)
        self.assertIn('data-chat-background="aurora"', css)
        self.assertIn(".message-image", css)

    def test_round_counter_exists_and_private_dom_is_cleared_on_session_reset(self):
        for control in (
            'id="roundCounter"',
            'id="speakRoundButton"',
            'id="soundToggleButton"',
        ):
            self.assertIn(control, self.html)
        self.assertNotIn("${tr(", self.html)
        script = (ROOT / "static/app.js").read_text()
        clear_runtime = re.search(
            r"function clearRuntime\(\) \{(.*?)\n\}", script, re.S
        ).group(1)
        for reset in (
            '$("messageLog").replaceChildren()',
            '$("page-messages").classList.remove("conversation-open")',
            '$("page-community").replaceChildren()',
            '$("botLog").replaceChildren()',
        ):
            self.assertIn(reset, clear_runtime)

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

    def test_bot_and_messages_send_from_keyboard_without_screen_arrows(self):
        script = (ROOT / "static/app.js").read_text()
        for removed_control in (
            'id="botSend"',
            'id="messageSend"',
            'id="stopBotButton"',
            'id="botSettingsButton"',
        ):
            self.assertNotIn(removed_control, self.html)
        self.assertIn('enterkeyhint="send"', self.html)
        self.assertIn('bindKeyboardComposer("botInput")', script)
        self.assertIn('bindKeyboardComposer("messageInput")', script)
        self.assertIn("sentences medium", script)
        self.assertIn('strip.className = "result-strip"', script)
        for metric in (
            "result.wpm",
            "result.accuracy",
            "result.points",
            "result.penalty",
        ):
            self.assertIn(metric, script)
        self.assertNotIn("result.error_count", script)

    def test_stop_during_loading_or_submit_is_deferred(self):
        script = (ROOT / "static/app.js").read_text()
        self.assertIn("stopAfterCurrent: false", script)
        self.assertIn("state.stopAfterCurrent = true", script)
        self.assertIn("else if (state.stopAfterCurrent)", script)
        self.assertIn("await stopBot({ silent: true })", script)

    def test_community_sections_grow_with_content_and_accent_choices_exist(self):
        css = (ROOT / "static/style.css").read_text()
        section_gap = re.search(r"\.section-gap\s*\{([^}]*)\}", css).group(1)
        self.assertNotIn("height", section_gap)
        self.assertIn(".card.section-gap > .section-heading", css)
        for accent in ("ocean", "mint", "rose"):
            self.assertIn(f'data-accent="{accent}"', css)
        self.assertIn('id="prefAccent"', (ROOT / "static/app.js").read_text())
        self.assertIn(".app-screen.dm-open #bottomNav", css)

    def test_live_accuracy_aligns_edits_and_dm_profile_names_can_shrink(self):
        script = (ROOT / "static/app.js").read_text()
        css = (ROOT / "static/style.css").read_text()
        self.assertIn("function scoreLiveText(expectedText, typedText)", script)
        self.assertIn('normalize("NFC")', script)
        self.assertIn("score.accuracy.toFixed(1)", script)
        self.assertIn("<bdi>${who(user)}</bdi>", script)
        self.assertIn(".conversation-profile > span > bdi", css)
        self.assertIn("text-overflow: ellipsis", css)

    def test_pwa_manifest_icons_and_apple_home_screen_metadata(self):
        for tag in (
            '<meta name="apple-mobile-web-app-capable" content="yes" />',
            '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />',
            '<meta name="apple-mobile-web-app-title" content="Typing Test" />',
            '<link rel="apple-touch-icon" href="/apple-touch-icon.png" />',
            '<link rel="manifest" href="/manifest.json" />',
        ):
            self.assertIn(tag, self.html)

        manifest = json.loads((ROOT / "manifest.json").read_text())
        self.assertEqual(manifest["name"], "Typing Test App")
        self.assertEqual(manifest["short_name"], "TypingTest")
        self.assertEqual(manifest["start_url"], "/")
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["background_color"], "#ffffff")
        self.assertEqual(manifest["theme_color"], "#d58ab3")
        expected = {"/icon-192.png": (192, 192), "/icon-512.png": (512, 512)}
        actual = {}
        for item in manifest["icons"]:
            with Image.open(ROOT / item["src"].lstrip("/")) as icon:
                actual[item["src"]] = icon.size
        self.assertEqual(actual, expected)
        with Image.open(ROOT / "apple-touch-icon.png") as icon:
            self.assertEqual(icon.size, (180, 180))

    def test_service_worker_is_registered_and_does_not_cache_private_api(self):
        worker = (ROOT / "sw.js").read_text()
        pwa = (ROOT / "static/pwa.js").read_text()
        self.assertIn(
            'navigator.serviceWorker.register("/sw.js", { scope: "/" })', pwa
        )
        self.assertIn('url.pathname.startsWith("/api/")', worker)
        self.assertIn('url.pathname.startsWith("/media/")', worker)
        self.assertIn('request.mode === "navigate"', worker)
        self.assertIn("self.clients.claim()", worker)

    def test_first_visit_welcome_offers_install_instructions_and_continue(self):
        pwa = (ROOT / "static/pwa.js").read_text()
        self.assertIn('id="welcomeScreen"', self.html)
        self.assertIn('id="installAppButton"', self.html)
        self.assertIn('id="welcomeContinueButton"', self.html)
        self.assertIn('id="installInstructions"', self.html)
        self.assertIn("beforeinstallprompt", pwa)
        self.assertIn("Add to Home Screen", self.html)
        self.assertIn("typing.welcome-seen", pwa)
        self.assertIn("في Safari", pwa)

    def test_bot_chat_uses_full_screen_layout_with_a_return_button(self):
        css = (ROOT / "static/style.css").read_text()
        script = (ROOT / "static/app.js").read_text()
        self.assertIn('id="exitBotButton"', self.html)
        self.assertIn('$("exitBotButton").addEventListener("click", () => setPage("home"))', script)
        self.assertRegex(
            css,
            r"\.app-screen\.bot-active #bottomNav\s*\{\s*display:\s*none;",
        )
        self.assertIn("env(safe-area-inset-top)", css)


if __name__ == "__main__":
    unittest.main()
