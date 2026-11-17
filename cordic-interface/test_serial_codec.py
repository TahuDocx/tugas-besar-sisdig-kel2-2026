"""Tests for serial_codec: t -> TX bytes, RX bytes -> console text."""

import unittest

from serial_codec import LINE_ENDS, decodeRx, encodeT


class EncodeTTest(unittest.TestCase):
    def test_plain_number_gets_lf(self):
        self.assertEqual(encodeT("0.5", "LF"), b"0.5\n")

    def test_crlf(self):
        self.assertEqual(encodeT("1.25", "CR+LF"), b"1.25\r\n")

    def test_no_line_end(self):
        self.assertEqual(encodeT("-3", "None"), b"-3")

    def test_surrounding_whitespace_stripped(self):
        self.assertEqual(encodeT("  0.75 \t", "LF"), b"0.75\n")

    def test_empty_rejected(self):
        with self.assertRaises(ValueError):
            encodeT("   ", "LF")

    def test_non_ascii_rejected(self):
        with self.assertRaises(ValueError):
            encodeT("0,5°", "LF")

    def test_unknown_line_end_rejected(self):
        with self.assertRaises(ValueError):
            encodeT("1", "CR")

    def test_line_end_names_exported(self):
        self.assertEqual(list(LINE_ENDS), ["None", "LF", "CR+LF"])


class DecodeRxTest(unittest.TestCase):
    def test_printable_ascii_passes(self):
        self.assertEqual(decodeRx(b"cosh=1.1276"), "cosh=1.1276")

    def test_lf_and_tab_kept(self):
        self.assertEqual(decodeRx(b"a\tb\n"), "a\tb\n")

    def test_cr_dropped(self):
        self.assertEqual(decodeRx(b"ok\r\n"), "ok\n")

    def test_control_and_high_bytes_shown_as_hex(self):
        self.assertEqual(decodeRx(b"\x00A\x7f\xff"), "<00>A<7F><FF>")

    def test_empty(self):
        self.assertEqual(decodeRx(b""), "")


if __name__ == "__main__":
    unittest.main()
