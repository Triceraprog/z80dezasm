import unittest

test_file_content = """
Label: $1000, Start
Comment: $1000
A comment on $1000

Label: $2000, Stop
"""


def read_comment_file(opened_file):
    lines = opened_file.readlines()
    return read_comment_file_contents(lines)


def read_comment_file_contents(lines):
    labels = []
    comments = []
    incomment = False

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
                incomment = (address, specifier, [])
        else:
            if incomment:
                if not stripped_line:
                    if incomment[2]:
                        comments.append(incomment)
                    incomment = None
                else:
                    address, specifier, lines = incomment
                    lines.append(line)
                    incomment = address, specifier, lines

    return comments, labels


class CommentReadingTestCase(unittest.TestCase):
    def test_can_read_an_empty_file(self):
        lines = [""]

        comments, labels = read_comment_file_contents(lines)
        self.assertEqual([], comments)
        self.assertEqual([], labels)

    def test_can_read_a_label(self):
        lines = ["Label: $1000, Start"]

        comments, labels = read_comment_file_contents(lines)
        self.assertEqual([], comments)
        self.assertEqual([(0x1000, "Start")], labels)

    def test_can_read_a_comment_without_specifier(self):
        lines = ["Comment: $1020", "This is a comment", "On several lines"]

        comments, labels = read_comment_file_contents(lines)
        self.assertEqual([(0x1020, "right", ["This is a comment", "On several lines"])], comments)
        self.assertEqual([], labels)

    def test_can_read_a_comment_with_specifier(self):
        lines = ["Comment: $1020/above", "This is a comment", "On several lines"]

        comments, labels = read_comment_file_contents(lines)
        self.assertEqual([(0x1020, "above", ["This is a comment", "On several lines"])], comments)
        self.assertEqual([], labels)


if __name__ == '__main__':
    unittest.main()
