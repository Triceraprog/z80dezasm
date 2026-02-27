from dissasm import get_data_skip_regions, _split_data_into_segments, _apply_null_termination

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

    def test_vg5000_char_within_string_extends_segment(self):
        # $12 ('é') between printable runs should merge them into one string segment
        data = b"D\x12passement de capacit\x12"
        result = _split_data_into_segments(data)
        self.assertEqual([('string', data)], result)

    def test_vg5000_char_at_start_of_string(self):
        # $12 before printable run: if total printable >= MIN, it's a string
        data = b"\x12puis\x12es"
        result = _split_data_into_segments(data)
        self.assertEqual([('string', data)], result)

    def test_isolated_vg5000_char_without_enough_printable_stays_bytes(self):
        # $12 + 3 printable chars = not enough printable → stays bytes
        data = b"\x12abc"
        result = _split_data_into_segments(data)
        self.assertEqual([('bytes', data)], result)


class ApplyNullTerminationTestCase(unittest.TestCase):
    def test_string_followed_by_null_becomes_nullstring(self):
        segments = [('string', b"Hello"), ('bytes', b"\x00")]
        result = _apply_null_termination(segments)
        self.assertEqual([('nullstring', b"Hello")], result)

    def test_string_followed_by_null_and_more_bytes(self):
        segments = [('string', b"Hello"), ('bytes', b"\x00\x01\x02")]
        result = _apply_null_termination(segments)
        self.assertEqual([('nullstring', b"Hello"), ('bytes', b"\x01\x02")], result)

    def test_string_not_followed_by_null_stays_string(self):
        segments = [('string', b"Hello"), ('bytes', b"\x01\x02")]
        result = _apply_null_termination(segments)
        self.assertEqual([('string', b"Hello"), ('bytes', b"\x01\x02")], result)

    def test_string_at_end_stays_string(self):
        segments = [('string', b"Hello")]
        result = _apply_null_termination(segments)
        self.assertEqual([('string', b"Hello")], result)

    def test_bytes_unaffected(self):
        segments = [('bytes', b"\x00\x01"), ('string', b"World")]
        result = _apply_null_termination(segments)
        self.assertEqual([('bytes', b"\x00\x01"), ('string', b"World")], result)


if __name__ == '__main__':
    unittest.main()
