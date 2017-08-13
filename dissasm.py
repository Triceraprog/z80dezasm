from z80tools import decode_full
from z80opcode_strings import decoded_to_string, inject_label_on_call
from analysis import mark_all_code_regions, mark_all_data_regions, detect_partial_instructions, inject_instructions_on_missing_labels
from rom import Rom
from comments import read_comment_file
import itertools


def memory_to_byte_list(memory, hex_prefix="", separator=" "):
    byte_list = [(hex_prefix+"%02x") % x for x in memory]
    byte_string = separator.join(byte_list)
    return byte_string


def get_label_and_x_ref(label, hex_prefix):
    if label:
        label_name, label_references = label
        label_name += ":"
        label_name = label_name.lower()
        label_references = "called from: " + ",".join([hex_prefix + "{:>04x}".format(a) for a in label_references])
    else:
        label_name = ""
        label_references = ""

    return label_name, label_references


def create_online_comment(comments, label_references):
    comment = label_references if label_references else ""
    online_comment = [c for c_type, c in comments if c_type == "online"]

    if online_comment:
        comment += online_comment[0]

    return comment


def write_comments_below(rom, address, comments, options):
    for comment in comments:
        tag, content = comment
        if tag == 'partial-instruction':
            byte_string = memory_to_byte_list(rom.memory[address:address+content[-1]])
            partial_string = decoded_to_string(content[:-1], options=options)
            line = "{mnemonic:<8} {args:<15} ; {hex_prefix}{pc:0>4x} {bytes:<15} ; <-- reads as".format(
                hex_prefix=options.get("hex_prefix", "0x"),
                pc=address,
                bytes=byte_string,
                mnemonic=partial_string[0].lower(),
                args=partial_string[1].lower())
            labeled_line = "; {label:<10} {line}".format(label="", line=line)
            print(labeled_line)


def print_code(rom, address, data, options):
    hex_prefix=options.get("hex_prefix", "0x")
    label_name, label_references = get_label_and_x_ref(rom.get_label_at(address), hex_prefix)
    comments = rom.get_comments_at(address)

    decoded_size = data[-1]

    byte_string = memory_to_byte_list(rom.memory[address:address+decoded_size])
    decoded = inject_label_on_call(rom.labels, data[:-1])
    string = decoded_to_string(decoded, options=options)
    comment = create_online_comment(comments, label_references)

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

    write_comments_below(rom, address, comments, options)

    if "TODO" in line:
        exit(1)

    if decoded_size == 0:
        exit(1)


def print_data(rom, address, data, options):
    hex_prefix=options.get("hex_prefix", "0x")
    label_name, label_references = get_label_and_x_ref(rom.get_label_at(address), hex_prefix)
    comments = rom.get_comments_at(address)

    data_per_line = 10

    comment = create_online_comment(comments, label_references)

    while data:
        line_data = data[:data_per_line]
        byte_string = memory_to_byte_list(line_data, hex_prefix, ",")

        character_list = [(chr(x) if (x > 32 and x < 127) else ".") for x in line_data]
        character_string = "".join(character_list)

        line = "{mnemonic:<8} {data:<39} ; {char_string:10} ; {comment}".format(
            mnemonic="defb",
            data=byte_string,
            char_string=character_string,
            comment=comment
            )
        labeled_line = "{label:<12} {line}".format(label=label_name, line=line)
        print(labeled_line)

        comment = ""

        address += data_per_line
        data = data[data_per_line:]


def dump_undefined_labels(rom):
    memory_size = len(rom.memory)
    for label in rom.get_labels():
        address, (name, refs) = label
        if address > memory_size or not rom.get_content_at(address):
            print(" " * 13 + "defc     " + name.lower() + "=${address:>04x}".format(address=address))

def main():
    hex_prefix = "$"
    options = {"hex_prefix": hex_prefix}

    with open("comments.txt") as commentsFile:
        user_comments, user_labels= read_comment_file(commentsFile)

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

    for label in user_labels:
        address, name = label
        rom.name_label(address, name)

    # for r in sorted(rom.ranges):
    #     (begin, end), t = r
    #     output = "${:0>4x}-${:0>4x} {}".format(begin, end, t)
    #     print(output)
    # exit()

    for content in rom.get_content(0, len(romContent) + 1):
        address, region_type, data = content

        if region_type == 'code':
            print_code(rom, address, data, options)
        else:
            print_data(rom, address, data, options)

    dump_undefined_labels(rom)


if __name__ == '__main__':
    main()