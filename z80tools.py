import unittest
from two_complement import two_complement_to_signed

# with open("vg5000_1.1.rom", "rb") as romFile:
#    romContent = romFile.read()

# xxyyyzz
#   ppq

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
P_REGISTER = "P_REG"
P_REGISTER_PAIR = "P_REG_P"
P_CONDITION = "P_COND"

REG_AF = "R_AF"
REG_AF_PRIME = "R_AF_P"
REG_BC = "R_BC"
REG_DE = "R_DE"
REG_HL = "R_HL"
REG_SP = "R_SP"


COND_NZ = "COND_NZ"
COND_Z = "COND_Z"
COND_NC = "COND_NC"
COND_C = "COND_C"

COND_REGISTERS_TABLE = [COND_NZ, COND_Z, COND_NC, COND_C]
REGISTER_PAIRS_WITH_SP = [REG_BC, REG_DE, REG_HL, REG_SP]


class NotEnoughMemoryOnDecode(BaseException):
    pass


def displacement_decode(splitted_opcode, memory):
    if len(memory) < 1:
        raise NotEnoughMemoryOnDecode()

    return P_DISPLACEMENT, two_complement_to_signed(memory[0], 8)


def immediate_16_decode(splitted_opcode, memory):
    if len(memory) < 2:
        raise NotEnoughMemoryOnDecode()

    operand_16bits = memory[0] + (memory[1] << 8)
    return P_IMMEDIATE_16, operand_16bits


def register(register_name):
    def decode_direct_register(splitted_opcode, memory):
        return P_REGISTER, register_name

    return decode_direct_register


def register_pair_from_p(splitted_opcode, memory):
    _, _, _, p, _ = splitted_opcode
    return (P_REGISTER_PAIR, REGISTER_PAIRS_WITH_SP[p])


def condition_register(register_shift=0):
    def decode_direct_register(splitted_opcode, memory):
        _, y, _, _, _ = splitted_opcode
        shifted_register = y + register_shift
        return P_CONDITION, COND_REGISTERS_TABLE[shifted_register]

    return decode_direct_register


# Format on the table is
# opcode_key, mnemonic, function to decode param 1, function to decode param 2
# opcode_key can be (x, z, y) or (x, z, q, p)
table = [((0, 0, 0), "NOP", None, None),
         ((0, 0, 1), "EX", register(REG_AF), register(REG_AF_PRIME)),
         ((0, 0, 2), "DJNZ", None, displacement_decode),
         ((0, 0, 3), "JR", None, displacement_decode),
         ((0, 0, range(4, 8)), "JR", condition_register(register_shift=-4), displacement_decode),
         ((0, 1, 0, 0), "LD", register_pair_from_p, immediate_16_decode),
         ((0, 1, 0, 1), "LD", register_pair_from_p, immediate_16_decode),
         ((0, 1, 0, 2), "LD", register_pair_from_p, immediate_16_decode),
         ((0, 1, 0, 3), "LD", register_pair_from_p, immediate_16_decode),
         ((0, 7, 0), "RLCA", None, None),
         ((0, 7, 1), "RRCA", None, None),
         ((0, 7, 2), "RLA", None, None),
         ((0, 7, 3), "RRA", None, None),
         ((0, 7, 4), "DAA", None, None),
         ((0, 7, 5), "CPL", None, None),
         ((0, 7, 6), "SCF", None, None),
         ((0, 7, 7), "CCF", None, None),
         ((3, 3, 0), "JP", None, immediate_16_decode),
         ((3, 1, 1, 0), "RET", None, None)]

