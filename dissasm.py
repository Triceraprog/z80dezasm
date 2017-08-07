from z80tools import decode_full
from z80opcode_strings import decoded_to_string, adjust_displacement
from analysis import mark_all_code_regions
from rom import Rom


def decode_code(pc, memory, options):
    decoded = decode_full(memory[pc:])
    decoded = adjust_displacement(decoded, pc)

    decoded_size = decoded[-1]

    byte_list = ["%02x" % x for x in memory[pc:pc+decoded_size]]
    byte_string = " ".join(byte_list)


    string = decoded_to_string(decoded[:-1], options=options)

    line = "{mnemonic:<8} {args:<15} ; {hex_prefix}{pc:0>4x} {bytes:<15} ;".format(
        hex_prefix=options.get("hex_prefix", "0x"),
        pc=pc,
        bytes=byte_string,
        mnemonic=string[0].lower(),
        args=string[1].lower())

    return decoded_size, line

def decode_data(pc, memory, options):
    data = memory[pc]
    line = "{mnemonic:<8} {hex_prefix}{data:0>2x}".format(
        mnemonic="defb",
        hex_prefix=options.get("hex_prefix", "0x"),
        data=data
        )
    return 1, line


def new_main():
    with open("vg5000_1.1.rom", "rb") as romFile:
        romContent = romFile.read()

    starting_addresses = [0x0000]

    rom = Rom(romContent)
    rom = mark_all_code_regions(rom, starting_addresses)

    for r in sorted(rom.ranges):
    # for r in rom.ranges:
        (begin, end), t = r
        output = "${:0>4x}-${:0>4x}".format(begin, end)
        print(output)


def main():
    with open("vg5000_1.1.rom", "rb") as romFile:
        romContent = romFile.read()

    size = len(romContent)

    data_ranges = {0x0003: 0x0008, 0x0026: 0x0028, 0x1148: 0x1945, 0x2000: 0x2214}
    hex_prefix = "$"

    options = {"hex_prefix": hex_prefix}

    decoding_function = decode_code

    pc = 0
    end_data_range = None
    while (pc < size):
        if pc in data_ranges:
            end_data_range = data_ranges[pc]
            decoding_function = decode_data

        if pc == end_data_range:
            decoding_function = decode_code

        decoded_size, line = decoding_function(pc, romContent, options)

        label = ""
        labeled_line = "{label:<12} {line}".format(label=label, line=line)

        print(labeled_line)

        if "TODO" in line:
            exit(1)

        if decoded_size == 0:
            exit(1)

        pc += decoded_size

if __name__ == '__main__':
    new_main()