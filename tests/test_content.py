import asyncio
import unittest

from fastapi import HTTPException

import main


class ContentPoolTests(unittest.TestCase):
    def test_pool_sizes_and_uniqueness_for_every_level(self):
        expected = {"sentences": 400, "stories": 500, "news": 400, "repeat": 350}
        for language in ("ar", "en"):
            for level in ("easy", "medium", "hard"):
                for game, size in expected.items():
                    with self.subTest(language=language, level=level, game=game):
                        pool = main.CONTENT[language][game][level]
                        self.assertEqual(len(pool), size)
                        self.assertEqual(len(set(pool)), size)

    def test_repeat_words_are_unique_and_each_is_shown_three_times(self):
        for count in (1, 20):
            with self.subTest(count=count):
                result = asyncio.run(main.get_target("repeat", "medium", "ar", count))
                words = result["target"].split()
                self.assertEqual(len(words), count * 3)
                self.assertEqual(result["display"], result["target"])
                self.assertTrue(all(words[i] == words[i + 1] == words[i + 2]
                                    for i in range(0, len(words), 3)))
                self.assertEqual(len(set(words[::3])), count)

    def test_repeat_count_outside_range_is_rejected(self):
        for count in (None, 0, 21):
            with self.subTest(count=count):
                with self.assertRaises(HTTPException) as caught:
                    asyncio.run(main.get_target("repeat", "easy", "ar", count))
                self.assertEqual(caught.exception.status_code, 422)

    def test_regular_game_target_reports_expected_pool_size(self):
        expected = {"sentences": 400, "stories": 500, "news": 400}
        for game, size in expected.items():
            with self.subTest(game=game):
                result = asyncio.run(main.get_target(game, "hard", "ar", None))
                self.assertEqual(result["pool_size"], size)
                self.assertTrue(result["target"])

    def test_home_page_uses_new_brand_and_cairo(self):
        response = asyncio.run(main.serve_app())
        html = response.body.decode()
        self.assertIn("mr.typing", html)
        self.assertIn("Cairo", html)
        self.assertNotIn("Typing Master Pro", html)

    def test_account_and_community_sections_remain_visible_but_disabled(self):
        html = asyncio.run(main.serve_app()).body.decode()
        for tab in ("account", "leaderboard", "community", "vip"):
            with self.subTest(tab=tab):
                self.assertIn(f'data-tab="{tab}"', html)
        self.assertIn("Coming soon", html)
        self.assertIn("قيد التجهيز", html)
        self.assertIn("Sign in", html)
        self.assertIn("Create account", html)
        self.assertIn("<button disabled>", html)
        self.assertIn("لا يوجد شراء", html)

    def test_mobile_layout_uses_dynamic_viewport_and_static_ui_is_translatable(self):
        html = asyncio.run(main.serve_app()).body.decode()
        self.assertIn("100dvh - 87px", html)
        self.assertNotIn("100svh - 87px", html)
        self.assertIn("function applyStaticText()", html)
        self.assertIn("Training data stays on this device", html)


if __name__ == "__main__":
    unittest.main()
