from analysis import analysis
from comments_new import read_new_comment_file
from rom import Rom
from z80opcode_strings import decoded_to_string, inject_label_on_call, find_reserved_label_conflicts, P_CONDITION

comment_leftovers = []
comment_end_address = 0


def memory_to_byte_list(memory, hex_prefix="", separator=" "):
    try:
        byte_list = [(hex_prefix + "%02x") % x for x in memory]
    except TypeError:
        print(f"Memory is not data : {memory}")
        raise
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
    online_comment = [c for c_type, c, end_address in comments if c_type == "online" or c_type == "right"]
    end_address = max((end for c_type, _, end in comments if c_type == "online" or c_type == "right"), default=0)
    comment_collection.extend(online_comment)

    adjusted_comments = []
    for comment in comment_collection:
        if isinstance(comment, str):
            adjusted_comments.append(comment.strip())
        elif isinstance(comment, list):
            for c in comment:
                adjusted_comments.append(c.strip())

    return adjusted_comments, end_address


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


def print_code(rom: Rom, address, data, options):
    global comment_leftovers, comment_end_address

    print_common(rom, address)

    hex_prefix = options.get("hex_prefix", "0x")

    label_name, label_references = get_label_and_x_ref(rom.get_label_at(address), hex_prefix)

    if not options.get("cross_ref", False):
        label_references = []

    comments = rom.get_comments_at(address)

    decoded_size = data[-1]

    if "CHAR" in rom.get_tags_at(address):
        options = dict(options)
        options.update({'as_char': True})

    if "NOT_LABEL" in rom.get_tags_at(address):
        options = dict(options)
        options.update({'not_label': True})

    byte_string = memory_to_byte_list(rom.memory[address:address + decoded_size])

    if not options.get("not_label", False):
        conflicts = find_reserved_label_conflicts(rom.labels, data[:-1])
        decoded = inject_label_on_call(rom.labels, data[:-1])
    else:
        conflicts = []
        decoded = data[:-1]

    string = decoded_to_string(decoded, options=options)
    comments_on_the_right, end_address = create_online_comment(comments, label_references)
    comments_on_the_right = format_comments(comments_on_the_right, width=70)

    for addr, name in conflicts:
        comments_on_the_right.append(f"'{name}' (${addr:04x}) skipped: sjasmplus reserved keyword")

    partial_instruction = [c for c in comments if c[0] == 'partial-instruction']
    partial_instruction_count = len(partial_instruction)
    if partial_instruction_count >= 1:
        assert (partial_instruction_count == 1)
        _, content, end_address = partial_instruction[0]
        byte_string, partial_string = get_partial_read_as(rom, address, content[-1], content[:-1], options)

        comment = "As: {mnemonic:<6} {args:<10} ; {bytes:<10} ; Next: {hex_prefix}{pc:0>4x}".format(
            hex_prefix=options.get("hex_prefix", "0x"),
            bytes=byte_string,
            mnemonic=partial_string[0].lower(),
            args=partial_string[1].lower(),
            pc=address + content[-1])
        comments_on_the_right.append(comment)

    starting_comment_line = False
    ending_comment_line = False
    continuing_comment_line = False
    if (len(comment_leftovers) == 0 and end_address != address and len(comments_on_the_right) > 0) or \
        len(comments_on_the_right) > 1:
        starting_comment_line = True
    if address == comment_end_address and len(comment_leftovers) <= 1:
        ending_comment_line = True
    if address <= comment_end_address and not starting_comment_line and not ending_comment_line:
        continuing_comment_line = True

    comments_on_the_right.extend(comment_leftovers)

    first_line_of_comments = ""
    if comments_on_the_right:
        first_line_of_comments = comments_on_the_right[0]
        if ending_comment_line:
            first_line_of_comments = r"\ " + first_line_of_comments
        elif continuing_comment_line:
            first_line_of_comments = "| " + first_line_of_comments
        elif starting_comment_line and not ending_comment_line:
            first_line_of_comments = "/ " + first_line_of_comments
        else:
            first_line_of_comments = "  " + first_line_of_comments
    else:
        if continuing_comment_line:
            first_line_of_comments = "| "
        elif starting_comment_line:
            first_line_of_comments = "/ "
        elif ending_comment_line:
            first_line_of_comments = r"\ "

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

    comment_end_address = end_address if end_address != 0 else comment_end_address

    if comments_on_the_right:
        comments_on_the_right = comments_on_the_right[1:]
        if address == comment_end_address:
            while comments_on_the_right:
                continuation = "| " if len(comments_on_the_right) > 1 else r"\ "
                comment_next_line = (" " * 67) + "; " + continuation + comments_on_the_right[0]
                print(comment_next_line)
                comments_on_the_right = comments_on_the_right[1:]
            comment_end_address = 0
            comment_leftovers = []
        else:
            comment_leftovers = list(comments_on_the_right)
            # comment_end_address = end_address if end_address != 0 else comment_end_address

    # Now included in comments on the right
    # write_comments_below(rom, address, comments, options)

    if data[0] in ("RET", "RETI", "RETN") or (data[0] in ("JP", "JR") and data[1] != P_CONDITION):
        print()  # Blank line after return

    if "TODO" in line:
        exit(1)

    if decoded_size == 0:
        exit(1)


