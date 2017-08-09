from z80tools import decode_full
from z80opcode_strings import decoded_to_string, adjust_displacement
from analysis import mark_all_code_regions, mark_all_data_regions, detect_partial_instructions, inject_instructions_on_missing_labels
from rom import Rom


def new_main():
    hex_prefix = "$"
    options = {"hex_prefix": hex_prefix}

    with open("vg5000_1.1.rom", "rb") as romFile:
        romContent = romFile.read()

    starting_addresses = [0x0000]

    # Adding RST addresses
    for rst in range(1, 8):
        starting_addresses.append(rst * 8)

    rom = Rom(romContent)
    rom = mark_all_code_regions(rom, starting_addresses)
    rom = mark_all_data_regions(rom)
    rom = inject_instructions_on_missing_labels(rom)
    rom = detect_partial_instructions(rom)

    # for r in sorted(rom.ranges):
    #     (begin, end), t = r
    #     output = "${:0>4x}-${:0>4x} {}".format(begin, end, t)
    #     print(output)
    # exit()

    for content in rom.get_content(0, len(romContent) + 1):
        address, region_type, data = content
        label = rom.get_label_at(address)
        comments = rom.get_comments_at(address)

        if label:
            label_name, label_references = label
            label_name += ":"
            label_references = "called from: " + ",".join([hex_prefix + "{:>04x}".format(a) for a in label_references])
        else:
            label_name = ""
            label_references = ""

        if region_type == 'code':
            decoded_size = data[-1]

            byte_list = ["%02x" % x for x in romContent[address:address+decoded_size]]
            byte_string = " ".join(byte_list)

            string = decoded_to_string(data[:-1], options=options)

            if label_references:
                comment = label_references
            else:
                comment = ""

            online_comment = [comment for comment in comments if comment[0] == "online"]

            if online_comment:
                comment += online_comment[0][1]

            line = "{mnemonic:<8} {args:<15} ; {hex_prefix}{pc:0>4x} {bytes:<15} ; {comment}".format(
                hex_prefix=options.get("hex_prefix", "0x"),
                pc=address,
                bytes=byte_string,
                mnemonic=string[0].lower(),
                args=string[1].lower(),
                comment=comment[:60])

            labeled_line = "{label:<12} {line}".format(label=label_name, line=line)
            print(labeled_line)

            comment = comment[60:]
            while len(comment):
                comment_next_line = (" " * 62) + "; " + comment[:60]
                print(comment_next_line)
                comment = comment[60:]

            for comment in comments:
                tag, content = comment
                if tag == 'partial-instruction':
                    byte_list = ["%02x" % x for x in romContent[address:address+content[-1]]]
                    byte_string = " ".join(byte_list)
                    partial_string = decoded_to_string(content[:-1], options=options)
                    line = "{mnemonic:<8} {args:<15} ; {hex_prefix}{pc:0>4x} {bytes:<15} ; <-- reads as".format(
                        hex_prefix=options.get("hex_prefix", "0x"),
                        pc=address,
                        bytes=byte_string,
                        mnemonic=partial_string[0].lower(),
                        args=partial_string[1].lower())
                    labeled_line = "; {label:<10} {line}".format(label="", line=line)
                    print(labeled_line)


            if "TODO" in line:
                exit(1)

            if decoded_size == 0:
                exit(1)

        else:
            hex_prefix = options.get("hex_prefix", "0x")
            data_per_line = 10

            if label_references:
                comment = label_references
            else:
                comment = ""

            while data:
                line_data = data[:data_per_line]
                byte_list = [(hex_prefix + "%02x" % x) for x in line_data]
                byte_string = ",".join(byte_list)

                character_list = [(chr(x) if (x > 32 and x < 127) else ".") for x in line_data]
                character_string = "".join(character_list)

                line = "{mnemonic:<8} {data:<39} ; {char_string:10} ; {comment}".format(
                    mnemonic="defb",
                    data=byte_string,
                    char_string=character_string,
                    comment=comment
                    )
                labeled_line = "{label:<12} {line}".format(label=label_name, line=line)

                if comment:
                    comment = ""

                address += 10
                data = data[data_per_line:]

                print(labeled_line)


if __name__ == '__main__':
    new_main()