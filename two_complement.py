import unittest


def two_complement(number, width):
    all_1 = 2 ** width - 1
    number = number ^ all_1
    number += 1
    number &= all_1
    return number


def two_complement_to_signed(number, width):
    all_1 = 2 ** width - 1
    number &= all_1

    sign_bit = 1 << (width-1)

    if sign_bit & number == 0:
        return number

    return -two_complement(number, width)


class TwoComplementTestCase(unittest.TestCase):
    def test_0_complement_is_0(self):
        self.assertEqual(0, two_complement(0, 8))

    def test_1_complement_is_11111111(self):
        self.assertEqual(255, two_complement(1, 8))

    def test_10000001_complement_is_01111111(self):
        self.assertEqual(129, two_complement(127, 8))

    def test_0_is_signed_0(self):
        self.assertEqual(0, two_complement_to_signed(0, 8))

    def test_1_is_signed_1(self):
        self.assertEqual(1, two_complement_to_signed(1, 8))

    def test_255_is_signed_minus_1(self):
        self.assertEqual(-1, two_complement_to_signed(255, 8))

    def test_65535_is_signed_minus_1(self):
        self.assertEqual(-1, two_complement_to_signed(65535, 16))


if __name__ == '__main__':
    unittest.main()
