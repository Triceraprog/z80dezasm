HEXADECIMAL_MARKER = '$'


def get_hexadecimal_from_string(s: str):
    """Gets a string representing a maximum 16 bit long hexadecimal number starting with a specific character.
     Returns the number as integer or throws ValueError. """

    if len(s) > 0 and s[0] != HEXADECIMAL_MARKER:
        raise ValueError(f"Number should start with '{HEXADECIMAL_MARKER}' but starts with '{s[0]}'")

    return int(s[1:5], 16)


def get_starting_address(line):
    """ Checks if the line starts with a memory address in hexadecimal.
        The address must be on the first column. """
    try:
        potential_address = get_hexadecimal_from_string(line[0:5])
    except ValueError:
        return False, 0

    return True, potential_address


COMMENT_TYPE_LABEL = "LABEL"
COMMENT_TYPE_TEXT = "TEXT"
COMMENT_TYPE_TAG = "TAG"
COMMENT_TYPE_ERROR = "ERROR"


def get_type_and_content(s: str):
    """ Gets a stripped comment string and returns it's type, and it's extracted content. """
    if len(s) == 0:
        return COMMENT_TYPE_TEXT, ""

    assert (len(s) > 0 and not s[0].isspace())

    if s[0] == '[':
        if s[-1] == ']':
            return COMMENT_TYPE_LABEL, s[1:-1]
        else:
            return COMMENT_TYPE_ERROR, s
    elif s[0] == '%':
        return COMMENT_TYPE_TAG, s[1:].split(',')
    else:
        return COMMENT_TYPE_TEXT, s


class NewCommentParser:
    def __init__(self):
        self.labels = {}
        self.texts = {}
        self.tags = {}
        self.descriptions = {}
        self.end_address = {}

        self.text_accumulator = []
        self.current_address = 0
        self.current_type = ""

    def __agglomerate_text(self, new_text):
        self.text_accumulator.append(new_text)
        return "\n".join(self.text_accumulator).rstrip()

    def feed(self, line: str):
        starts_with_address, address = get_starting_address(line)
        if starts_with_address:
            self.current_address = address
            self.text_accumulator = []
            second_part_position = 5

            if line[5] == '-':
                has_second_address, end_address = get_starting_address(line[6:])

                if has_second_address:
                    second_part_position = 11
                    self.end_address[address] = end_address

            second_part = line[second_part_position:].strip()

            t, content = get_type_and_content(second_part)
            if t is COMMENT_TYPE_LABEL:
                self.labels[address] = content
            elif t is COMMENT_TYPE_TEXT:
                agglomerated_text = self.__agglomerate_text(content)
                self.texts[address] = agglomerated_text
            elif t is COMMENT_TYPE_TAG:
                self.tags[address] = content
            self.current_type = t
        else:
            t, content = get_type_and_content(line.strip())

            if t is COMMENT_TYPE_TAG:
                self.tags[self.current_address] = content
            else:
                agglomerated_text = self.__agglomerate_text(content)

                if len(agglomerated_text) > 0:
                    if self.current_type is COMMENT_TYPE_LABEL:
                        self.descriptions[self.current_address] = agglomerated_text
                    else:
                        self.texts[self.current_address] = agglomerated_text

    def get_label_at(self, addr: int):
        return self.labels.get(addr)

    def get_comment_at(self, addr: int):
        return self.texts.get(addr)

    def get_tags_at(self, addr: int):
        return self.tags.get(addr)

    def get_description_at(self, addr: int):
        return self.descriptions.get(addr)

    def is_multiline(self, addr: int):
        return addr in self.end_address

    def end_address_for_comment_at(self, addr: int):
        if self.is_multiline(addr):
            return self.end_address.get(addr)
        else:
            return addr

    def all_labels(self):
        return self.labels.items()

    def all_texts(self):
        return self.texts.items()

    def all_tags(self):
        return self.tags.items()

    def all_descriptions(self):
        return self.descriptions.items()


def read_new_comment_file(opened_file):
    c = NewCommentParser()
    for line_from_file in opened_file:
        if line_from_file.startswith("STOP"):
            break
        c.feed(line_from_file)

    return c
