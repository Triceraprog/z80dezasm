import unittest

from .rom import Rom
from .z80tools import decode_full, \
    P_IMMEDIATE_16, P_DISPLACEMENT, P_CONDITION, COND_NZ, P_REGISTER_PAIR, \
    REG_HL, REG_BC, P_IMMEDIATE_8


def is_unconditional_jump(fully_decoded):
    mnemonic, p1, v1, p2, v2, size = fully_decoded
    return ((mnemonic in ("JP", "JR") and p1 is None and (
            p2 == P_IMMEDIATE_16 or p2 == P_DISPLACEMENT or p2 == P_REGISTER_PAIR))
            or (mnemonic in ("RET", "RETI", "RETN") and p1 is None and p2 is None))


def find_next_unconditional_jump(memory, start, stop=None):
    if stop is None:
        stop = len(memory)

    last_address = min(stop, len(memory))
    pc = start
    decoded_instructions = []
    while pc < last_address:
        fully_decoded = decode_full(memory[pc:])
        decoded_instructions.append((pc, fully_decoded))
        size = fully_decoded[-1]
        pc += size

        if is_unconditional_jump(fully_decoded) or size == 0:
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


def create_labels_with_callers(instructions):
    labels = {}
    for pc, instruction in instructions:
        mnemonic, p1, v1, p2, v2, size = instruction
        if mnemonic in ("JP", "JR", "DJNZ", "CALL", "RST") and p2 is P_IMMEDIATE_16:
            base_name = {"JP": "jump", "JR": "loop", "DJNZ": "loop", "CALL": "call", "RST": "rst"}[mnemonic]

            if base_name == "loop" and v2 > pc:
                base_name = "skip"

            label_name = base_name + "{:>04X}".format(v2)

            if v2 in labels:
                callers = labels[v2][1]
                callers.append(pc)
            else:
                callers = [pc]
            labels[v2] = (label_name, callers)

    return labels


def instructions_too_near(couple):
    pc1, (_, _, _, _, _, size1) = couple[0]
    pc2, (_, _, _, _, _, _) = couple[1]

    return pc1 + size1 > pc2


def detect_partial_instruction_tricks(instructions, memory):
    couples = zip(instructions[:-1], instructions[1:])
    problems = [couple for couple in couples if instructions_too_near(couple)]

    comments = []

    for problem in problems:
        instruction, following = problem

        index = instructions.index(instruction)
        instructions.remove(instruction)

        pc1, (_, _, _, _, _, size) = instruction
        pc2, (_, _, _, _, _, _) = following

        while pc1 < pc2:
            replacement = (pc1, ("DEFB", None, None, P_IMMEDIATE_8, memory[pc1], 1))
            instructions.insert(index, replacement)
            index += 1
            pc1 += 1

        comments.append(instruction)

    return instructions, comments


def find_next_data_region_address(rom, scan_start):
    for (start, stop), t in sorted(rom.regions):
        if start >= scan_start and t == "data":
            return start
    return None


def mark_all_code_regions(rom, starting_addresses):
    while len(starting_addresses) > 0:
        # Never sort the addresses, the process needs to first find
        # all code paths before making new passes
        # starting_addresses = sorted(starting_addresses) <-- This causes wrong paths.

        start = starting_addresses[0]
        starting_addresses = starting_addresses[1:]

        # print(start, hex(start))
        next_data_region_address = find_next_data_region_address(rom, start)
        instructions, total_size = find_next_unconditional_jump(rom.memory, start, next_data_region_address)
        rom.mark_code(start, start + total_size)

        instructions = adjust_relative_displacements(instructions)

        for instruction in instructions:
            address, decoded = instruction

            _, _, previous_content = rom.get_content_at(address)

            if previous_content is None:
                rom.add_content(address, decoded)

        labels = create_labels_with_callers(instructions)

        rom.add_labels(labels)

        references = [r for r in labels.keys()
                      if rom.get_type(r) == 'unknown' and rom.org <= r < len(rom.memory)]

        starting_addresses.extend(references)

    return rom


def mark_all_data_regions(rom):
    latest_data_begin = rom.org
    new_regions = []
    for r in sorted(rom.regions):
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


def mark_declared_data_regions(rom, data_regions):
    for begin, size in data_regions:
        end = begin + size
        rom.mark_data(begin, end)
        rom.add_content(begin, rom.memory[begin:end])

    return rom


