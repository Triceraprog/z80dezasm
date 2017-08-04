import unittest
from two_complement import two_complement_to_signed

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
P_REGISTER_INDEXED = "P_REG_IDX"
P_REGISTER_PAIR = "P_REG_P"
P_REGISTER_PAIR_INDIRECT = "P_REG_P_IND"
P_CONDITION = "P_COND"

REG_AF = "R_AF_P"
REG_AF_PRIME = "R_AF_PRIME_P"
REG_BC = "R_BC_P"
REG_DE = "R_DE_P"
REG_HL = "R_HL_P"
REG_SP = "R_SP_P"
REG_IX = "R_IX_P"

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

    return (P_DISPLACEMENT, two_complement_to_signed(memory[0], 8)), 1


def immediate_8_decode(splitted_opcode, memory):
    if len(memory) < 1:
        raise NotEnoughMemoryOnDecode()

    operand_8bits = memory[0]
    return (P_IMMEDIATE_8, operand_8bits), 1

def immediate_8_indirect_decode(splitted_opcode, memory):
    param, size = immediate_8_decode(splitted_opcode, memory)
    return (P_IMMEDIATE_8_INDIRECT, param[1]), size


def immediate_16_decode(splitted_opcode, memory):
    if len(memory) < 2:
        raise NotEnoughMemoryOnDecode()

    operand_16bits = memory[0] + (memory[1] << 8)
    return (P_IMMEDIATE_16, operand_16bits), 2


def immediate_16_indirect_decode(splitted_opcode, memory):
    param, size = immediate_16_decode(splitted_opcode, memory)
    return (P_IMMEDIATE_16_INDIRECT, param[1]), size


def register(register_name):
    param_type = P_REGISTER_PAIR if register_name.endswith("_P") else P_REGISTER

    return lambda splitted_opcode, memory: ((param_type, register_name), 0)


def register_pair_indirect(register_name):
    return lambda splitted_opcode, memory: ((P_REGISTER_PAIR_INDIRECT, register_name), 0)


def register_pair_from_p(splitted_opcode, memory):
    _, _, _, p, _ = splitted_opcode
    return (P_REGISTER_PAIR, REGISTER_PAIRS_WITH_SP[p]), 0


def register_pair_alt_from_p(splitted_opcode, memory):
    _, _, _, p, _ = splitted_opcode
    return (P_REGISTER_PAIR, REGISTER_PAIRS_WITH_AF[p]), 0


def register_from_y(splitted_opcode, memory):
    _, y, _, _, _ = splitted_opcode
    return (P_REGISTER, REGISTERS[y]), 0


def register_from_z(splitted_opcode, memory):
    _, _, z, _, _ = splitted_opcode
    return (P_REGISTER, REGISTERS[z]), 0


def address_from_y(splitted_opcode, memory):
    _, y, _, _, _ = splitted_opcode
    return (P_IMMEDIATE_16, y * 8), 0


def constant_from_y(splitted_opcode, memory):
    _, y, _, _, _ = splitted_opcode
    return (P_IMMEDIATE_8, y), 0


def constant_8bits(value):
    return lambda splitted_opcode, memory: ((P_IMMEDIATE_8, value), 0)


ALU_MNEMONICS = ["ADD", "ADC", "SUB", "SBC", "AND", "XOR", "OR", "CP"]

def alu_opcode_from_y(splitted_opcode):
    _, y, _, _, _ = splitted_opcode
    return ALU_MNEMONICS[y]


BLOCK_MNEMONICS = [
        ["LDI", "LDD", "INI", "OUTI"],
        ["CPI", "CPD", "IND", "OUTD"],
        ["LDI", "CPIR", "INIR", "OTIR"],
        ["LDI", "CPDR", "INDR", "OTDR"],
    ]

def block_opcode_from_yz(splitted_opcode):
    _, y, z, _, _ = splitted_opcode
    y -= 4
    return BLOCK_MNEMONICS[y][z]


SHIFT_ROT_MNEMONICS = ["RLC", "RRC", "RL", "RR", "SLA", "SRA", "SLL", "SRL"]

def rot_shift_opcode_from_y(splitted_opcode):
    _, y, _, _, _ = splitted_opcode
    return SHIFT_ROT_MNEMONICS[y]


def condition_register(register_shift=0):
    def decode_direct_register(splitted_opcode, memory):
        _, y, _, _, _ = splitted_opcode
        shifted_register = y + register_shift
        return (P_CONDITION, COND_REGISTERS_TABLE[shifted_register]), 0

    return decode_direct_register


def register_fix_for_dd_prefix(decoded, memory):
    mnemonic, p1, v1, p2, v2, size = decoded
    result = None

    if p1 == P_REGISTER and v1 == REG_AT_HL:
        if p2 == None or (p2 == P_REGISTER and v2 == REG_A):
            (_, disp), _ = displacement_decode(None, memory[0:])
            result = mnemonic, P_REGISTER_INDEXED, (REG_IX, disp), p2, v2, size + 2
        elif p2 == P_IMMEDIATE_8:
            (_, disp), _ = displacement_decode(None, memory[0:])
            (_, value), _ = immediate_8_decode(None, memory[1:])
            result = mnemonic, P_REGISTER_INDEXED, (REG_IX, disp), p2, value, size + 2


    if p2 == P_REGISTER and v2 == REG_AT_HL:
        if p1 == P_REGISTER:
            (p, value), p_size = displacement_decode(None, memory[size - 1:])
            result = mnemonic, p1, v1, P_REGISTER_INDEXED, (REG_IX, value), size + p_size + 1

    return result or ("DD PREFIX TODO", None, None, None, None, 1)