_MIN_STRING_LENGTH = 4
_DEFM_MAX_CHARS = 40

# VG5000µ special characters used in French text (byte value → display char)
_VG5000_CHAR_DISPLAY = {
    0x11: 'î',
    0x12: 'é',
    0x1b: 'ê',
}
_VG5000_TEXT_CHARS = set(_VG5000_CHAR_DISPLAY.keys())


def _is_printable(byte):
    return 32 <= byte <= 126


def _display_char(byte):
    """Return a human-readable character for use in comments."""
    if byte in _VG5000_CHAR_DISPLAY:
        return _VG5000_CHAR_DISPLAY[byte]
    return chr(byte) if _is_printable(byte) else '.'


def _split_data_into_segments(data):
    """Split data into ('string', bytes) or ('bytes', bytes) segments.
    A 'string' segment contains >= _MIN_STRING_LENGTH printable ASCII bytes,
    potentially interleaved with VG5000 special text characters."""
    n = len(data)
    in_string = [False] * n

    i = 0
    while i < n:
        if _is_printable(data[i]) or data[i] in _VG5000_TEXT_CHARS:
            j = i
            while j < n and (_is_printable(data[j]) or data[j] in _VG5000_TEXT_CHARS):
                j += 1
            printable_count = sum(1 for k in range(i, j) if _is_printable(data[k]))
            if printable_count >= _MIN_STRING_LENGTH:
                for k in range(i, j):
                    in_string[k] = True
            i = j
        else:
            i += 1

    segments = []
    i = 0
    while i < n:
        if in_string[i]:
            j = i
            while j < n and in_string[j]:
                j += 1
            segments.append(('string', data[i:j]))
            i = j
        else:
            j = i
            while j < n and not in_string[j]:
                j += 1
            segments.append(('bytes', data[i:j]))
            i = j

    return segments


def _apply_null_termination(segments):
    """Convert ('string', s) followed by a bytes segment starting with $00
    into ('nullstring', s), consuming that $00 from the bytes segment."""
    segments = list(segments)
    result = []
    i = 0
    while i < len(segments):
        seg_type, seg_data = segments[i]
        if (seg_type == 'string'
                and i + 1 < len(segments)
                and segments[i + 1][0] == 'bytes'
                and segments[i + 1][1][0:1] == b'\x00'):
            result.append(('nullstring', seg_data))
            tail = segments[i + 1][1][1:]
            if tail:
                segments[i + 1] = ('bytes', tail)
            else:
                i += 1  # skip now-empty bytes segment
        else:
            result.append((seg_type, seg_data))
        i += 1
    return result


def _defm_arg(string_data):
    """Build sjasmplus DEFM argument.
    Double-quote bytes become $22; VG5000 special chars become $xx."""
    parts = []
    i = 0
    while i < len(string_data):
        b = string_data[i]
        if b == 0x22 or b in _VG5000_TEXT_CHARS:
            parts.append(f"${b:02x}")
            i += 1
        else:
            j = i
            while j < len(string_data) and string_data[j] != 0x22 and string_data[j] not in _VG5000_TEXT_CHARS:
                j += 1
            parts.append('"' + "".join(chr(x) for x in string_data[i:j]) + '"')
            i = j
    return ",".join(parts)


def print_defm_line(string_data, comment, label, hex_prefix, null_terminated=False):
    defm_arg = _defm_arg(string_data)
    if null_terminated:
        defm_arg += ",0"

    line = "{mnemonic:<8} {data:<57} ; {comment}".format(
        mnemonic="defm",
        data=defm_arg,
        comment=comment
    )
    labeled_line = "{label:<12} {line}".format(label=label, line=line).rstrip()
    print(labeled_line)


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
    if not options.get("cross_ref", False):
        label_references = []

    comments = rom.get_comments_at(address)

    data_per_line = 10

    comments_on_the_right, end_address = create_online_comment(comments, label_references)
    comments_on_the_right = format_comments(comments_on_the_right, width=70)

    if rom.is_in_nostring_region(address):
        segments = [('bytes', data)]
    else:
        segments = _apply_null_termination(_split_data_into_segments(data))

    for seg_type, seg_data in segments:
        if seg_type in ('string', 'nullstring'):
            null_terminated = (seg_type == 'nullstring')
            chunk_data = seg_data
            while chunk_data:
                comment = "" if not comments_on_the_right else comments_on_the_right[0]
                is_last_chunk = len(chunk_data) <= _DEFM_MAX_CHARS
                print_defm_line(chunk_data[:_DEFM_MAX_CHARS], comment, label_name, hex_prefix,
                                null_terminated=(null_terminated and is_last_chunk))
                comments_on_the_right = comments_on_the_right[1:]
                label_name = ""
                chunk_data = chunk_data[_DEFM_MAX_CHARS:]
        else:
            chunk_data = seg_data
            while chunk_data:
                comment = "" if not comments_on_the_right else comments_on_the_right[0]
                print_data_line(chunk_data, data_per_line, comment, label_name, hex_prefix)
                comments_on_the_right = comments_on_the_right[1:]
                label_name = ""
                chunk_data = chunk_data[data_per_line:]

    while comments_on_the_right:
        comment_next_line = (" " * 80) + "; " + comments_on_the_right[0]
        print(comment_next_line)
        comments_on_the_right = comments_on_the_right[1:]


