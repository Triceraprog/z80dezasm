from dissasm import load_rom_with_comments


def print_for_address(rom, address, code):
    annotation_lines = []
    header_lines = []
    directives = []

    address_str = f"${hex(address)[2:]:0>4}"
    label_information = rom.get_label_at(address)
    label, _ = label_information if label_information else (None, None)

    comments = rom.get_comments_at(address)
    for comment in comments:
        position, content = comment
        if position == 'above':
            header_lines.extend(content)
        elif position == 'right':
            annotation_lines.extend(content)
        elif position == 'online' or position == 'partial-instruction':
            # Does nothing, these comments are generated
            pass
        else:
            raise AssertionError(f"Unknown position {position}")

    if code:
        directives.append("CODE")

    if directives:
        directives_str = "%" + ",".join(directives)
        if header_lines:
            header_lines.insert(0, directives_str)
        else:
            annotation_lines.insert(0, directives_str)

    if label:
        if header_lines:
            header_lines.insert(0, f"[{label}]")
        else:
            annotation_lines.insert(0, f"[{label}]")

    if not annotation_lines:
        annotation_lines.append("---")

    if header_lines:
        print()

    for index, line in enumerate(header_lines):
        line = line.rstrip()
        if line.strip() == ';':
            line = ""
        if index == 0:
            print(f"{address_str:<12}{line}")
        else:
            print(f"{'':<12}{line}")

    for index, line in enumerate(annotation_lines):
        line = line.rstrip()
        if index == 0:
            print(f"{address_str:<12}{line}")
        else:
            print(f"{'':<12}{line}")


def main():
    rom, rom_content, starting_addresses = load_rom_with_comments()

    for content in rom.get_content(0, len(rom_content) + 1):
        address, region_type, data = content
        print_for_address(rom, address, address in starting_addresses)

    memory_size = len(rom.memory)
    for label in rom.get_labels():
        address, (name, refs) = label
        if address >= memory_size or not rom.get_content_at(address):
            print_for_address(rom, address, address in starting_addresses)


if __name__ == '__main__':
    main()
