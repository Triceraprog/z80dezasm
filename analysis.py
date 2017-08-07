import unittest

from z80tools import decode_full, P_IMMEDIATE_16, P_DISPLACEMENT, P_CONDITION, COND_NZ

# Memory content reads as
# JP 0x0009
# DEFM "PRINT", 0
# JP 0x0000

memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

def is_unconditionnal_jump(fully_decoded):
    mnemonic, p1, v1, p2, v2, size = fully_decoded
    return mnemonic in ("JP", "JR") and p1 == None and (p2 == P_IMMEDIATE_16 or p2 == P_DISPLACEMENT)


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


def test_adjust_relative_displacements(instructions):
    new_instructions = []
    for pc, instruction in instructions:
        mnemonic, p1, v1, p2, v2, size = instruction
        if mnemonic in ("JR", "DJNZ") and p2 == P_DISPLACEMENT:
            instruction = mnemonic, p1, v1, P_IMMEDIATE_16, pc + v2 + size, size

        new_instructions.append((pc, instruction))

    return new_instructions


class RomCodeTestCase(unittest.TestCase):
    def test_from_a_start_point_go_to_next_unconditional_jump(self):
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

        new_instructions = test_adjust_relative_displacements(instructions)

        self.assertEqual(0x0009, new_instructions[0][1][4])
        self.assertEqual(0x1000, new_instructions[1][1][4])
        self.assertEqual(0x100B, new_instructions[2][1][4])


if __name__ == '__main__':
    unittest.main()
