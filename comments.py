import unittest


def read_comment_file(opened_file):
    lines = opened_file.readlines()
    return read_comment_file_contents(lines)


def read_comment_file_contents(lines):
    labels = []
    comments = []
    entries = []
    in_comment = False

    lines.append("")  # To be sure the last comment is taken

    for line in lines:
        if line.startswith("//"):
            continue

        stripped_line = line.strip()
        if line.startswith("Label: "):
            parameters = stripped_line[7:]
            comma = parameters.find(",")
            if comma != -1:
                address = parameters[:comma].strip()
                name = parameters[comma + 1:].strip()

                if address:
                    if address[0] != "$":
                        print("Please use $ for specifying hex addresses: " + line)
                    else:
                        address = int(address[1:], 16)

                        labels.append((address, name))

            else:
                print("Cannot parse line: " + line)

        elif line.startswith("Comment: "):
            parameters = stripped_line[9:]
            slash = parameters.find("/")
            specifier = "right"

            if slash != -1:
                address = parameters[:slash].strip()
                specifier = parameters[slash + 1:].strip()
            else:
                address = parameters.strip()

            if address[0] != "$":
                print("Please use $ for specifying hex addresses: " + line)
            else:
                address = int(address[1:], 16)
                in_comment = (address, specifier, [])

        elif line.startswith("Code: "):
            parameters = stripped_line[6:].strip()
            address = parameters
            if address[0] != "$":
                print("Please use $ for specifying hex addresses: " + line)
            else:
                address = int(address[1:], 16)
                entries.append((address, 'code'))

        else:
            if in_comment:
                if not stripped_line:
                    if in_comment[2]:
                        comments.append(in_comment)
                    in_comment = None
                else:
                    address, specifier, lines = in_comment
                    lines.append(line)
                    in_comment = address, specifier, lines

    return comments, labels, entries


class CommentReadingTestCase(unittest.TestCase):
    def test_can_read_an_empty_file(self):
        lines = [""]

        comments, labels, entries = read_comment_file_contents(lines)
        self.assertEqual([], comments)
        self.assertEqual([], labels)
        self.assertEqual([], entries)

    def test_can_read_a_label(self):
        lines = ["Label: $1000, Start"]

        comments, labels, entries = read_comment_file_contents(lines)
        self.assertEqual([], comments)
        self.assertEqual([(0x1000, "Start")], labels)
        self.assertEqual([], entries)

    def test_can_read_a_comment_without_specifier(self):
        lines = ["Comment: $1020", "This is a comment", "On several lines"]

        comments, labels, entries = read_comment_file_contents(lines)
        self.assertEqual([(0x1020, "right", ["This is a comment", "On several lines"])], comments)
        self.assertEqual([], labels)
        self.assertEqual([], entries)

    def test_can_read_a_comment_with_specifier(self):
        lines = ["Comment: $1020/above", "This is a comment", "On several lines"]

        comments, labels, entries = read_comment_file_contents(lines)
        self.assertEqual([(0x1020, "above", ["This is a comment", "On several lines"])], comments)
        self.assertEqual([], labels)
        self.assertEqual([], entries)
        
    def test_can_read_a_code_entry(self):
        lines = ["Code: $2250"]

        comments, labels, entries = read_comment_file_contents(lines)
        self.assertEqual([(0x2250, "code")], entries)
        self.assertEqual([], labels)
        self.assertEqual([], comments)


if __name__ == '__main__':
    unittest.main()
