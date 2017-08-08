import unittest

from z80tools import decode_full, P_IMMEDIATE_16, P_DISPLACEMENT, P_CONDITION, COND_NZ
from rom import Rom

def is_unconditionnal_jump(fully_decoded):
    mnemonic, p1, v1, p2, v2, size = fully_decoded
    return ((mnemonic in ("JP", "JR") and p1 == None and (p2 == P_IMMEDIATE_16 or p2 == P_DISPLACEMENT))
            or
            (mnemonic in ("RET", "RETI", "RETN") and p1 == None and p2 == None))



def find_next_unconditionnal_jump(memory, start):
    last_address = len(memory)
    pc = start
    decoded_instructions = []
    while pc < last_address:
        fully_decoded = decode_full(memory[pc:])
        decoded_instructions.append((pc, fully_decoded))
        pc += fully_decoded[-1]

        if is_unconditionnal_jump(fully_decoded):
            break
            
    return decoded_instructions, (pc - start)


def adjust_relative_displacements(instructions):
    new_instructions = []
    for pc, instruction in instructions:
        mnemonic, p1, v1, p2, v2, size = instruction
        if mnemonic in ("JR", "DJNZ") and p2 == P_DISPLACEMENT:
            instruction = mnemonic, p1, v1, P_IMMEDIATE_16, pc + v2 + size, size

        new_instructions.append((pc, instruction))

    return new_instructions


def collect_address_references(instructions):
    references = []
    for pc, instruction in instructions:
        mnemonic, p1, v1, p2, v2, size = instruction
        if mnemonic in ("JP", "JR", "DJNZ", "CALL", "RST") and p2 == P_IMMEDIATE_16:
            references.append(v2)

    return references


def mark_all_code_regions(rom, starting_addresses):
    while len(starting_addresses) > 0:
        start = starting_addresses[0]
        starting_addresses = starting_addresses[1:]

        if rom.get_type(start) == 'unknown':
            instructions, total_size = find_next_unconditionnal_jump(rom.memory, start)
            rom.mark_code(start, start + total_size)

            instructions = adjust_relative_displacements(instructions)

            for instruction in instructions:
                address, decoded = instruction
                rom.add_content(address, decoded)

            references = collect_address_references(instructions)

            references = [r for r in references if rom.get_type(r) == 'unknown']

            starting_addresses.extend(references)

    return rom


def mark_all_data_regions(rom):
    latest_data_begin = 0
    new_regions = []
    for r in sorted(rom.ranges):
        (begin, end), t = r
        if begin > latest_data_begin:
            new_region = ((latest_data_begin, begin), 'data')
            new_regions.append(new_region)

        latest_data_begin = end

    for r in new_regions:
        (begin, end), t = r
        rom.mark_data(begin, end)
        rom.add_content(begin, rom.memory[begin:end])

    return rom


class RomCodeTestCase(unittest.TestCase):
    def test_from_a_start_point_go_to_next_unconditional_jump(self):
        # Memory content reads as
        # JP 0x0009
        # DEFM "PRINT", 0
        # JP 0x0000

        memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

        start = 0x0000
        instructions, total_size = find_next_unconditionnal_jump(memory, start)
        self.assertEqual(1, len(instructions))
        self.assertEqual(3, total_size)

        address, last_instruction = instructions[-1]
        size_of_last_instruction = last_instruction[-1]
        self.assertEqual(3, size_of_last_instruction)

    def test_adjust_relative_displacements_for_jr_and_djnz(self):
        instructions = [(0x1000, ('JP', None, None, P_IMMEDIATE_16, 9, 3)),
                        (0x1003, ('DJNZ', None, None, P_DISPLACEMENT, -5, 2)),
                        (0x1005, ('JR', P_CONDITION, COND_NZ, P_DISPLACEMENT, 4, 2))]

        new_instructions = adjust_relative_displacements(instructions)

        self.assertEqual(0x0009, new_instructions[0][1][4])
        self.assertEqual(0x1000, new_instructions[1][1][4])
        self.assertEqual(0x100B, new_instructions[2][1][4])

    def test_collect_address_references_from_instrctions(self):
        instructions = [(0x1000, ('JP', None, None, P_IMMEDIATE_16, 9, 3)),
                        (0x1003, ('DJNZ', None, None, P_IMMEDIATE_16, 0x1000, 2)),
                        (0x1005, ('JR', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x100B, 2)),
                        (0x1007, ('CALL', None, None, P_IMMEDIATE_16, 0x2000, 3)),
                        (0x100A, ('RST', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x0038, 1))]

        references = collect_address_references(instructions)

        self.assertEqual(5, len(references))
        self.assertIn(0x0009, references)
        self.assertIn(0x1000, references)
        self.assertIn(0x100B, references)
        self.assertIn(0x2000, references)
        self.assertIn(0x0038, references)


class RomCodeAnalysisProcessTestCase(unittest.TestCase):
    def test_full_analysis(self):
        memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]
        rom = Rom(memory)

        starting_addresses = [0x0000]

        rom = mark_all_code_regions(rom, starting_addresses)

        self.assertEqual(2, len(rom.ranges))
        self.assertEqual(((0, 3), 'code'), rom.ranges[0])
        self.assertEqual(((9, 12), 'code'), rom.ranges[1])

        rom = mark_all_data_regions(rom)
        self.assertEqual(3, len(rom.ranges))
        self.assertEqual(((3, 9), 'data'), rom.ranges[1])

        expected = (0x0000, 'code', ('JP', None, None, P_IMMEDIATE_16, 0x0009, 3))
        found = None

        for content in rom.get_content(0, 3):
            found = content

        self.assertEqual(expected, found)

        expected = (0x0003, 'data', [0x50, 0x52, 0x49, 0x4E, 0x54, 0x00])
        found = None

        for content in rom.get_content(3, 9):
            found = content

        self.assertEqual(expected, found)


if __name__ == '__main__':
    unittest.main()
