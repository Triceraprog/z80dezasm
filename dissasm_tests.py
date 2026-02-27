from dissasm import get_data_skip_regions, _split_data_into_segments

import unittest


class DataSkipRegionsTestCase(unittest.TestCase):
    def test_dataskip_without_size_defaults_to_one(self):
        directives = [(0x1234, ["DATASKIP"])]
        result = get_data_skip_regions(directives)
        self.assertEqual([(0x1234, 1)], result)

    def test_dataskip_with_explicit_size(self):
        directives = [(0x1234, ["DATASKIP(10)"])]
        result = get_data_skip_regions(directives)
        self.assertEqual([(0x1234, 10)], result)


class SplitDataIntoSegmentsTestCase(unittest.TestCase):
    def test_all_bytes_returns_single_bytes_segment(self):
        data = bytes([0x00, 0x01, 0x02])
        self.assertEqual([('bytes', data)], _split_data_into_segments(data))

    def test_short_printable_run_treated_as_bytes(self):
        data = bytes([0x41, 0x42, 0x43])  # "ABC" - only 3 chars, below threshold
        self.assertEqual([('bytes', data)], _split_data_into_segments(data))

    def test_long_enough_printable_run_is_string(self):
        data = b"Hello"
        self.assertEqual([('string', data)], _split_data_into_segments(data))

    def test_mixed_data_splits_correctly(self):
        data = b"\x00\x01Hello\x00"
        result = _split_data_into_segments(data)
        self.assertEqual([('bytes', b"\x00\x01"), ('string', b"Hello"), ('bytes', b"\x00")], result)

    def test_string_followed_by_bytes(self):
        data = b"Hello\x00\x01"
        result = _split_data_into_segments(data)
        self.assertEqual([('string', b"Hello"), ('bytes', b"\x00\x01")], result)

    def test_non_printable_before_string(self):
        data = b"\xff\xfeSyntax error\x00"
        result = _split_data_into_segments(data)
        self.assertEqual([('bytes', b"\xff\xfe"), ('string', b"Syntax error"), ('bytes', b"\x00")], result)

    def test_empty_data_returns_empty(self):
        self.assertEqual([], _split_data_into_segments(b""))

    def test_double_quote_in_string_stays_as_string_segment(self):
        data = b'Say "hello"'
        result = _split_data_into_segments(data)
        self.assertEqual([('string', data)], result)


if __name__ == '__main__':
    unittest.main()