def inject_instructions_on_missing_labels(rom):
    for label in rom.get_labels():
        address, label = label
        address, region_type, content = rom.get_content_at(address)
        if not content and rom.org <= address < len(rom.memory):
            fully_decoded = decode_full(rom.memory[address:])
            instructions = [(address, fully_decoded)]

            # As this can result in an instruction size less than the span
            # of memory the previous instruction covers, let's decode a bit
            # further
            size = fully_decoded[-1]
            next_address = address + size

            # Maximum instruction size is 5, we will already have one
            # on the instruction before
            left_to_decode = 4 - size

            while left_to_decode > 0:
                _, _, existing = rom.get_content_at(next_address)
                if isinstance(existing, tuple) and len(existing) == 6:
                    break  # Already has a decoded instruction, don't overwrite
                fully_decoded = decode_full(rom.memory[next_address:])
                instructions.append((next_address, fully_decoded))

                size = fully_decoded[-1]
                if size == 0:
                    break

                next_address += size
                left_to_decode -= size

            instructions = adjust_relative_displacements(instructions)
            for instr_addr, instr in instructions:
                rom.add_content(instr_addr, instr)

    return rom


def detect_partial_instructions(rom):
    instructions = []
    for content in rom.get_content(0, len(rom.memory) + 1):
        if content[1] == 'code':
            instructions.append((content[0], content[2]))

    instructions, comments = detect_partial_instruction_tricks(instructions, rom.memory)

    for instruction in instructions:
        pc, instruction = instruction
        rom.add_content(pc, instruction)

    for comment in comments:
        address, comment = comment
        # rom.add_comment(address, 'online', f'partial instruction trick')
        rom.add_comment(address, 'partial-instruction', comment, address)

    return rom


def analysis(rom, starting_addresses, data_regions=None):
    if data_regions is None:
        data_regions = []

    rom = mark_declared_data_regions(rom, data_regions)
    rom = mark_all_code_regions(rom, starting_addresses)
    rom = mark_all_data_regions(rom)
    rom = inject_instructions_on_missing_labels(rom)
    rom = detect_partial_instructions(rom)

    return rom


class RomCodeTestCase(unittest.TestCase):
    def test_from_a_start_point_go_to_next_unconditional_jump(self):
        # Memory content reads as
        # JP 0x0009
        # DEFM "PRINT", 0
        # JP 0x0000

        memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

        start = 0x0000
        instructions, total_size = find_next_unconditional_jump(memory, start)
        self.assertEqual(1, len(instructions))
        self.assertEqual(3, total_size)

        address, last_instruction = instructions[-1]
        size_of_last_instruction = last_instruction[-1]
        self.assertEqual(3, size_of_last_instruction)

    def test_find_unconditional_jump_stops_on_error(self):
        memory = [0xC3]

        start = 0x0000
        instructions, total_size = find_next_unconditional_jump(memory, start)
        self.assertEqual(1, len(instructions))
        self.assertEqual(0, total_size)

    def test_adjust_relative_displacements_for_jr_and_djnz(self):
        instructions = [(0x1000, ('JP', None, None, P_IMMEDIATE_16, 9, 3)),
                        (0x1003, ('DJNZ', None, None, P_DISPLACEMENT, -5, 2)),
                        (0x1005, ('JR', P_CONDITION, COND_NZ, P_DISPLACEMENT, 4, 2))]

        new_instructions = adjust_relative_displacements(instructions)

        self.assertEqual(0x0009, new_instructions[0][1][4])
        self.assertEqual(0x1000, new_instructions[1][1][4])
        self.assertEqual(0x100B, new_instructions[2][1][4])

    def test_create_labels_with_callers(self):
        instructions = [(0x1000, ('JP', None, None, P_IMMEDIATE_16, 0x0009, 3)),
                        (0x1003, ('DJNZ', None, None, P_IMMEDIATE_16, 0x1000, 2)),
                        (0x1005, ('JR', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x100B, 2)),
                        (0x1007, ('CALL', None, None, P_IMMEDIATE_16, 0x2000, 3)),
                        (0x100A, ('RST', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x0038, 1)),
                        (0x100B, ('JP', None, None, P_IMMEDIATE_16, 0x0009, 3))]

        labels = create_labels_with_callers(instructions)

        self.assertEqual(5, len(labels))
        self.assertIn(0x0009, labels)
        self.assertIn(0x1000, labels)
        self.assertIn(0x100B, labels)
        self.assertIn(0x2000, labels)
        self.assertIn(0x0038, labels)

        self.assertEqual(("jump0009", [0x1000, 0x100B]), labels[0x0009])
        self.assertEqual(("loop1000", [0x1003]), labels[0x1000])
        self.assertEqual(("skip100B", [0x1005]), labels[0x100B])
        self.assertEqual(("call2000", [0x1007]), labels[0x2000])
        self.assertEqual(("rst0038", [0x100A]), labels[0x0038])

    def test_detect_partial_instruction_tricks(self):
        memory = [0x00] * 0x285C + [0x00, 0x00, 0x00, 0x28, 0xDB, 0x00]
        instructions = [(0x285D, ('JP', None, None, P_IMMEDIATE_16, 0x0009, 3)),
                        (0x2860, ('JR', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x288D, 2)),
                        (0x2861, ('DEC', None, None, P_REGISTER_PAIR, REG_HL, 1)),
                        (0x2862, ('DEC', None, None, P_REGISTER_PAIR, REG_BC, 1))]

        expected_comment = instructions[1]

        instructions, comments = detect_partial_instruction_tricks(instructions, memory)

        expected = [(0x285D, ('JP', None, None, P_IMMEDIATE_16, 0x0009, 3)),
                    (0x2860, ('DEFB', None, None, P_IMMEDIATE_8, 0xDB, 1)),
                    (0x2861, ('DEC', None, None, P_REGISTER_PAIR, REG_HL, 1)),
                    (0x2862, ('DEC', None, None, P_REGISTER_PAIR, REG_BC, 1))]

        self.assertEqual(expected, instructions)
        self.assertEqual(expected_comment, comments[0])


