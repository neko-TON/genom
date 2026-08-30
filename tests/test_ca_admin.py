"""Чистые функции CA-админки: парсинг конфига, валидация, секрет."""
import unittest

from ca_lib import check_secret, parse_edge_config, validate_ca


class TestParseEdgeConfig(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(
            parse_edge_config("https://edge-config.vercel.com/ecfg_abc?token=tok1"),
            ("ecfg_abc", "tok1"))

    def test_garbage(self):
        for bad in (None, "", "ftp://x/y?token=1",
                    "https://edge-config.vercel.com/?token=1",
                    "https://edge-config.vercel.com/ecfg_abc"):
            self.assertIsNone(parse_edge_config(bad), bad)


class TestValidateCa(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(validate_ca("test"), "test")
        self.assertEqual(validate_ca("  0xAbC123  "), "0xAbC123")
        self.assertEqual(validate_ca(""), "")
        self.assertEqual(validate_ca("x" * 80), "x" * 80)

    def test_bad(self):
        self.assertIsNone(validate_ca("x" * 81))
        self.assertIsNone(validate_ca("тест"))
        self.assertIsNone(validate_ca("a\nb"))
        self.assertIsNone(validate_ca(None))
        self.assertIsNone(validate_ca(123))


class TestCheckSecret(unittest.TestCase):
    def test_match(self):
        self.assertTrue(check_secret("s3cret", "s3cret"))

    def test_mismatch_or_empty(self):
        self.assertFalse(check_secret("wrong", "s3cret"))
        self.assertFalse(check_secret("s3cret", ""))
        self.assertFalse(check_secret(None, "s3cret"))


if __name__ == "__main__":
    unittest.main()
