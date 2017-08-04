import unittest
from two_complement import two_complement_to_signed


# with open("vg5000_1.1.rom", "rb") as romFile:
#    romContent = romFile.read()

# xxyyyzzz
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


P_IMMEDIATE_8 = "P_IMM_8"
P_IMMEDIATE_8_INDIRECT = "P_IMM_8_IND"
P_IMMEDIATE_16 = "P_IMM_16"
P_IMMEDIATE_16_INDIRECT = "P_IMM_16_IND"
P_DISPLACEMENT = "P_DISP"
P_REGISTER = "P_REG"
P_REGISTER_PAIR = "P_REG_P"
P_REGISTER_PAIR_INDIRECT = "P_REG_P_IND"
P_CONDITION = "P_COND"

REG_AF = "R_AF_P"
REG_AF_PRIME = "R_AF_PRIME_P"
REG_BC = "R_BC_P"
REG_DE = "R_DE_P"
REG_HL = "R_HL_P"
REG_SP = "R_SP_P"

REG_B = "R_B"
REG_C = "R_C"
REG_D = "R_D"
REG_E = "R_E"
REG_H = "R_H"
REG_L = "R_L"
REG_AT_HL = "R_AT_HL"
REG_A = "R_A"

REGISTERS = [REG_B, REG_C, REG_D, REG_E, REG_H, REG_L, REG_AT_HL, REG_A]

COND_NZ = "COND_NZ"
COND_Z = "COND_Z"
COND_NC = "COND_NC"
COND_C = "COND_C"
COND_PO = "COND_PO"
COND_PE = "COND_PE"
COND_P = "COND_P"
COND_M = "COND_M"

COND_REGISTERS_TABLE = [COND_NZ, COND_Z, COND_NC, COND_C, COND_PO, COND_PE, COND_P, COND_M]
REGISTER_PAIRS_WITH_SP = [REG_BC, REG_DE, REG_HL, REG_SP]
REGISTER_PAIRS_WITH_AF = [REG_BC, REG_DE, REG_HL, REG_AF]


class NotEnoughMemoryOnDecode(BaseException):
    pass


def displacement_decode(splitted_opcode, memory):
    if len(memory) < 1:
        raise NotEnoughMemoryOnDecode()

    return P_DISPLACEMENT, two_complement_to_signed(memory[0], 8)


def immediate_8_decode(splitted_opcode, memory):
    if len(memory) < 1:
        raise NotEnoughMemoryOnDecode()

    operand_8bits = memory[0]
    return P_IMMEDIATE_8, operand_8bits

def immediate_8_indirect_decode(splitted_opcode, memory):
    decode = immediate_8_decode(splitted_opcode, memory)
    return P_IMMEDIATE_8_INDIRECT, decode[1]


def immediate_16_decode(splitted_opcode, memory):
    if len(memory) < 2:
        raise NotEnoughMemoryOnDecode()

    operand_16bits = memory[0] + (memory[1] << 8)
    return P_IMMEDIATE_16, operand_16bits


def immediate_16_indirect_decode(splitted_opcode, memory):
    decode = immediate_16_decode(splitted_opcode, memory)
    return P_IMMEDIATE_16_INDIRECT, decode[1]


def register(register_name):
    param_type = P_REGISTER_PAIR if register_name.endswith("_P") else P_REGISTER
    def decode_direct_register(splitted_opcode, memory):
        return param_type, register_name

    return decode_direct_register


def register_pair_indirect(register_name):
    def decode_direct_register(splitted_opcode, memory):
        return P_REGISTER_PAIR_INDIRECT, register_name

    return decode_direct_register


def register_pair_from_p(splitted_opcode, memory):
    _, _, _, p, _ = splitted_opcode
    return P_REGISTER_PAIR, REGISTER_PAIRS_WITH_SP[p]


def register_pair_alt_from_p(splitted_opcode, memory):
    _, _, _, p, _ = splitted_opcode
    return P_REGISTER_PAIR, REGISTER_PAIRS_WITH_AF[p]