# Format on the table is
# opcode_key, mnemonic, function to decode param 1, function to decode param 2
# opcode_key can be (x, z, y) or (x, z, q, p)
ed_table = [((1, 0, range(0, 6)), "IN", register_from_y, register_pair_indirect(REG_BC)),
            ((1, 0, 6), "IN", None, register_pair_indirect(REG_BC)),
            ((1, 0, 7), "IN", register_from_y, register_pair_indirect(REG_BC)),
            ((1, 1, range(0, 6)), "OUT", register_pair_indirect(REG_BC), register_from_y),
            ((1, 1, 6), "OUT", register_pair_indirect(REG_BC), constant_8bits(0)),
            ((1, 1, 7), "OUT", register_pair_indirect(REG_BC), register_from_y),
            ((1, 3, 0, range(0, 8)), "LD", immediate_16_indirect_decode, register_pair_from_p),
            ((1, 5, 0), "RETN", None, None),
            ((1, 5, 1), "RETI", None, None),
            ((1, 5, range(2, 8)), "RETN", None, None),

            ((2, range(0, 4), range(4, 8)), block_opcode_from_yz, None, None)
             ]

cb_table = [((0, range(0, 8), range(0, 8)), rot_shift_opcode_from_y, register_from_z, None),
            ((1, range(0, 8), range(0, 8)), "BIT", constant_from_y, register_from_z),
            ((2, range(0, 8), range(0, 8)), "RES", constant_from_y, register_from_z),
            ((3, range(0, 8), range(0, 8)), "SET", constant_from_y, register_from_z),
             ]

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
         ((3, 5, 1, 0), "CALL", None, immediate_16_decode),
         ((3, 5, 1, 1), "DD PREFIX TODO", None, None),
         ((3, 5, 1, 2), "ED PREFIX TODO", None, None),
         ((3, 5, 1, 3), "FD PREFIX TODO", None, None),

         ((3, 6, range(0, 8)), alu_opcode_from_y, register(REG_A), immediate_8_decode),

         ((3, 7, range(0, 8)), "RST", None, address_from_y),
         ]


# Return format is
# mnemonic, parameter type 1, parameter value 1, parameter type 2, parameter value 2, consumed bytes
def decode_full(memory):
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
        return ((None, None), 0) if function is None else function(splitted_opcode, memory)

    if len(memory) < 1:
        return ("NOT ENOUGH MEMORY TO DECODE ANYTHING", None, None, None, None, 0)

    opcode = memory[0]
    current_table = table
    prefix_context_register_fix = lambda x, y: x

    if opcode == 0xDD:
        if len(memory) < 2:
            return ("NOT ENOUGH MEMORY TO DECODE WITH DD PREFIX", None, None, None, None, 0)
        memory = memory[1:]
        opcode = memory[0]
        if opcode in (0xDD, 0xED, 0xFD):
            return ("NONI", None, None, None, None, 1)
        if opcode == 0xCB:
            return ("DDCB PREFIX TODO", None, None, None, None, 4)
        prefix_context_register_fix = register_fix_for_dd_prefix

    prefix_size = 0

    if opcode == 0xED:
        current_table = ed_table
        memory = memory[1:]
        opcode = memory[0]
        prefix_size = 1

    if opcode == 0xCB:
        current_table = cb_table
        memory = memory[1:]
        opcode = memory[0]
        prefix_size = 1

    splitted_opcode = split_opcode(opcode)
    x, y, z, p, q = splitted_opcode
    splitted_opcode_2 = x, z, y, q, p
    mnemonic = "(not yet found)"

    try:
        for entry in current_table:
            opcode_key = entry[0]
            if match_xz(opcode_key, splitted_opcode_2):
                if match(opcode_key, splitted_opcode_2):
                    mnemonic = entry[1]
                    if not isinstance(mnemonic, str):
                        mnemonic = mnemonic(splitted_opcode)

                    param_1 = decode_parameter(entry[2], splitted_opcode, memory[1:])
                    param_1, size_1 = param_1
                    param_2 = decode_parameter(entry[3], splitted_opcode, memory[1:])
                    param_2, size_2 = param_2

                    decoded_instruction = (mnemonic,) + (param_1) + (param_2) + (1 + size_1 + size_2 + prefix_size, )
                    decoded_instruction = prefix_context_register_fix(decoded_instruction, memory[1:])

                    return decoded_instruction

    except NotEnoughMemoryOnDecode:
        return ("NOT ENOUGH MEMORY TO DECODE " + mnemonic, None, None, None, None, 0)

    return ("DECODE ERROR", None, None, None, None, 0)


def decode(memory):
    return decode_full(memory)[:-1]
