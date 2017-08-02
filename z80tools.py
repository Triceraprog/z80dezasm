import unittest

# with open("vg5000_1.1.rom", "rb") as romFile:
#    romContent = romFile.read()

def two_complement(number, width):
    all_1 = 2 ** width - 1
    number = number ^ all_1
    number += 1
    number &= all_1
    return number


def two_complement_to_signed(number, width):
    all_1 = 2 ** width - 1
    number &= all_1

    sign_bit = 1 << (width-1)

    if sign_bit & number == 0:
        return number

    return -two_complement(number, width)


def split_opcode(opcode):
    x = (0xC0 & opcode) >> 6
    y = (0x38 & opcode) >> 3
    z = (0x07 & opcode) >> 0

    p = (0x30 & opcode) >> 4
    q = (0x08 & opcode) >> 3

    return x, y, z, p, q


class OpCodeTestCase(unittest.TestCase):
    def test_opcode_nop_splits_to_all_0(self):
        expect = (0, 0, 0, 0, 0)
        self.assertEqual(expect, split_opcode(0x00))

    def test_opcode_ret_split(self):
        expect = (3, 1, 1, 0, 1)
        self.assertEqual(expect, split_opcode(0xC9))


P_IMMEDIATE_16 = "P_IMM_16"
P_DISPLACEMENT = "P_DISP"

# Format (x, z, y, "NAME")
# Format (x, z, q, p, "NAME")
# NAME = OP nn
# (0, 0, 0, "NOP")
# (0, 0, 0, "NOP")

def displacement_decode(memory):
    if len(memory) < 1:
        return "NOT ENOUGH MEMORY FOR DECODING"

    return P_DISPLACEMENT, two_complement_to_signed(memory[0], 8)


def immediate_16_decode(memory):
    if len(memory) < 2:
        return "NOT ENOUGH MEMORY FOR DECODING"

    operand_16bits = memory[0] + (memory[1] << 8)
    return P_IMMEDIATE_16, operand_16bits


table = [(0, 0, 0, "NOP", None, None),
         (0, 0, 2, "DJNZ", None, displacement_decode),
         (3, 3, 0, "JP", None, immediate_16_decode),
         (3, 1, 1, 0, "RET", None, None)]

# Return format
# "NOP", None, "", None, ""
# "JP", None, "", P_IMMEDIATE, 0x123
# "JP", None, "", P_DISPLACEMENT, -14
# "LD", P_REGISTER, REG_HL, P_REGISTER, REG_SP

def decode(memory):
    # [prefix,] opcode [,displacement byte] [,immediate data]
    # two prefix bytes (DD/FD + CB), displacement byte, opcode

    # prefixes: CB, DD, ED, FD
    # displacement, signed 8bits
    # immediate: 0 to 2 bytes, LSB first

    # if invalid, NOP (or NONI)

    # LD A,A does nothing, as NOP
    if len(memory) < 1:
        return "ERROR"

    opcode = memory[0]
    splitted_opcode = split_opcode(opcode)
    x, y, z, p, q = splitted_opcode
    splitted_opcode_2 = x, z, y, q, p

    for entry in table:
        if entry[0:2] == splitted_opcode_2[0:2]:
            if len(entry) == 6:
                if entry[2] == splitted_opcode_2[2]:

                    decoding_function = entry[5]
                    if decoding_function is None:
                        param_2 = (None, None)
                    else:
                        param_2 = decoding_function(memory[1:])

                    return (entry[3], None, None) + (param_2)
            elif len(entry) == 7:
                if entry[2:3] == splitted_opcode_2[3:4]:
                    return (entry[4], None, None, None, None)

    return "DECODE ERROR"



class TwoComplementTestCase(unittest.TestCase):
    def test_0_complement_is_0(self):
        self.assertEqual(0, two_complement(0, 8))

    def test_1_complement_is_11111111(self):
        self.assertEqual(255, two_complement(1, 8))

    def test_10000001_complement_is_01111111(self):
        self.assertEqual(129, two_complement(127, 8))

    def test_0_is_signed_0(self):
        self.assertEqual(0, two_complement_to_signed(0, 8))

    def test_1_is_signed_1(self):
        self.assertEqual(1, two_complement_to_signed(1, 8))

    def test_255_is_signed_minus_1(self):
        self.assertEqual(-1, two_complement_to_signed(255, 8))

    def test_65535_is_signed_minus_1(self):
        self.assertEqual(-1, two_complement_to_signed(65535, 16))



class DecodeTestCase(unittest.TestCase):
    def test_decode_of_nop(self):
        memory = [0]
        expected = ("NOP", None, None, None, None)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_djnz_disp(self):
        memory = [0x10, 0xe8]
        expected = ("DJNZ", None, None, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_ret(self):
        memory = [0xC9]
        expected = ("RET", None, None, None, None)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_jp_direct(self):
        memory = [0xC3, 0x00, 0x10]
        expected = ("JP", None, None, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

if __name__ == '__main__':
    unittest.main()