def register_from_y(splitted_opcode, memory):
    _, y, _, _, _ = splitted_opcode
    return P_REGISTER, REGISTERS[y]


def register_from_z(splitted_opcode, memory):
    _, _, z, _, _ = splitted_opcode
    return P_REGISTER, REGISTERS[z]


ALU_MNEMONICS = ["ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP"]

def alu_opcode_from_y(splitted_opcode):
    _, y, _, _, _ = splitted_opcode
    return ALU_MNEMONICS[y]


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
         ((0, 1, 0, range(0, 5)), "LD", register_pair_from_p, immediate_16_decode),
         ((0, 1, 1, range(0, 5)), "ADD", register(REG_HL), register_pair_from_p),
         ((0, 2, 0, 0), "LD", register_pair_indirect(REG_BC), register(REG_A)),
         ((0, 2, 0, 1), "LD", register_pair_indirect(REG_DE), register(REG_A)),
         ((0, 2, 0, 2), "LD", immediate_16_indirect_decode, register(REG_HL)),
         ((0, 2, 0, 3), "LD", immediate_16_indirect_decode, register(REG_A)),
         ((0, 2, 1, 0), "LD", register(REG_A), register_pair_indirect(REG_BC)),
         ((0, 2, 1, 1), "LD", register(REG_A), register_pair_indirect(REG_DE)),
         ((0, 2, 1, 2), "LD", register(REG_HL), immediate_16_indirect_decode),
         ((0, 2, 1, 3), "LD", register(REG_A), immediate_16_indirect_decode),
         ((0, 3, 0, range(0, 5)), "INC", register_pair_from_p, None),
         ((0, 3, 1, range(0, 5)), "DEC", register_pair_from_p, None),
         ((0, 4, range(0, 9)), "INC", register_from_y, None),
         ((0, 5, range(0, 9)), "DEC", register_from_y, None),
         ((0, 6, range(0, 9)), "LD", register_from_y, immediate_8_decode),
         ((0, 7, 0), "RLCA", None, None),
         ((0, 7, 1), "RRCA", None, None),
         ((0, 7, 2), "RLA", None, None),
         ((0, 7, 3), "RRA", None, None),
         ((0, 7, 4), "DAA", None, None),
         ((0, 7, 5), "CPL", None, None),
         ((0, 7, 6), "SCF", None, None),
         ((0, 7, 7), "CCF", None, None),

         ((1, range(0, 6), range(0, 9)), "LD", register_from_y, register_from_z),
         ((1, 6, range(0, 6)), "LD", register_from_y, register_from_z),
         ((1, 6, 6), "HALT", None, None),
         ((1, 6, range(7, 9)), "LD", register_from_y, register_from_z),
         ((1, 7, range(0, 9)), "LD", register_from_y, register_from_z),

         ((2, range(0, 8), range(0, 8)), alu_opcode_from_y, register(REG_A), register_from_z),

         ((3, 0, range(0, 8)), "RET", condition_register(), None),
         ((3, 1, 0, range(0, 4)), "POP", register_pair_alt_from_p, None),
         ((3, 1, 1, 0), "RET", None, None),
         ((3, 1, 1, 1), "EXX", None, None),
         ((3, 1, 1, 2), "JP", None, register(REG_HL)),
         ((3, 1, 1, 3), "LD", register(REG_SP), register(REG_HL)),

         ((3, 2, range(0, 8)), "JP", condition_register(), immediate_16_decode),

         ((3, 3, 0), "JP", None, immediate_16_decode),
         ((3, 3, 1), "CB PREFIX TODO", None, None),
         ((3, 3, 2), "OUT", immediate_8_indirect_decode, register(REG_A)),
         ((3, 3, 3), "IN", register(REG_A), immediate_8_indirect_decode),
         ((3, 3, 4), "EX", register_pair_indirect(REG_SP), register(REG_HL)),
         ((3, 3, 5), "EX", register(REG_DE), register(REG_HL)),
         ((3, 3, 6), "DI", None, None),
         ((3, 3, 7), "EI", None, None),

         ((3, 4, range(0, 8)), "CALL", condition_register(), immediate_16_decode),

         ((3, 5, 0, range(0, 4)), "PUSH", None, register_pair_alt_from_p),
         ]


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

    def match_xz(opcode_ref_key, opcode_key):
        if isinstance(opcode_ref_key[1], range):
            return (opcode_ref_key[0] == opcode_key[0]
                    and opcode_key[1] in opcode_ref_key[1])
        return opcode_ref_key[0:2] == opcode_key[0:2]

    def match_y(opcode_ref_key, opcode_key):
        if isinstance(opcode_ref_key[2], range):
            return opcode_key[2] in opcode_ref_key[2]
        return opcode_key[2] == opcode_ref_key[2]

    def match_pq(opcode_ref_key, opcode_key):
        if isinstance(opcode_ref_key[3], range):
            return (opcode_ref_key[2] == opcode_key[3]
                    and opcode_key[4] in opcode_ref_key[3])
        return opcode_ref_key[2:4] == opcode_key[3:5]

    def match(opcode_ref_key, opcode_key):
        return ((len(opcode_ref_key) == 3) and match_y(opcode_ref_key, opcode_key)
                or
                (len(opcode_ref_key) == 4) and match_pq(opcode_ref_key, opcode_key))

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
            if match_xz(opcode_key, splitted_opcode_2):
                if match(opcode_key, splitted_opcode_2):
                    mnemonic = entry[1]
                    if not isinstance(mnemonic, str):
                        mnemonic = mnemonic(splitted_opcode)

                    param_1 = decode_parameter(entry[2], splitted_opcode, memory[1:])
                    param_2 = decode_parameter(entry[3], splitted_opcode, memory[1:])

                    return (mnemonic,) + (param_1) + (param_2)

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

    # Instructions without prefix, with x=0
    def test_decode_of_nop(self):
        self.assertSimpleInstructions(0x00, "NOP")

    def test_decode_of_nop(self):
        memory = [0x08]
        expected = ("EX", P_REGISTER_PAIR, REG_AF, P_REGISTER_PAIR, REG_AF_PRIME)
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

    def test_decode_of_add_hl_with_register_pair(self):
        memory = [0x09]
        expected = ("ADD", P_REGISTER_PAIR, REG_HL, P_REGISTER_PAIR, REG_BC)
        self.assertEqual(expected, decode(memory))

        memory = [0x19]
        expected = ("ADD", P_REGISTER_PAIR, REG_HL, P_REGISTER_PAIR, REG_DE)
        self.assertEqual(expected, decode(memory))

        memory = [0x29]
        expected = ("ADD", P_REGISTER_PAIR, REG_HL, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        memory = [0x39]
        expected = ("ADD", P_REGISTER_PAIR, REG_HL, P_REGISTER_PAIR, REG_SP)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_ld_indirect(self):
        memory = [0x02]
        expected = ("LD", P_REGISTER_PAIR_INDIRECT, REG_BC, P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))

        memory = [0x12]
        expected = ("LD", P_REGISTER_PAIR_INDIRECT, REG_DE, P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))

        memory = [0x22, 0x00, 0x40]
        expected = ("LD", P_IMMEDIATE_16_INDIRECT, 16384, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        memory = [0x32, 0x00, 0x40]
        expected = ("LD", P_IMMEDIATE_16_INDIRECT, 16384, P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))

        memory = [0x0A]
        expected = ("LD", P_REGISTER, REG_A, P_REGISTER_PAIR_INDIRECT, REG_BC)
        self.assertEqual(expected, decode(memory))

        memory = [0x1A]
        expected = ("LD", P_REGISTER, REG_A, P_REGISTER_PAIR_INDIRECT, REG_DE)
        self.assertEqual(expected, decode(memory))

        memory = [0x2A, 0x00, 0x40]
        expected = ("LD", P_REGISTER_PAIR, REG_HL, P_IMMEDIATE_16_INDIRECT, 16384)
        self.assertEqual(expected, decode(memory))

        memory = [0x3A, 0x00, 0x40]
        expected = ("LD", P_REGISTER, REG_A, P_IMMEDIATE_16_INDIRECT, 16384)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_inc_dec_register_pairs(self):
        memory = [0x03]
        expected = ("INC", P_REGISTER_PAIR, REG_BC, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x13]
        expected = ("INC", P_REGISTER_PAIR, REG_DE, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x23]
        expected = ("INC", P_REGISTER_PAIR, REG_HL, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x33]
        expected = ("INC", P_REGISTER_PAIR, REG_SP, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x0B]
        expected = ("DEC", P_REGISTER_PAIR, REG_BC, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x1B]
        expected = ("DEC", P_REGISTER_PAIR, REG_DE, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x2B]
        expected = ("DEC", P_REGISTER_PAIR, REG_HL, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x3B]
        expected = ("DEC", P_REGISTER_PAIR, REG_SP, None, None)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_inc_dec_register(self):
        memory = [0x04]
        expected = ("INC", P_REGISTER, REG_B, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x0C]
        expected = ("INC", P_REGISTER, REG_C, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x14]
        expected = ("INC", P_REGISTER, REG_D, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x1C]
        expected = ("INC", P_REGISTER, REG_E, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x24]
        expected = ("INC", P_REGISTER, REG_H, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x2C]
        expected = ("INC", P_REGISTER, REG_L, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x34]
        expected = ("INC", P_REGISTER, REG_AT_HL, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x3C]
        expected = ("INC", P_REGISTER, REG_A, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x05]
        expected = ("DEC", P_REGISTER, REG_B, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x0D]
        expected = ("DEC", P_REGISTER, REG_C, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x15]
        expected = ("DEC", P_REGISTER, REG_D, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x1D]
        expected = ("DEC", P_REGISTER, REG_E, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x25]
        expected = ("DEC", P_REGISTER, REG_H, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x2D]
        expected = ("DEC", P_REGISTER, REG_L, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x35]
        expected = ("DEC", P_REGISTER, REG_AT_HL, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0x3D]
        expected = ("DEC", P_REGISTER, REG_A, None, None)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_ld_8_immediate(self):
        memory = [0x06, 0xFF]
        expected = ("LD", P_REGISTER, REG_B, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x0E, 0xFF]
        expected = ("LD", P_REGISTER, REG_C, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x16, 0xFF]
        expected = ("LD", P_REGISTER, REG_D, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x1E, 0xFF]
        expected = ("LD", P_REGISTER, REG_E, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x26, 0xFF]
        expected = ("LD", P_REGISTER, REG_H, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x2E, 0xFF]
        expected = ("LD", P_REGISTER, REG_L, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x36, 0xFF]
        expected = ("LD", P_REGISTER, REG_AT_HL, P_IMMEDIATE_8, 255)
        self.assertEqual(expected, decode(memory))

        memory = [0x3E, 0xFF]
        expected = ("LD", P_REGISTER, REG_A, P_IMMEDIATE_8, 255)
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

    # Instructions without prefix, with x=1
    def test_decode_of_ld_8_register_to_register(self):
        memory = [0x40]
        expected = ("LD", P_REGISTER, REG_B, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0x78]
        expected = ("LD", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0x43]
        expected = ("LD", P_REGISTER, REG_B, P_REGISTER, REG_E)
        self.assertEqual(expected, decode(memory))

        memory = [0x4B]
        expected = ("LD", P_REGISTER, REG_C, P_REGISTER, REG_E)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_halt(self):
        self.assertSimpleInstructions(0x76, "HALT")

    # Instructions without prefix, with x=2
    def test_decode_of_alu_instructions(self):
        memory = [0x80]
        expected = ("ADD", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0x88]
        expected = ("ADC", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0x90]
        expected = ("SUB", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0x98]
        expected = ("SBC", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0xA0]
        expected = ("AND", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0xA8]
        expected = ("XOR", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0xB0]
        expected = ("OR", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0xB8]
        expected = ("CP", P_REGISTER, REG_A, P_REGISTER, REG_B)
        self.assertEqual(expected, decode(memory))

        memory = [0xB9]
        expected = ("CP", P_REGISTER, REG_A, P_REGISTER, REG_C)
        self.assertEqual(expected, decode(memory))

        memory = [0xB7]
        expected = ("OR", P_REGISTER, REG_A, P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))

    # Instructions without prefix, with x=3
    def test_decode_of_conditional_ret(self):
        memory = [0xC0]
        expected = ("RET", P_CONDITION, COND_NZ, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xC8]
        expected = ("RET", P_CONDITION, COND_Z, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xD0]
        expected = ("RET", P_CONDITION, COND_NC, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xD8]
        expected = ("RET", P_CONDITION, COND_C, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xE0]
        expected = ("RET", P_CONDITION, COND_PO, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xE8]
        expected = ("RET", P_CONDITION, COND_PE, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xF0]
        expected = ("RET", P_CONDITION, COND_P, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xF8]
        expected = ("RET", P_CONDITION, COND_M, None, None)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_pop_register_pair(self):
        memory = [0xC1]
        expected = ("POP", P_REGISTER_PAIR, REG_BC, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xD1]
        expected = ("POP", P_REGISTER_PAIR, REG_DE, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xE1]
        expected = ("POP", P_REGISTER_PAIR, REG_HL, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xF1]
        expected = ("POP", P_REGISTER_PAIR, REG_AF, None, None)
        self.assertEqual(expected, decode(memory))


    def test_decode_of_various_x_3_z_1(self):
        self.assertSimpleInstructions(0xC9, "RET")
        self.assertSimpleInstructions(0xD9, "EXX")

        memory = [0xE9]
        expected = ("JP", None, None, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        memory = [0xF9]
        expected = ("LD", P_REGISTER_PAIR, REG_SP, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_conditional_jp(self):
        memory = [0xC2, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xCA, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_Z, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xD2, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_NC, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xDA, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_C, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xE2, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_PO, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xEA, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_PE, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xF2, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_P, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xFA, 0x00, 0x10]
        expected = ("JP", P_CONDITION, COND_M, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_jp_direct(self):
        memory = [0xC3, 0x00, 0x10]
        expected = ("JP", None, None, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_out(self):
        memory = [0xD3, 0x80]
        expected = ("OUT", P_IMMEDIATE_8_INDIRECT, 128, P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_in(self):
        memory = [0xDB, 0x81]
        expected = ("IN", P_REGISTER, REG_A, P_IMMEDIATE_8_INDIRECT, 129)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_various_x_3_z_3(self):
        memory = [0xE3]
        expected = ("EX", P_REGISTER_PAIR_INDIRECT, REG_SP, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        memory = [0xEB]
        expected = ("EX", P_REGISTER_PAIR, REG_DE, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        self.assertSimpleInstructions(0xF3, "DI")
        self.assertSimpleInstructions(0xFB, "EI")

    def test_decode_of_conditional_call(self):
        memory = [0xC4, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xCC, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_Z, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xD4, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_NC, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xDC, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_C, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xE4, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_PO, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xEC, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_PE, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xF4, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_P, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

        memory = [0xFC, 0x00, 0x10]
        expected = ("CALL", P_CONDITION, COND_M, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_conditional_call(self):
        memory = [0xC5]
        expected = ("PUSH", None, None, P_REGISTER_PAIR, REG_BC)
        self.assertEqual(expected, decode(memory))

        memory = [0xD5]
        expected = ("PUSH", None, None, P_REGISTER_PAIR, REG_DE)
        self.assertEqual(expected, decode(memory))

        memory = [0xE5]
        expected = ("PUSH", None, None, P_REGISTER_PAIR, REG_HL)
        self.assertEqual(expected, decode(memory))

        memory = [0xF5]
        expected = ("PUSH", None, None, P_REGISTER_PAIR, REG_AF)
        self.assertEqual(expected, decode(memory))


if __name__ == '__main__':
    unittest.main()
