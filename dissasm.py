from analysis import analysis
from comments_new import read_new_comment_file
from rom import Rom
from z80opcode_strings import decoded_to_string, inject_label_on_call, P_CONDITION


def memory_to_byte_list(memory, hex_prefix="", separator=" "):
    byte_list = [(hex_prefix + "%02x") % x for x in memory]
    byte_string = separator.join(byte_list)
    return byte_string


def get_label_and_x_ref(label, hex_prefix):
    label_name = ""
    label_references = ""
    if label:
        label_name, label_references = label
        label_name = label_name.lower() + ":"
        if label_references:
            label_references = "called from: " + ", ".join([hex_prefix + f"{a:>04x}" for a in label_references])

    return label_name, label_references


def create_online_comment(comments, label_references):
    comment_collection = [label_references] if label_references else []
    online_comment = [c for c_type, c in comments if c_type == "online" or c_type == "right"]
    comment_collection.extend(online_comment)

    adjusted_comments = []
    for comment in comment_collection:
        if isinstance(comment, str):
            adjusted_comments.append(comment.strip())
        elif isinstance(comment, list):
            for c in comment:
                adjusted_comments.append(c.strip())

    return adjusted_comments


def format_description(descriptions):
    result = []
    if descriptions:
        result.append(";")
        for desc in descriptions:
            result.extend(["; " + line.strip() for line in desc])
        result.append(";")

    return result


def get_partial_read_as(rom, address, size, decoded, options):
    byte_string = memory_to_byte_list(rom.memory[address:address + size])
    partial_string = decoded_to_string(decoded, options=options)

    return byte_string, partial_string


def write_comments_below(rom, address, comments, options):
    for comment in comments:
        tag, content = comment
        if tag == 'partial-instruction':
            byte_string, partial_string = get_partial_read_as(rom, address, content[-1], content[:-1], options)
            line = "{mnemonic:<8} {args:<20} ; {hex_prefix}{pc:0>4x} {bytes:<15} ; <-- reads as".format(
                hex_prefix=options.get("hex_prefix", "0x"),
                pc=address,
                bytes=byte_string,
                mnemonic=partial_string[0].lower(),
                args=partial_string[1].lower())
            labeled_line = "; {label:<10} {line}".format(label="", line=line)
            print(labeled_line)


def format_comments(list_of_comments, width):
    formatted_comments = []
    for comment in list_of_comments:
        if len(comment) <= width:
            formatted_comments.append(comment)
        else:
            while comment:
                if len(comment) > width:
                    break_position = comment[:width].rfind(' ')
                else:
                    break_position = len(comment)
                if break_position == -1:
                    formatted_comments.append(comment)
                    comment = ""
                else:
                    formatted_comments.append(comment[:break_position])
                    comment = comment[break_position + 1:]

    return formatted_comments


def print_common(rom, address):
    description = format_description(rom.get_description_at(address))
    if description:
        print("\n".join(description))


def print_code(rom, address, data, options):
    print_common(rom, address)

    hex_prefix = options.get("hex_prefix", "0x")
    label_name, label_references = get_label_and_x_ref(rom.get_label_at(address), hex_prefix)
    comments = rom.get_comments_at(address)

    decoded_size = data[-1]

    if "CHAR" in rom.get_directives_at(address):
        options = dict(options)
        options.update({'as_char': True})

    if "NOT_LABEL" in rom.get_directives_at(address):
        options = dict(options)
        options.update({'not_label': True})

    byte_string = memory_to_byte_list(rom.memory[address:address + decoded_size])

    if not options.get("not_label", False):
        decoded = inject_label_on_call(rom.labels, data[:-1])
    else:
        decoded = data[:-1]

    string = decoded_to_string(decoded, options=options)
    comments_on_the_right = create_online_comment(comments, label_references)
    comments_on_the_right = format_comments(comments_on_the_right, width=55)

    partial_instruction = [c for c in comments if c[0] == 'partial-instruction']
    partial_instruction_count = len(partial_instruction)
    if partial_instruction_count >= 1:
        assert (partial_instruction_count == 1)
        _, content = partial_instruction[0]
        byte_string, partial_string = get_partial_read_as(rom, address, content[-1], content[:-1], options)

        comment = "As: {mnemonic:<6} {args:<10} ; {bytes:<10} ; Next: {hex_prefix}{pc:0>4x}".format(
            hex_prefix=options.get("hex_prefix", "0x"),
            bytes=byte_string,
            mnemonic=partial_string[0].lower(),
            args=partial_string[1].lower(),
            pc=address + content[-1])
        comments_on_the_right.append(comment)

    first_line_of_comments = ""
    if comments_on_the_right:
        first_line_of_comments = comments_on_the_right[0]

    # Preserve casing in char arguments
    arguments = string[1]
    if arguments.count("'") == 2 and arguments.count(",") == 1:
        before_comma, after_comma = arguments.split(",")
        arguments = before_comma.lower() + "," + after_comma
    else:
        arguments = arguments.lower()

    line = "{mnemonic:<8} {args:<20} ; {hex_prefix}{pc:0>4x} {bytes:<15} ; {comment}".format(
        hex_prefix=options.get("hex_prefix", "0x"),
        pc=address,
        bytes=byte_string,
        mnemonic=string[0].lower(),
        args=arguments,
        comment=first_line_of_comments)

    labeled_line = "{label:<12} {line}".format(label=label_name, line=line)
    print(labeled_line)

    if comments_on_the_right:
        comments_on_the_right = comments_on_the_right[1:]
        while comments_on_the_right:
            comment_next_line = (" " * 67) + "; " + comments_on_the_right[0]
            print(comment_next_line)
            comments_on_the_right = comments_on_the_right[1:]

    # Now included in comments on the right
    # write_comments_below(rom, address, comments, options)

    if data[0] in ("RET", "RETI", "RETN") or (data[0] in ("JP", "JR") and data[1] != P_CONDITION):
        print()  # Blank line after return

    if "TODO" in line:
        exit(1)

    if decoded_size == 0:
        exit(1)


