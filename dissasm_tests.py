from dissasm import get_data_skip_regions

import unittest


class DataSkipRegionsTestCase(unittest.TestCase):
    def test_dataskip_without_size_defaults_to_one(self):
        directives = [(0x1234, ["DATASKIP"])]
        result = get_data_skip_regions(directives)
        self.assertEqual([(0x1234, 1)], result)

    def test_dataskip_with_explicit_size(self):
        directives = [(0x1234, ["DATASKIP(10)"])]
        result = get_data_skip_regions(directives)
        self.assertEqual([(0x1234, 10)], result)


if __name__ == '__main__':
    unittest.main()