def dump_undefined_labels(rom):
    from z80opcode_strings import _SJASMPLUS_RESERVED
    memory_size = len(rom.memory)
    for label in rom.get_labels():
        address, (name, refs) = label
        if address >= memory_size or not rom.get_content_at(address):
            if name.lower() not in _SJASMPLUS_RESERVED:
                print(f"{name.lower():<12} {'EQU':<8} ${address:04x}")
            else:
                print(f"; '{name.lower()}' (${address:04x}) skipped: sjasmplus reserved keyword")


def read_new_comments(comments_filename="new_comments.txt"):
    with open(comments_filename) as commentsFile:
        return read_new_comment_file(commentsFile)


def load_rom_with_comments(rom_filename, comments_filename):
    comments = read_new_comments(comments_filename)

    with open(rom_filename, "rb") as rom_file:
        rom_raw_content = rom_file.read()

    data_skip_regions = get_data_skip_regions(comments.all_tags())
    starting_addresses = get_starting_addresses(comments.all_tags(), data_skip_regions)

    rom = Rom(rom_raw_content)
    rom = analysis(rom, starting_addresses, data_skip_regions)

    for address, label in comments.all_labels():
        rom.name_label(address, label)

    for address, comment in comments.all_texts():
        end_address = comments.end_address_for_comment_at(address)
        rom.add_comment(address, "right", comment.split("\n"), end_address)

    for address, comment in comments.all_descriptions():
        rom.add_description(address, comment.split("\n"))

    for address, tags in comments.all_tags():
        for tag in tags:
            rom.add_tag(address, tag)
            if tag == 'NOSTRING':
                end = comments.end_address_for_comment_at(address)
                rom.add_nostring_region(address, end)

    # for r in sorted(rom.regions):
    #     (begin, end), t = r
    #     output = "${:0>4x}-${:0>4x} {}".format(begin, end, t)
    #     print(output)
    # exit()

    return rom, rom_raw_content, starting_addresses


def get_starting_addresses(tags, data_skip_regions=None):
    if data_skip_regions is None:
        data_skip_regions = []

    starting_addresses = [0x0000]
    # Adding RST addresses
    for rst in range(1, 8):
        starting_addresses.append(rst * 8)

    # Adding specific CODE parts
    for address, tags in tags:
        if "CODE" in tags:
            starting_addresses.append(address)

    # Adding starting addresses generated by skipping data
    for address, size in data_skip_regions:
        starting_addresses.append(address + size)

    return starting_addresses


def get_data_skip_regions(tags):
    # Data Skip are data intertwined in code parts with PC manipulation
    # They generate a starting address after their region
    data_regions = []
    for address, tags in tags:
        for tag in tags:
            if tag.startswith("DATASKIP"):
                closing_parenthesis = tag.find(")")
                if closing_parenthesis == -1:
                    size = 1
                else:
                    opening_parenthesis = tag.find("(")
                    size = int(tag[opening_parenthesis + 1:closing_parenthesis])
                data_regions.append((address, size))

    return data_regions


def main(rom_filename, comments_filename, cross_ref):
    hex_prefix = "$"
    options = {"hex_prefix": hex_prefix,
               "cross_ref": cross_ref}

    rom, rom_content, _ = load_rom_with_comments(rom_filename, comments_filename)

    print("    OPT --syntax=a")
    print("    ORG $0000")
    print()

    for content in rom.get_content(0, len(rom_content) + 1):
        address, region_type, data = content

        if region_type == 'code':
            print_code(rom, address, data, options)
        else:
            print_data(rom, address, data, options)

    dump_undefined_labels(rom)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--romfile', type=str)
    parser.add_argument('--crossref', type=bool)
    parser.add_argument('--comments', type=str)

    args = parser.parse_args()

    main(rom_filename=args.romfile, comments_filename=args.comments, cross_ref=args.crossref)