def print_data_line(data, size, comment, label, hex_prefix):
    line_data = data[:size]
    byte_string = memory_to_byte_list(line_data, hex_prefix, ",")

    character_list = [(chr(x) if (32 < x < 127) else ".") for x in line_data]
    character_string = "".join(character_list)

    line = "{mnemonic:<8} {data:<44} ; {char_string:10} ; {comment}".format(
        mnemonic="defb",
        data=byte_string,
        char_string=character_string,
        comment=comment
    )
    labeled_line = "{label:<12} {line}".format(label=label, line=line)
    print(labeled_line)


def print_data(rom, address, data, options):
    print_common(rom, address)

    hex_prefix = options.get("hex_prefix", "0x")
    label_name, label_references = get_label_and_x_ref(rom.get_label_at(address), hex_prefix)
    comments = rom.get_comments_at(address)

    data_per_line = 10

    comments_on_the_right = create_online_comment(comments, label_references)
    comments_on_the_right = format_comments(comments_on_the_right, width=55)

    while data:
        comment = "" if not comments_on_the_right else comments_on_the_right[0]

        print_data_line(data, data_per_line, comment, label_name, hex_prefix)

        comments_on_the_right = comments_on_the_right[1:]
        label_name = ""

        address += data_per_line
        data = data[data_per_line:]


def dump_undefined_labels(rom):
    memory_size = len(rom.memory)
    for label in rom.get_labels():
        address, (name, refs) = label
        if address >= memory_size or not rom.get_content_at(address):
            print(" " * 13 + "defc     " + name.lower() + "=${address:>04x}".format(address=address))


def read_new_comments():
    with open("new_comments.txt") as commentsFile:
        return read_new_comment_file(commentsFile)


def load_rom_with_comments():
    comments = read_new_comments()

    with open("vg5000_1.1.rom", "rb") as rom_file:
        rom_raw_content = rom_file.read()

    starting_addresses = get_starting_addresses(comments.all_directives())

    rom = Rom(rom_raw_content)
    rom = analysis(rom, starting_addresses)

    for address, label in comments.all_labels():
        rom.name_label(address, label)

    for address, comment in comments.all_texts():
        rom.add_comment(address, "right", comment.split("\n"))

    for address, comment in comments.all_descriptions():
        rom.add_description(address, comment.split("\n"))

    for address, directives in comments.all_directives():
        for directive in directives:
            rom.add_directive(address, directive)

    # for r in sorted(rom.ranges):
    #     (begin, end), t = r
    #     output = "${:0>4x}-${:0>4x} {}".format(begin, end, t)
    #     print(output)
    # exit()

    return rom, rom_raw_content, starting_addresses


def get_starting_addresses(directives):
    starting_addresses = [0x0000]
    # Adding RST addresses
    for rst in range(1, 8):
        starting_addresses.append(rst * 8)
    for address, directives in directives:
        if "CODE" in directives:
            starting_addresses.append(address)
    return starting_addresses


def main():
    hex_prefix = "$"
    options = {"hex_prefix": hex_prefix}

    rom, rom_content, _ = load_rom_with_comments()

    for content in rom.get_content(0, len(rom_content) + 1):
        address, region_type, data = content

        if region_type == 'code':
            print_code(rom, address, data, options)
        else:
            print_data(rom, address, data, options)

    dump_undefined_labels(rom)


if __name__ == '__main__':
    main()
