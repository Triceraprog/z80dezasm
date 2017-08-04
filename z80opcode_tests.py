import unittest
from z80tools import *


class DecodeTestCase(unittest.TestCase):
    def assertSimpleInstructions(self, code, mnemonic):
        memory = [code]
        expected = (mnemonic, None, None, None, None)
        self.assertEqual(expected, decode(memory))
        size = decode_full(memory)[-1]
        self.assertEqual(1, size)

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
        size = decode_full(memory)[-1]
        self.assertEqual(2, size)

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
        size = decode_full(memory)[-1]
        self.assertEqual(3, size)

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
    def test_decode_of_alu_instructions_with_regs(self):
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

    def test_decode_of_call(self):
        memory = [0xCD, 0x00, 0x10]
        expected = ("CALL", None, None, P_IMMEDIATE_16, 0x1000)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_alu_instructions_immediate(self):
        memory = [0xC6, 0x20]
        expected = ("ADD", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xCE, 0x20]
        expected = ("ADC", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xD6, 0x20]
        expected = ("SUB", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xDE, 0x20]
        expected = ("SBC", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xE6, 0x20]
        expected = ("AND", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xEE, 0x20]
        expected = ("XOR", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xF6, 0x20]
        expected = ("OR", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

        memory = [0xFE, 0x20]
        expected = ("CP", P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_rst(self):
        memory = [0xC7]
        expected = ("RST", None, None, P_IMMEDIATE_16, 0x00)
        self.assertEqual(expected, decode(memory))

        memory = [0xCF]
        expected = ("RST", None, None, P_IMMEDIATE_16, 0x08)
        self.assertEqual(expected, decode(memory))

        memory = [0xFF]
        expected = ("RST", None, None, P_IMMEDIATE_16, 0x38)
        self.assertEqual(expected, decode(memory))


class DecodeEDPrefixTestCase(unittest.TestCase):
    def test_decode_of_in_16_bits(self):
        memory = [0xED, 0x40]
        expected = ("IN", P_REGISTER, REG_B, P_REGISTER_PAIR_INDIRECT, REG_BC)
        self.assertEqual(expected, decode(memory))

        memory = [0xED, 0x78]
        expected = ("IN", P_REGISTER, REG_A, P_REGISTER_PAIR_INDIRECT, REG_BC)
        self.assertEqual(expected, decode(memory))

        memory = [0xED, 0x70]
        expected = ("IN", None, None, P_REGISTER_PAIR_INDIRECT, REG_BC)
        self.assertEqual(expected, decode(memory))

    def test_decode_of_retn(self):
        memory = [0xED, 0x45]
        expected = ("RETN", None, None, None, None)
        self.assertEqual(expected, decode(memory))


class DecodeDDPrefixTestCase(unittest.TestCase):
    def test_ignore_dd_if_another_conflicting_prefix(self):
        memory = [0xDD, 0xDD]
        expected = ("NONI", None, None, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xDD, 0xED]
        expected = ("NONI", None, None, None, None)
        self.assertEqual(expected, decode(memory))

        memory = [0xDD, 0xFD]
        expected = ("NONI", None, None, None, None)
        self.assertEqual(expected, decode(memory))

    def test_dec_with_dd_prefix(self):
        memory = [0xDD, 0x35, 0x00]
        expected = ("DEC", P_REGISTER_INDEXED, (REG_IX, 0), None, None)
        self.assertEqual(expected, decode(memory))
        size = decode_full(memory)[-1]
        self.assertEqual(3, size)

    def test_ld_with_dd_prefix(self):
        memory = [0xDD, 0x7E, 0x02]
        expected = ("LD", P_REGISTER, REG_A, P_REGISTER_INDEXED, (REG_IX, 2))
        self.assertEqual(expected, decode(memory))
        size = decode_full(memory)[-1]
        self.assertEqual(3, size)

        memory = [0xDD, 0x77, 0xFF]
        expected = ("LD", P_REGISTER_INDEXED, (REG_IX, -1), P_REGISTER, REG_A)
        self.assertEqual(expected, decode(memory))
        size = decode_full(memory)[-1]
        self.assertEqual(3, size)


if __name__ == '__main__':
    unittest.main()
