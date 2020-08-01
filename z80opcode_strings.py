from z80tools import *


def get_param_str(param, value, options):
    hex_prefix = options.get("hex_prefix", "0x")
    as_char = options.get("as_char", False)

    if param is P_REGISTER_PAIR:
        if value is REG_AF_PRIME:
            return "AF'"
        else:
            return value[2:4]

    if param is P_REGISTER_PAIR_INDIRECT:
        if value is REG_AF_PRIME:
            return "(AF')"
        else:
            return "(%s)" % value[2:4]

    if param is P_REGISTER:
        if value is REG_AT_HL:
            return "(HL)"
        else:
            return value[2:]

    if param == P_IMMEDIATE_16:
        if isinstance(value, int):
            return hex_prefix + "%04X" % value
        else:
            return value

    if param == P_IMMEDIATE_16_INDIRECT:
        if isinstance(value, int):
            return "(" + hex_prefix + "%04X)" % value
        else:
            return "(" + value + ")"

    if param == P_IMMEDIATE_8:
        if as_char:
            return "'" + chr(value) + "'"
        else:
            return hex_prefix + "%02X" % value

    if param == P_IMMEDIATE_8_INDIRECT:
        return "(" + hex_prefix + "%02X)" % value

    if param == P_CONDITION:
        return value[5:]

    if param == P_DISPLACEMENT:
        return str(value)

    if param is P_REGISTER_INDEXED:
        register_pair, displacement = value
        sign = "+" if displacement >= 0 else "-"
        displacement = abs(displacement)
        return "(%s%s%s%02X)" % (register_pair[2:4], sign, hex_prefix, displacement)

    return None


def decoded_to_string(decoded, options=None):
    if options is None:
        options = dict()

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

    return mnemonic, param_str


class FromDecodedToStringTestCase(unittest.TestCase):
    def test_immediate_16(self):
        decoded = ('JP', None, None, P_IMMEDIATE_16, 4096)
        expected = ('JP', '0x1000')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_immediate_16_with_label(self):
        decoded = ('JP', None, None, P_IMMEDIATE_16, 'jump1000')
        expected = ('JP', 'jump1000')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_indirect_16_with_label(self):
        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16_INDIRECT, 'jump1000')
        expected = ('LD', 'SP,(jump1000)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_register_pair(self):
        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 32256)
        expected = ('LD', 'SP,0x7E00')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_register_pair_indirect(self):
        decoded = ('EX', P_REGISTER_PAIR_INDIRECT, REG_SP, P_REGISTER_PAIR, REG_HL)
        expected = ('EX', '(SP),HL')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_register_with_ld(self):
        decoded = ('LD', P_REGISTER, REG_A, P_REGISTER, REG_AT_HL)
        expected = ('LD', 'A,(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_register_with_cp(self):
        decoded = ('CP', P_REGISTER, REG_A, P_REGISTER, REG_AT_HL)
        expected = ('CP', 'A,(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_condition(self):
        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        expected = ('JP', 'NZ,0x2238')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_immediate_8(self):
        decoded = ('CP', P_REGISTER, REG_A, P_IMMEDIATE_8, 0x3A)
        expected = ('CP', 'A,0x3A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_immediate_8_as_char(self):
        decoded = ('CP', P_REGISTER, REG_A, P_IMMEDIATE_8, 0x20)
        expected = ('CP', "A,' '")

        output = decoded_to_string(decoded, {"as_char": True})
        self.assertEqual(expected, output)

    def test_immediate_8_indirect(self):
        decoded = ('OUT', P_IMMEDIATE_8_INDIRECT, 0xCF, P_REGISTER, REG_A)
        expected = ('OUT', '(0xCF),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_immediate_16_indirect(self):
        decoded = ('LD', P_IMMEDIATE_16_INDIRECT, 0x4890, P_REGISTER, REG_A)
        expected = ('LD', '(0x4890),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_displacement(self):
        decoded = ('JR', P_CONDITION, COND_NZ, P_DISPLACEMENT, -14)
        expected = ('JR', 'NZ,-14')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_index(self):
        decoded = ('LD', P_REGISTER, REG_A, P_REGISTER_INDEXED, (REG_IX, 3))
        expected = ('LD', 'A,(IX+0x03)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_alternate_hex_writing(self):
        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        expected = ('JP', 'NZ,$2238')

        output = decoded_to_string(decoded, {"hex_prefix": "$"})
        self.assertEqual(expected, output)

    def test_bc_written_c_in_out(self):
        decoded = ('OUT', P_REGISTER_PAIR_INDIRECT, REG_BC, P_REGISTER, REG_A)
        expected = ('OUT', '(C),A')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)

    def test_jp_hl_written_as_jp_at_hl(self):
        decoded = ('JP', None, None, P_REGISTER_PAIR, REG_HL)
        expected = ('JP', '(HL)')

        output = decoded_to_string(decoded)
        self.assertEqual(expected, output)


def inject_label_on_call(labels, decoded):
    mnemonic, p1, v1, p2, v2 = decoded

    new_v1 = v1
    if p1 is P_IMMEDIATE_16 or p1 is P_IMMEDIATE_16_INDIRECT:
        if mnemonic in ('JP', 'JR', 'CALL', 'RST') or v1 != 0:
            new_v1 = labels.get(v1, (v1, []))
            new_v1, _ = new_v1

    new_v2 = v2
    if p2 is P_IMMEDIATE_16 or p2 is P_IMMEDIATE_16_INDIRECT:
        if mnemonic in ('JP', 'JR', 'CALL', 'RST') or v2 != 0:
            new_v2 = labels.get(v2, (v2, []))
            new_v2, _ = new_v2

    return mnemonic, p1, new_v1, p2, new_v2


class InjectingLabelsTestCase(unittest.TestCase):
    def test_address_found_in_label_is_modified_to_label_name(self):
        labels = {0x2238: ('jump2238', [10]), }

        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 'jump2238')
        self.assertEqual(expected, decoded)

        decoded = ('JR', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('JR', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 'jump2238')
        self.assertEqual(expected, decoded)

        decoded = ('CALL', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('CALL', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 'jump2238')
        self.assertEqual(expected, decoded)

        decoded = ('RST', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2238)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('RST', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 'jump2238')
        self.assertEqual(expected, decoded)

    def test_address_not_found_in_label_is_not_modified(self):
        labels = {0x2238: ('jump2238', [10]), }

        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2240)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0x2240)
        self.assertEqual(expected, decoded)

    def test_address_in_immediate_values(self):
        labels = {0x7E00: ('someLabel', []), }

        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 32256)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 'someLabel')
        self.assertEqual(expected, decoded)

    def test_address_in_immediate_values_not_labeling_zero_except_for_jumps(self):
        labels = {0x0000: ('someLabel', []), }

        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 0)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16, 0)
        self.assertEqual(expected, decoded)

        decoded = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 0)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('JP', P_CONDITION, COND_NZ, P_IMMEDIATE_16, 'someLabel')
        self.assertEqual(expected, decoded)

    def test_address_in_indirect_values(self):
        labels = {0x7E00: ('someLabel', []), }

        decoded = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16_INDIRECT, 32256)
        decoded = inject_label_on_call(labels, decoded)

        expected = ('LD', P_REGISTER_PAIR, REG_SP, P_IMMEDIATE_16_INDIRECT, 'someLabel')
        self.assertEqual(expected, decoded)


if __name__ == '__main__':
    unittest.main()
