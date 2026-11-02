import random
import time
import unittest
import unicodedata
import regex

from typing_app.game_engine import (
    _TOPIC_PARTS,
    _corpus_words,
    generate_target,
    score_attempt,
)


class TargetGenerationTests(unittest.TestCase):
    def test_text_games_cover_languages_and_all_levels(self):
        for language in ("ar", "en"):
            for difficulty in ("easy", "medium", "hard"):
                for game in ("sentences", "stories", "news"):
                    with self.subTest(
                        language=language, difficulty=difficulty, game=game
                    ):
                        result = generate_target(
                            game, difficulty, language, rng=random.Random(314)
                        )
                        self.assertTrue(result.target)
                        self.assertEqual(result.display, result.target)
                        self.assertEqual(result.language, language)
                        self.assertEqual(result.difficulty, difficulty)
                        self.assertIsNone(result.word_count)
                        self.assertLessEqual(len(result.target), 600)
                        self.assertTrue(result.metadata["synthetic"])
                        if language == "ar":
                            self.assertTrue(regex.search(r"\p{Arabic}", result.target))
                        else:
                            self.assertTrue(regex.search(r"\p{Latin}", result.target))
                        if game == "news":
                            self.assertFalse(result.metadata["factual_news"])

    def test_explicit_topics_always_start_with_a_matching_topic_scene(self):
        for topic in _TOPIC_PARTS:
            for language in ("ar", "en"):
                scenes = _TOPIC_PARTS[topic][language][0]
                for game in ("sentences", "stories", "news"):
                    with self.subTest(topic=topic, language=language, game=game):
                        result = generate_target(
                            game,
                            "easy",
                            language,
                            rng=random.Random(f"{topic}-{language}-{game}"),
                            topic=topic,
                        )
                        self.assertEqual(result.metadata["topic"], topic)
                        self.assertTrue(
                            any(result.target.startswith(scene) for scene in scenes)
                        )

    def test_repeat_display_and_target_at_minimum_and_maximum(self):
        for language in ("ar", "en"):
            for count in (1, 20):
                with self.subTest(language=language, count=count):
                    result = generate_target(
                        "repeat", "medium", language, count, random.Random(1000 + count)
                    )
                    words = result.target.split()
                    self.assertEqual(len(words), count * 3)
                    unique = words[::3]
                    self.assertEqual(len(set(unique)), count)
                    self.assertTrue(
                        all(
                            words[i : i + 3] == [words[i]] * 3
                            for i in range(0, len(words), 3)
                        )
                    )
                    expected_display = " · ".join(f"({word})3" for word in unique)
                    self.assertEqual(result.display, expected_display)
                    self.assertEqual(result.word_count, count)

    def test_repeat_level_lengths_target_limit_and_variation_for_every_language(self):
        limits = {"easy": (2, 4), "medium": (5, 7), "hard": (8, 9)}
        for language in ("ar", "en"):
            for difficulty, (minimum, maximum) in limits.items():
                with self.subTest(language=language, difficulty=difficulty):
                    result = generate_target(
                        "repeat",
                        difficulty,
                        language,
                        20,
                        random.Random(f"{language}-{difficulty}"),
                    )
                    words = result.target.split()
                    unique = words[::3]
                    self.assertEqual(len(unique), 20)
                    self.assertTrue(
                        all(minimum <= len(word) <= maximum for word in unique)
                    )
                    self.assertLessEqual(len(result.target), 600)
                    self.assertGreaterEqual(len({len(word) for word in unique}), 2)

    def test_corpus_words_are_script_letters_with_optional_marks_not_digits(self):
        for language, script in (("ar", r"\p{Arabic}"), ("en", r"\p{Latin}")):
            words = _corpus_words(language)
            self.assertTrue(words)
            for word in words:
                self.assertTrue(
                    regex.fullmatch(
                        script + r"[\p{L}\p{M}]*", word, flags=regex.VERSION1
                    )
                )
                self.assertTrue(word[0].isalpha())
                self.assertTrue(
                    all(
                        char.isalpha() or unicodedata.category(char).startswith("M")
                        for char in word
                    )
                )

    def test_seeded_generation_has_many_distinct_results(self):
        rng = random.Random(982_451_653)
        targets = [
            generate_target("sentences", "easy", "en", rng=rng).target
            for _ in range(500)
        ]
        self.assertGreaterEqual(len(set(targets)), 490)

    def test_repeat_count_is_required_and_bounded(self):
        for count in (None, 0, -1, 21, 1.5, True):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    generate_target("repeat", "easy", "ar", count)

    def test_count_is_rejected_for_text_games(self):
        with self.assertRaises(ValueError):
            generate_target("stories", "easy", "en", 1)

    def test_invalid_game_level_language_and_rng_are_rejected(self):
        for args in (
            ("unknown", "easy", "en"),
            ("sentences", "expert", "en"),
            ("sentences", "easy", "fr"),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                generate_target(*args)
        with self.assertRaises(ValueError):
            generate_target("sentences", "easy", "en", rng=object())


class ScoringTests(unittest.TestCase):
    def test_nfc_and_arabic_diacritics_align_by_grapheme(self):
        composed = "café"
        decomposed = unicodedata.normalize("NFD", composed)
        result = score_attempt(composed, decomposed, 60)
        self.assertEqual(result["base_points"], 4)
        self.assertEqual(result["correct_characters"], 4)
        self.assertEqual(result["error_count"], 0)
        self.assertEqual(result["accuracy"], 100.0)

        arabic = "مُدَرِّس"
        same_arabic = unicodedata.normalize("NFD", arabic)
        arabic_result = score_attempt(arabic, same_arabic, 60)
        self.assertEqual(
            arabic_result["correct_characters"], len(regex.findall(r"\X", arabic))
        )
        self.assertEqual(arabic_result["error_count"], 0)

    def test_letter_substitution_is_one_error_costing_two(self):
        result = score_attempt("abc", "axc", 60)
        self.assertEqual(result["penalty"], 2)
        self.assertEqual(result["points"], 1)
        self.assertEqual(result["error_count"], 1)
        self.assertEqual(result["letter_errors"], 1)
        self.assertEqual(result["correct_characters"], 2)
        self.assertEqual(
            result["errors"],
            [
                {
                    "operation": "substitute",
                    "expected": "b",
                    "actual": "x",
                    "position": 2,
                }
            ],
        )

    def test_spacing_and_punctuation_edits_each_cost_one(self):
        spacing = score_attempt("a b", "ab", 30)
        self.assertEqual(spacing["penalty"], 1)
        self.assertEqual(spacing["spacing_errors"], 1)
        self.assertEqual(spacing["error_count"], 1)
        self.assertEqual(spacing["errors"][0]["operation"], "delete")

        punctuation = score_attempt("a!", "a?", 30)
        self.assertEqual(punctuation["penalty"], 1)
        self.assertEqual(punctuation["punctuation_errors"], 1)
        self.assertEqual(punctuation["errors"][0]["operation"], "substitute")

    def test_letter_insertion_and_deletion_cost_two_as_single_operations(self):
        insertion = score_attempt("cat", "cart", 60)
        self.assertEqual(
            (
                insertion["error_count"],
                insertion["penalty"],
                insertion["letter_errors"],
            ),
            (1, 2, 1),
        )
        self.assertEqual(insertion["errors"][0]["operation"], "insert")
        deletion = score_attempt("cart", "cat", 60)
        self.assertEqual(
            (deletion["error_count"], deletion["penalty"], deletion["letter_errors"]),
            (1, 2, 1),
        )
        self.assertEqual(deletion["errors"][0]["operation"], "delete")

    def test_unicode_letters_and_numbers_keep_weighted_penalties(self):
        arabic = score_attempt("ا١", "ب٢", 30)
        self.assertEqual(
            (arabic["penalty"], arabic["letter_errors"], arabic["points"]), (4, 2, 0)
        )
        emoji = score_attempt("🙂", "🙃", 30)
        self.assertEqual((emoji["penalty"], emoji["punctuation_errors"]), (1, 1))

    def test_incomplete_and_overlong_attempts_are_scored_without_negative_points(self):
        incomplete = score_attempt("hello", "he", 60)
        self.assertEqual(incomplete["correct_characters"], 2)
        self.assertEqual(incomplete["points"], 0)
        self.assertEqual(incomplete["penalty"], 6)
        empty = score_attempt("abc", "", 60)
        self.assertEqual(empty["points"], 0)
        self.assertEqual(empty["penalty"], 6)
        overlong = score_attempt("a", "abcd", 60)
        self.assertEqual(overlong["points"], 0)
        self.assertEqual(overlong["error_count"], 3)

    def test_accuracy_and_wpm_use_correct_graphemes_and_elapsed_minutes(self):
        result = score_attempt("abcdefghij", "abcdefgXij", 60)
        self.assertEqual(result["wpm"], 9 / 5)
        self.assertEqual(result["accuracy"], 90.0)
        faster = score_attempt("abcdefghij", "abcdefghij", 30)
        self.assertEqual(faster["wpm"], 4.0)

    def test_errors_are_capped_and_more_errors_reports_remainder(self):
        result = score_attempt("a" * 30, "b" * 30, 60)
        self.assertEqual(result["error_count"], 30)
        self.assertEqual(len(result["errors"]), 12)
        self.assertEqual(result["more_errors"], 18)

    def test_elapsed_and_text_size_limits(self):
        for elapsed in (0, -1, float("inf"), float("nan")):
            with self.subTest(elapsed=elapsed), self.assertRaises(ValueError):
                score_attempt("a", "a", elapsed)
        with self.assertRaises(ValueError):
            score_attempt("a" * 601, "", 1)
        with self.assertRaises(ValueError):
            score_attempt("", "a" * 1201, 1)

    def test_maximum_size_alignment_completes_within_reasonable_time(self):
        expected = "a" * 600
        typed = "b" * 1200
        start = time.perf_counter()
        result = score_attempt(expected, typed, 60)
        elapsed = time.perf_counter() - start
        self.assertEqual(result["base_points"], 600)
        self.assertEqual(result["error_count"], 1200)
        self.assertLess(elapsed, 5.0, f"600x1200 alignment took {elapsed:.3f}s")


if __name__ == "__main__":
    unittest.main()
