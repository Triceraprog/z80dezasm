import unittest
import functools
import itertools


class Rom():
    def __init__(self, memory):
        self.memory = memory
        self.ranges = []
        self.content = {}
        self.labels = {}
        self.comments = {}

    def get_type(self, address):
        r = self.__find_range(address)

        if not r:
            return "unknown"

        return r[1]

    def mark_data(self, begin, end):
        self.__mark_range(begin, end, 'data')

    def mark_code(self, begin, end):
        self.__mark_range(begin, end, 'code')

    def add_content(self, address, content):
        self.content[address] = content

    def get_content(self, begin, end):
        addresses = sorted(self.content.keys())
        addresses = itertools.dropwhile(lambda k: k < begin, addresses)
        addresses = itertools.takewhile(lambda k: k < end, addresses)

        for address in addresses:
            yield address, self.get_type(address), self.content[address]

    def get_content_at(self, address):
        return address, self.get_type(address), self.content.get(address, None)

    def add_labels(self, labels):
        for key, value in labels.items():
            if key in self.labels:
                name, callers = self.labels[key]
                callers = list(sorted(set(callers + value[1])))
                self.labels[key] = name, callers
            else:
                self.labels[key] = value

    def get_label_at(self, address):
        return self.labels.get(address, None)

    def get_labels(self):
        for address in sorted(self.labels.keys()):
            yield address, self.labels[address]

    def name_label(self, address, new_name):
        label = self.labels.get(address, ("", []))
        name, callers = label
        self.labels[address] = new_name, callers

    def add_comment(self, address, tag, comment):
        comments = self.comments.get(address, list())
        comments.append((tag, comment))
        self.comments[address] = comments

    def get_comments_at(self, address):
        return self.comments.get(address, set())

    def __mark_range(self, begin, end, range_type):
        """ begin is inclusive, end is exclusive, to be coherent with range()"""
        existing_range = self.__find_overlapping_range(begin, end)
        new_range = ((begin, end), range_type)

        if not existing_range:
            self.ranges.append(new_range)
        else:
            self.ranges.remove(existing_range)
            ((b_old, e_old), t_old) = existing_range
            ((b_new, e_new), t_new) = new_range

            if b_old < b_new:
                # Existing rang is flowing on the left
                new_old_left = (b_old, b_new), t_old
                self.ranges.append(new_old_left)

            if e_old > e_new:
                # Existing rang is flowing on the right
                new_old_right = (e_new, e_old), t_old
                self.ranges.append(new_old_right)

            self.ranges.append(new_range)

        self.__merge_adjacent_ranges()

    def __find_overlapping_range(self, begin, end):
        for r in sorted(self.ranges):
            limits = r[0]
            if ((begin < limits[0] and end > limits[0])
                or
                (begin >= limits[0] and begin < limits[1])):
                return r

        return None

    def __find_range(self, address):
        found_range = [r for r in self.ranges if address in range(*(r[0]))]
        return found_range[0] if found_range else None

    def __merge_adjacent_ranges(self):
        new_ranges = functools.reduce(merge_neighbours, sorted(self.ranges), [])
        self.ranges = new_ranges


def merge_neighbours(acc, new):
    if len(acc) > 0:
        previous = acc[-1]
        ((b_old, e_old), t_old) = previous
        ((b_new, e_new), t_new) = new

        if t_old == t_new and e_old == b_new:
            return acc[:-1] + [((b_old, e_new), t_new)]
        else:
            return acc + [new]

    else:
        return [new]



class RomTestCase(unittest.TestCase):
    # Memory content reads as
    # JP 0x0009
    # DEFM "PRINT", 0
    # JP 0x0000

    memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

    def test_rom_is_initialized_with_memory_content(self):
        rom = Rom(RomTestCase.memory)
        self.assertEqual("unknown", rom.get_type(0x0004))

    def test_rom_can_be_marked_with_data_range(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_data(0x0003, 0x0009)
        self.assertEqual("data", rom.get_type(0x0004))
        self.assertEqual("unknown", rom.get_type(0x0000))

    def test_rom_can_be_marked_with_code_range(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0001, len(RomTestCase.memory) + 1)
        self.assertEqual("code", rom.get_type(0x0004))
        self.assertEqual("unknown", rom.get_type(0x0000))

    def test_rom_can_be_marked_with_code_then_a_sub_data_range(self):
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

    def test_same_type_ranges_are_merged_if_contiguous(self):
        rom = Rom(RomTestCase.memory)
        rom.mark_code(0x0000, 0x0003)
        rom.mark_code(0x0003, 0x0005)

        self.assertEqual(1, len(rom.ranges))
        self.assertEqual('code', rom.ranges[0][1])

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
        self.assertEqual(all_labels[0], (0x0000, ('jump0000', [16, 32, 64])) )

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
        rom.add_comment(0x0000, 'after', comment1)
        rom.add_comment(0x0000, 'before', comment2)
        rom.add_comment(0x0001, 'online', comment3)

        self.assertEqual(set(), rom.get_comments_at(0x0003))

        result1 = rom.get_comments_at(0x0000)
        self.assertEqual(set([('after', comment1), ('before', comment2)]), set(result1))

        result2 = rom.get_comments_at(0x0001)
        self.assertEqual(set([('online', comment3)]), set(result2))


if __name__ == '__main__':
    unittest.main()
