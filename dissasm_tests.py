from dissasm import get_data_skip_regions, _split_data_into_segments, _apply_null_termination, print_data
from rom import Rom

import io
import sys
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


class PrintDataEmptyTestCase(unittest.TestCase):
    """Tests that labels are preserved when content is empty (label at end of content block)."""

    def _capture_print_data(self, memory, address, data, label=None):
        rom = Rom(memory)
        rom.mark_data(0, len(memory))
        rom.add_content(address, data)
        if label:
            rom.name_label(address, label)
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_data(rom, address, data, {"hex_prefix": "$"})
        finally:
            sys.stdout = sys.__stdout__
        return captured.getvalue()

    def test_label_on_non_empty_data_is_printed(self):
        output = self._capture_print_data(bytes(10), 0, b"\x01\x02", label="my_label")
        self.assertIn("my_label:", output)

    def test_label_on_empty_data_is_still_printed(self):
        output = self._capture_print_data(bytes(10), 0, b"", label="boundary_label")
        self.assertIn("boundary_label:", output)

    def test_no_label_on_empty_data_produces_no_output(self):
        output = self._capture_print_data(bytes(10), 0, b"")
        self.assertEqual("", output.strip())

    def test_split_at_end_of_content_creates_empty_content_with_visible_label(self):
        """When a label is placed exactly at the end of a content block, it must appear inline."""
        rom = Rom(bytes(20))
        rom.mark_data(0, 20)
        rom.add_content(0, bytes(range(8)))
        rom.name_label(8, "end_boundary")
        # After split: content[0]=8 bytes, content[8]=b""
        _, _, data_at_8 = rom.get_content_at(8)
        self.assertEqual(b"", data_at_8)
        # The label must still appear in output
        captured = io.StringIO()
        sys.stdout = captured
        try:
            print_data(rom, 8, b"", {"hex_prefix": "$"})
        finally:
            sys.stdout = sys.__stdout__
        self.assertIn("end_boundary:", captured.getvalue())

    def test_label_beyond_rom_boundary_does_not_create_empty_content(self):
        """A label at or beyond the ROM memory boundary should not create empty data content."""
        rom = Rom(bytes(8))  # ROM is 8 bytes: $0000-$0007
        rom.mark_data(0, 8)
        rom.add_content(0, bytes(range(8)))
        # Label at address 8 is exactly at ROM boundary (beyond valid memory)
        rom.name_label(8, "beyond_rom")
        _, _, content = rom.get_content_at(8)
        self.assertIsNone(content)

if __name__ == '__main__':
    unittest.main()
