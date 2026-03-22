from z80dezasm.rom import Rom

import unittest


class RomTestCase(unittest.TestCase):
    # Memory content reads as
    # JP 0x0009
    # DEFM "PRINT", 0
    # JP 0x0000

    memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

    def test_rom_is_initialized_with_memory_content(self):
        rom = Rom(RomTestCase.memory)
        self.assertEqual("unknown", rom.get_type(0x0004))

    def test_rom_can_be_marked_with_data_region(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_data(0x0003, 0x0009)
        self.assertEqual("data", rom.get_type(0x0004))
        self.assertEqual("unknown", rom.get_type(0x0000))

    def test_rom_can_be_marked_with_code_region(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0001, len(RomTestCase.memory) + 1)
        self.assertEqual("code", rom.get_type(0x0004))
        self.assertEqual("unknown", rom.get_type(0x0000))

    def test_rom_can_be_marked_with_code_then_a_sub_data_region(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0000, len(RomTestCase.memory) + 1)
        rom.mark_data(0x0003, 0x0009)
        self.assertEqual("code", rom.get_type(0x0000))
        self.assertEqual("data", rom.get_type(0x0004))

        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0000, len(RomTestCase.memory) + 1)
        rom.mark_data(0x0000, 0x0009)
        self.assertEqual("code", rom.get_type(0x000A))
        self.assertEqual("data", rom.get_type(0x0000))

        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0000, len(RomTestCase.memory) + 1)
        rom.mark_data(0x0004, len(RomTestCase.memory) + 1)
        self.assertEqual("code", rom.get_type(3))
        self.assertEqual("data", rom.get_type(len(RomTestCase.memory)))

    def test_same_type_regions_are_merged_when_marked_if_contiguous(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0000, 0x0003)
        rom.mark_code(0x0003, 0x0005)

        self.assertEqual(1, len(rom.regions))
        self.assertEqual('code', rom.regions[0][1])

    def test_can_add_content_to_an_address(self):
        content1 = "Some untyped content"
        content2 = "Some other content"
        rom = Rom(RomTestCase.memory)
        rom.add_content(0x0004, content1)
        rom.add_content(0x0002, content2)

        found_contents = []
        for c in rom.get_content(0, 9):
            found_contents.append(c)

        self.assertEqual([(0x0002, 'unknown', content2), (0x0004, 'unknown', content1)], found_contents)
        self.assertEqual((0x0002, 'unknown', content2), rom.get_content_at(0x0002))

    def test_can_add_labels_to_rom(self):
        label1 = ('jump0000', [0x0010, 0x0020])
        label2 = ('call0010', [0x0000])
        labels = {0x0000: label1,
                  0x0010: label2}

        rom = Rom(RomTestCase.memory)
        rom.add_labels(labels)

        self.assertIsNone(rom.get_label_at(0x0004))
        self.assertEqual(label1, rom.get_label_at(0x0000))
        self.assertEqual(label2, rom.get_label_at(0x0010))

        label3 = ('jump0000', [0x0020, 0x0040])
        label4 = ('loop0020', [0x0080])
        labels = {0x0000: label3,
                  0x0030: label4}

        rom.add_labels(labels)

        self.assertIsNone(rom.get_label_at(0x0024))

        self.assertEqual(label2, rom.get_label_at(0x0010))
        self.assertEqual(label4, rom.get_label_at(0x0030))

        all_labels = [l for l in rom.get_labels()]
        self.assertEqual(3, len(all_labels))
        self.assertEqual(all_labels[0], (0x0000, ('jump0000', [16, 32, 64])))

    def test_add_a_region_causes_data_content_to_be_split(self):
        content1 = [1, 2, 3, 4]
        rom = Rom(RomTestCase.memory)
        rom.mark_data(0, 4)
        rom.add_content(0x0000, content1)

        label1 = ('data0002', [])
        labels = {0x0002: label1}
        rom.add_labels(labels)

        found_contents = []
        for c in rom.get_content(0, 4):
            found_contents.append(c)

        self.assertEqual(2, len(found_contents))
        self.assertEqual((0, 'data', [1, 2]), found_contents[0])
        self.assertEqual((2, 'data', [3, 4]), found_contents[1])

    def test_can_rename_a_label(self):
        label1 = ('jump0000', [0x0010, 0x0020])
        label2 = ('call0010', [0x0000])
        labels = {0x0000: label1,
                  0x0010: label2}

        rom = Rom(RomTestCase.memory)
        rom.add_labels(labels)

        rom.name_label(0x0000, "Start")

        rom.add_labels({0x0000: ("Start", [0x0030])})
        rom.add_labels({0x0000: ("jump", [0x0040])})
        self.assertEqual(('Start', [0x0010, 0x0020, 0x0030, 0x0040]), rom.get_label_at(0x0000))

    def test_can_add_comments_to_rom(self):
        comment1 = "This is a comment after an address"
        comment2 = "This is a comment before an address"
        comment3 = "This is a comment online"

        rom = Rom(RomTestCase.memory)
        rom.add_comment(0x0000, 'after', comment1, 0x0000)
        rom.add_comment(0x0000, 'before', comment2, 0x0000)
        rom.add_comment(0x0001, 'online', comment3, 0x0001)

        self.assertEqual(list(), rom.get_comments_at(0x0003))

        result1 = rom.get_comments_at(0x0000)
        self.assertEqual({('after', comment1, 0x0000), ('before', comment2, 0x0000)}, set(result1))

        result2 = rom.get_comments_at(0x0001)
        self.assertEqual({('online', comment3, 0x0001)}, set(result2))

    def test_can_add_several_comments_with_the_same_tag(self):
        comment1 = "This is first comment online"
        comment2 = "This is second comment online"

        rom = Rom(RomTestCase.memory)
        rom.add_comment(0x0000, 'right', comment1, 0x0000)
        rom.add_comment(0x0000, 'right', comment2, 0x0000)

        comments = rom.get_comments_at(0x0000)

        self.assertEqual(2, len(comments))


class NoStringRegionTestCase(unittest.TestCase):
    memory = bytes(0x10000)

    def test_address_not_in_any_region_returns_false(self):
        rom = Rom(NoStringRegionTestCase.memory)
        self.assertFalse(rom.is_in_nostring_region(0x1000))

    def test_exact_address_is_in_single_address_region(self):
        rom = Rom(NoStringRegionTestCase.memory)
        rom.add_nostring_region(0x1000, 0x1000)
        self.assertTrue(rom.is_in_nostring_region(0x1000))

    def test_other_address_not_in_single_address_region(self):
        rom = Rom(NoStringRegionTestCase.memory)
        rom.add_nostring_region(0x1000, 0x1000)
        self.assertFalse(rom.is_in_nostring_region(0x1001))

    def test_address_inside_range_is_in_region(self):
        rom = Rom(NoStringRegionTestCase.memory)
        rom.add_nostring_region(0x1000, 0x1FFF)
        self.assertTrue(rom.is_in_nostring_region(0x1500))

    def test_address_at_end_of_range_is_in_region(self):
        rom = Rom(NoStringRegionTestCase.memory)
        rom.add_nostring_region(0x1000, 0x1FFF)
        self.assertTrue(rom.is_in_nostring_region(0x1FFF))

    def test_address_beyond_range_is_not_in_region(self):
        rom = Rom(NoStringRegionTestCase.memory)
        rom.add_nostring_region(0x1000, 0x1FFF)
        self.assertFalse(rom.is_in_nostring_region(0x2000))


if __name__ == '__main__':
    unittest.main()
