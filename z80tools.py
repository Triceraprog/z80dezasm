import unittest

# with open("vg5000_1.1.rom", "rb") as romFile:
#    romContent = romFile.read()


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

# Format (x, z, y, "NAME")
# Format (x, z, q, p, "NAME")
# NAME = OP nn
# (0, 0, 0, "NOP")
# (0, 0, 0, "NOP")

table = [(0, 0, 0, "NOP"),
         (3, 1, 1, 0, "RET")]


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
            if len(entry) == 4:
                if entry[2] == splitted_opcode_2[2]:
                    return entry[3]
            elif len(entry) == 5:
                if entry[2:3] == splitted_opcode_2[3:4]:
                    return entry[4]

    if splitted_opcode[0] == 3:
        if splitted_opcode[2] == 3:
            if splitted_opcode[1] == 0:
                if len(memory) < 3:
                    return "NOT ENOUGH MEMORY FOR DECODING JP"

                operand_16bits = memory[1] + (memory[2] << 8)
                return "JP 0x%04x" % operand_16bits

    return "DECODE ERROR"


class DecodeTestCase(unittest.TestCase):
    def test_decode_of_nop(self):
        memory = [0]
        self.assertEqual("NOP", decode(memory))

    def test_decode_of_ret(self):
        memory = [0xC9]
        self.assertEqual("RET", decode(memory))

    def test_decode_of_jp_direct(self):
        memory = [0xC3, 0x00, 0x10]
        self.assertEqual("JP 0x1000", decode(memory))

if __name__ == '__main__':
    unittest.main()