# Return format is
# mnemonic, parameter type 1, parameter value 1, parameter type 2, parameter value 2
def decode(memory):
    # [prefix,] opcode [,displacement byte] [,immediate data]
    # two prefix bytes (DD/FD + CB), displacement byte, opcode

    # prefixes: CB, DD, ED, FD
    # displacement, signed 8bits
    # immediate: 0 to 2 bytes, LSB first

    # if invalid, NOP (or NONI)

    # LD A,A does nothing, as NOP

    def match_y(opcode_ref_key, opcode_key):
        if isinstance(opcode_ref_key[2], range):
            return opcode_key[2] in opcode_ref_key[2]
        return opcode_key[2] == opcode_ref_key[2]

    def match(opcode_ref_key, opcode_key):
        return ((len(opcode_ref_key) == 3) and match_y(opcode_ref_key, opcode_key)
                or
                (len(opcode_ref_key) == 4) and (opcode_ref_key[2:4] == opcode_key[3:5]))


    def decode_parameter(function, splitted_opcode, memory):
        return (None, None) if function is None else function(splitted_opcode, memory)


    if len(memory) < 1:
        return "ERROR"

    opcode = memory[0]
    splitted_opcode = split_opcode(opcode)
    x, y, z, p, q = splitted_opcode
    splitted_opcode_2 = x, z, y, q, p
    mnemonic = "(not yet found)"

    try:
        for entry in table:
            opcode_key = entry[0]
            if opcode_key[0:2] == splitted_opcode_2[0:2]:
                if match(opcode_key, splitted_opcode_2):
                    mnemonic = entry[1]

                    param_1 = decode_parameter(entry[2], splitted_opcode, memory[1:])
                    param_2 = decode_parameter(entry[3], splitted_opcode, memory[1:])

                    return (mnemonic, ) + (param_1) + (param_2)

    except NotEnoughMemoryOnDecode:
        return ("NOT ENOUGH MEMORY TO DECODE " + mnemonic, None, None, None, None)

    return ("DECODE ERROR", None, None, None, None)



class DecodeTestCase(unittest.TestCase):
    def assertSimpleInstructions(self, code, mnemonic):
        memory = [code]
        expected = (mnemonic, None, None, None, None)
        self.assertEqual(expected, decode(memory))

    def test_giving_not_enough_memory_to_djnz(self):
        memory = [0x10]
        result = decode(memory)
        self.assertTrue(result[0].startswith("NOT ENOUGH"))

    def test_decode_of_nop(self):
        self.assertSimpleInstructions(0x00, "NOP")

    def test_decode_of_nop(self):
        memory = [0x08]
        expected = ("EX", P_REGISTER, REG_AF, P_REGISTER, REG_AF_PRIME)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_djnz_disp(self):
        memory = [0x10, 0xe8]
        expected = ("DJNZ", None, None, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_jr_disp(self):
        memory = [0x18, 0xe8]
        expected = ("JR", None, None, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_jr_cond_disp(self):
        memory = [0x20, 0xe8]
        expected = ("JR", P_CONDITION, COND_NZ, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

        memory = [0x28, 0xe8]
        expected = ("JR", P_CONDITION, COND_Z, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

        memory = [0x30, 0xe8]
        expected = ("JR", P_CONDITION, COND_NC, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

        memory = [0x38, 0xe8]
        expected = ("JR", P_CONDITION, COND_C, P_DISPLACEMENT, -24)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_ld_16_immediate(self):
        memory = [0x01, 0x34, 0x12]
        expected = ("LD", P_REGISTER_PAIR, REG_BC, P_IMMEDIATE_16, 4660)
        self.assertEqual(expected, decode(memory))

        memory = [0x11, 0x34, 0x12]
        expected = ("LD", P_REGISTER_PAIR, REG_DE, P_IMMEDIATE_16, 4660)
        self.assertEqual(expected, decode(memory))

        memory = [0x21, 0x34, 0x12]
        expected = ("LD", P_REGISTER_PAIR, REG_HL, P_IMMEDIATE_16, 4660)
        self.assertEqual(expected, decode(memory))

        memory = [0x31, 0x34, 0x12]
        expected = ("LD", P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 4660)
        self.assertEqual(expected, decode(memory))


    def test_decode_of_various_x_0(self):
        self.assertSimpleInstructions(0x07, "RLCA")
        self.assertSimpleInstructions(0x0F, "RRCA")
        self.assertSimpleInstructions(0x17, "RLA")
        self.assertSimpleInstructions(0x1F, "RRA")
        self.assertSimpleInstructions(0x27, "DAA")
        self.assertSimpleInstructions(0x2F, "CPL")
        self.assertSimpleInstructions(0x37, "SCF")
        self.assertSimpleInstructions(0x3F, "CCF")

    def test_decode_of_ret(self):
        self.assertSimpleInstructions(0xC9, "RET")

    def test_decode_of_jp_direct(self):
        memory = [0xC3, 0x00, 0x10]
        expected = ("JP", None, None, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))


if __name__ == '__main__':
    unittest.main()