class RomCodeAnalysisProcessTestCase(unittest.TestCase):
    def test_full_analysis(self):
        memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]
        rom = Rom(memory)

        starting_addresses = [0x0000]

        rom = mark_all_code_regions(rom, starting_addresses)

        self.assertEqual(2, len(rom.regions))
        self.assertEqual(((0, 3), 'code'), rom.regions[0])
        self.assertEqual(((9, 12), 'code'), rom.regions[1])

        rom = mark_all_data_regions(rom)
        self.assertEqual(3, len(rom.regions))
        self.assertEqual(((3, 9), 'data'), rom.regions[1])

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

        self.assertEqual(('jump0009', [0x0000]), rom.get_label_at(0x0009))
        self.assertEqual(('jump0000', [0x0009]), rom.get_label_at(0x0000))

    def test_trick_detection_without_label(self):
        # One trick can be detected when the second partial instruction
        # is decoded before the first
        memory = [0x00] * 0x010 + [0x28, 0x2B]
        rom = Rom(memory)
        starting_addresses = [0x11, 0x10]

        rom = mark_all_code_regions(rom, starting_addresses)
        rom = mark_all_data_regions(rom)
        rom = inject_instructions_on_missing_labels(rom)
        rom = detect_partial_instructions(rom)

        expected1 = (0x0010, 'code', ('DEFB', None, None, P_IMMEDIATE_8, 0x28, 1))
        expected2 = (0x0011, 'code', ('DEC', P_REGISTER_PAIR, REG_HL, None, None, 1))

        rom_content = []
        for content in rom.get_content(0x10, 0x12):
            rom_content.append(content)

        self.assertEqual([expected1, expected2], rom_content)
        self.assertIsNotNone(rom.get_comments_at(0x0010))

    def test_trick_detection_with_label(self):
        # The second trick can be detected when a label points to an adress
        # which was not decoded but which is in a code region
        memory = [0xC3, 0x14, 0x00] + [0x00] * 0x10 + [0x28, 0x2B]
        rom = Rom(memory)
        starting_addresses = [0x03, 0x00]

        rom = mark_all_code_regions(rom, starting_addresses)
        rom = mark_all_data_regions(rom)
        rom = inject_instructions_on_missing_labels(rom)
        rom = detect_partial_instructions(rom)

        expected1 = (0x0013, 'code', ('DEFB', None, None, P_IMMEDIATE_8, 0x28, 1))
        expected2 = (0x0014, 'code', ('DEC', P_REGISTER_PAIR, REG_HL, None, None, 1))

        self.assertEqual(expected1, rom.get_content_at(0x0013))
        self.assertEqual(expected2, rom.get_content_at(0x0014))

    def test_trick_detection_with_label_and_three_byte_instruction(self):
        memory = [0xC3, 0x14, 0x00] + [0x00] * 0x10 + [0xD2, 0xC1, 0xE1]
        rom = Rom(memory)
        starting_addresses = [0x03, 0x00]

        rom = mark_all_code_regions(rom, starting_addresses)
        rom = mark_all_data_regions(rom)
        rom = inject_instructions_on_missing_labels(rom)
        rom = detect_partial_instructions(rom)

        expected1 = (0x0013, 'code', ('DEFB', None, None, P_IMMEDIATE_8, 0xD2, 1))
        expected2 = (0x0014, 'code', ('POP', P_REGISTER_PAIR, REG_BC, None, None, 1))
        expected3 = (0x0015, 'code', ('POP', P_REGISTER_PAIR, REG_HL, None, None, 1))

        self.assertEqual(expected1, rom.get_content_at(0x0013))
        self.assertEqual(expected2, rom.get_content_at(0x0014))
        self.assertEqual(expected3, rom.get_content_at(0x0015))


if __name__ == '__main__':
    unittest.main()
