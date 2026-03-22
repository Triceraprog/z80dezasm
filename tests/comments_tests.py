import unittest

from z80decomp.comments import get_starting_address, get_type_and_content, COMMENT_TYPE_LABEL, COMMENT_TYPE_ERROR, \
    COMMENT_TYPE_TEXT, COMMENT_TYPE_TAG, NewCommentParser


class UtilityFunctionTestCase(unittest.TestCase):
    def test_can_check_starting_address(self):
        s = r"$0008		[chk_chr]"
        ok, addr = get_starting_address(s)

        self.assertTrue(ok)
        self.assertEqual(0x0008, addr)

    def test_can_check_not_starting_address(self):
        s = r"       [chk_chr]"
        ok, addr = get_starting_address(s)

        self.assertFalse(ok)


class ExtractCommentTestCase(unittest.TestCase):
    def test_can_extract_a_label(self):
        t, c = get_type_and_content("[label]")

        self.assertIs(COMMENT_TYPE_LABEL, t)
        self.assertEqual("label", c)

    def test_verifies_label_syntax(self):
        t, c = get_type_and_content("[label")

        self.assertIs(COMMENT_TYPE_ERROR, t)
        self.assertEqual("[label", c)

    def test_can_extract_text(self):
        t, c = get_type_and_content("This is some text")

        self.assertIs(COMMENT_TYPE_TEXT, t)
        self.assertEqual("This is some text", c)

    def test_can_extract_tags(self):
        t, c = get_type_and_content("%NTS,CODE")

        self.assertIs(COMMENT_TYPE_TAG, t)
        self.assertEqual(["NTS", "CODE"], c)


class NewCommentsFormatTestCase(unittest.TestCase):
    def test_can_read_label(self):
        s = r"$0008		[chk_chr]"

        c = NewCommentParser()
        c.feed(s)

        self.assertEqual("chk_chr", c.get_label_at(0x0008))

    def test_can_read_a_single_line_comment(self):
        s = r"$0010		This is a comment."

        c = NewCommentParser()
        c.feed(s)

        self.assertEqual("This is a comment.", c.get_comment_at(0x0010))

    def test_can_read_a_single_tag(self):
        s = r"$0020		%NTS"

        c = NewCommentParser()
        c.feed(s)

        self.assertEqual(["NTS"], c.get_tags_at(0x0020))

    def test_can_read_a_description_text_after_a_label(self):
        s = [r"$0020		[function]",
             r"             This is a descriptive text for the function",
             r"             and it is a multiline text."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a descriptive text for the function\nand it is a multiline text.",
                         c.get_description_at(0x0020))

    def test_can_read_a_multiline_text(self):
        s = [r"$0030		This is a multiline text to describe a single address",
             r"             and it is a multiline text."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a multiline text to describe a single address\nand it is a multiline text.",
                         c.get_comment_at(0x0030))

    def test_can_read_a_multiline_text_after_a_tag(self):
        s = [r"$0040		%NTS",
             r"             This is a multiline text to describe a single address",
             r"             and it is a multiline text."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a multiline text to describe a single address\nand it is a multiline text.",
                         c.get_comment_at(0x0040))
        self.assertEqual(["NTS"], c.get_tags_at(0x0040))

    def test_can_read_a_tag_after_a_label(self):
        s = [r"$0040		[directive]",
             r"             %NTS",
             r"             This is a multiline text to describe a single address",
             r"             and it is a multiline text."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("directive", c.get_label_at(0x0040))
        self.assertEqual(["NTS"], c.get_tags_at(0x0040))
        self.assertEqual("This is a multiline text to describe a single address\nand it is a multiline text.",
                         c.get_description_at(0x0040))

    def test_can_read_a_multiline_text_after_an_address_range(self):
        s = [r"$0030-$0040  This is a multiline text to describe an address range",
             r"             and it is a multiline text."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a multiline text to describe an address range\nand it is a multiline text.",
                         c.get_comment_at(0x0030))
        self.assertTrue(c.is_multiline(0x0030))
        self.assertEqual(0x0040, c.end_address_for_comment_at(0x0030))

    def test_can_read_a_sequence_of_comments(self):
        s = [r"$0030        This is a first comment",
             r"             and it's multiline.",
             r"$0040        This is a single line comment."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a first comment\nand it's multiline.", c.get_comment_at(0x0030))
        self.assertEqual("This is a single line comment.", c.get_comment_at(0x0040))

    def test_prunes_orphan_lines(self):
        s = [r"$0030        This is a first comment",
             r"",
             r"$0040        The previous empty line must be ignored."]

        c = NewCommentParser()
        for line in s:
            c.feed(line)

        self.assertEqual("This is a first comment", c.get_comment_at(0x0030))
        self.assertEqual("The previous empty line must be ignored.", c.get_comment_at(0x0040))


if __name__ == '__main__':
    unittest.main()
