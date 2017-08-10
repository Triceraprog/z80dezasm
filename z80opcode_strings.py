import unittest

from z80tools import *

def get_param_str(param, value, options):
    hex_prefix = options.get("hex_prefix", "0x")

    if param == P_REGISTER_PAIR:
        if value == REG_AF_PRIME:
            return "AF'"
        else:
            return value[2:4]

    if param == P_REGISTER_PAIR_INDIRECT:
        if value == REG_AF_PRIME:
            return "(AF')"
        else:
            return "(%s)" % value[2:4]

    if param == P_REGISTER:
        if value == REG_AT_HL:
            return "(HL)"
        else:
            return value[2:]

    if param == P_IMMEDIATE_16:
        return hex_prefix + "%04X" % value

    if param == P_IMMEDIATE_16_INDIRECT:
        return "(" + hex_prefix + "%04X)" % value

    if param == P_IMMEDIATE_8:
        return hex_prefix + "%02X" % value

    if param == P_IMMEDIATE_8_INDIRECT:
        return "(" + hex_prefix + "%02X)" % value

    if param == P_CONDITION:
        return value[5:]

    if param == P_DISPLACEMENT:
        return str(value)

    if param == P_REGISTER_INDEXED:
        register_pair, displacement = value
        sign = "+" if displacement >= 0 else "-"
        displacement = abs(displacement)
        return "(%s%s%s%02X)" % (register_pair[2:4], sign, hex_prefix, displacement)

    return None


def decoded_to_string(decoded, options={}):
    mnemonic, p1, v1, p2, v2 = decoded

    param1_str = get_param_str(p1, v1, options)
    param2_str = get_param_str(p2, v2, options)

    # if mnemonic in ("CP", "OR", "SUB") and param1_str == "A":
    #   param1_str = None

    if mnemonic in ("OUT", "IN"):
        if param1_str == "(BC)":
            param1_str = "(C)"
        if param2_str == "(BC)":
            param2_str = "(C)"

    if mnemonic == "JP" and param2_str == "HL":
        param2_str = "(HL)"

    if param1_str is None and param2_str is None:
        param_str = ""
    elif param2_str is None:
        param_str = param1_str
    elif param1_str is None:
        param_str = param2_str
    else:
        param_str = param1_str + "," + param2_str

    return (mnemonic, param_str)


class FromDecodedToStringTestCase(unittest.TestCase):
    def test_immediate_16(self):
        decoded = ('JP', None, None, P_IMMEDIATE_16, 4096)
        expected = ('JP', '0x1000')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_register_pair(self):
        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 32256)
        expected = ('LD', 'SP,0x7E00')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_register_pair_indirect(self):
        decoded = ('EX', P_REGISTER_PAIR_INDIRECT, REG_SP, P_REGISTER_PAIR, REG_HL)
        expected = ('EX', '(SP),HL')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_register(self):
        decoded = ('LD', P_REGISTER, REG_A, P_REGISTER, REG_AT_HL)
        expected = ('LD', 'A,(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_register(self):
        decoded = ('CP', P_REGISTER, REG_A, P_REGISTER, REG_AT_HL)
        expected = ('CP', 'A,(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_condition(self):
        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        expected = ('JP', 'NZ,0x2238')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_immediate_8(self):
        decoded = ('CP', P_REGISTER, REG_A, P_IMMEDIATE_8, 0x3A)
        expected = ('CP', 'A,0x3A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_immediate_8_indirect(self):
        decoded = ('OUT', P_IMMEDIATE_8_INDIRECT, 0xCF, P_REGISTER, REG_A)
        expected = ('OUT', '(0xCF),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_immediate_16_indirect(self):
        decoded = ('LD', P_IMMEDIATE_16_INDIRECT, 0x4890, P_REGISTER, REG_A)
        expected = ('LD', '(0x4890),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_displacement(self):
        decoded = ('JR', P_CONDITION, COND_NZ, P_DISPLACEMENT, -14)
        expected = ('JR', 'NZ,-14')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_index(self):
        decoded = ('LD', P_REGISTER, REG_A, P_REGISTER_INDEXED, (REG_IX, 3))
        expected = ('LD', 'A,(IX+0x03)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_alternate_hex_writing(self):
        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        expected = ('JP', 'NZ,$2238')

        output = decoded_to_string(decoded, {"hex_prefix": "$"})
        self.assertEqual(expected,  output)

    def test_bc_written_c_in_out(self):
        decoded = ('OUT', P_REGISTER_PAIR_INDIRECT, REG_BC, P_REGISTER, REG_A)
        expected = ('OUT', '(C),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)

    def test_jp_hl_written_as_jp_at_hl(self):
        decoded = ('JP', None, None, P_REGISTER_PAIR, REG_HL)
        expected = ('JP', '(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected,  output)


if __name__ == '__main__':
    unittest.main()
