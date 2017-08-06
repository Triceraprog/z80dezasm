import unittest


class Rom():
	def __init__(self, memory):
		self.memory = memory
		self.ranges = []

	def get_type(self, address):
		r = self.__find_range(address)

		if not r:
			return "unknown"

		return r[1]

	def mark_data(self, begin, end):
		self.__mark_range(begin, end, 'data')

	def mark_code(self, begin, end):
		self.__mark_range(begin, end, 'code')

	def __mark_range(self, begin, end, range_type):
		""" begin is inclusive, end is exclusive, to be coherent with range()"""
		existing_range = self.__find_overlapping_range(begin, end)

		new_range = ((begin, end), range_type)
		if not existing_range:
			self.ranges.append(new_range)
		else:
			self.ranges.remove(existing_range)
			((b_old, e_old), t_old) = existing_range
			((b_new, e_new), t_new) = new_range

			if b_old < b_new:
				# Existing rang is flowing on the left
				new_old_left = (b_old, b_new), t_old
				self.ranges.append(new_old_left)

			if e_old > e_new:
				# Existing rang is flowing on the right
				new_old_right = (e_new, e_old), t_old
				self.ranges.append(new_old_right)

			self.ranges.append(new_range)

	def __find_overlapping_range(self, begin, end):
		for r in sorted(self.ranges):
			limits = r[0]
			if ((begin < limits[0] and end > limits[0])
				or
				(begin >= limits[0] and begin < limits[1])):
				return r

		return None

	def __find_range(self, address):
		found_range = [r for r in self.ranges if address in range(*(r[0]))]
		return found_range[0] if found_range else None

# Memory content reads as
# JP 0x0009
# DEFM "PRINT", 0
# JP 0x0000

memory = [0xC3, 0x09, 0x00, 0x50, 0x52, 0x49, 0x4E, 0x54, 0x00, 0xC3, 0x00, 0x00]

class RomTestCase(unittest.TestCase):
	def test_rom_is_initialized_with_memory_content(self):
		rom = Rom(memory)
		self.assertEqual("unknown", rom.get_type(0x0004))

	def test_rom_can_be_marked_with_data_range(self):
		rom = Rom(memory)
		rom.mark_data(0x0003, 0x0009)
		self.assertEqual("data", rom.get_type(0x0004))
		self.assertEqual("unknown", rom.get_type(0x0000))

	def test_rom_can_be_marked_with_code_range(self):
		rom = Rom(memory)
		rom.mark_code(0x0001, len(memory) + 1)
		self.assertEqual("code", rom.get_type(0x0004))
		self.assertEqual("unknown", rom.get_type(0x0000))

	def test_rom_can_be_marked_with_code_then_a_sub_data_range(self):
		rom = Rom(memory)
		rom.mark_code(0x0000, len(memory) + 1)
		rom.mark_data(0x0003, 0x0009)
		self.assertEqual("code", rom.get_type(0x0000))
		self.assertEqual("data", rom.get_type(0x0004))

		rom = Rom(memory)
		rom.mark_code(0x0000, len(memory) + 1)
		rom.mark_data(0x0000, 0x0009)
		self.assertEqual("code", rom.get_type(0x000A))
		self.assertEqual("data", rom.get_type(0x0000))

		rom = Rom(memory)
		rom.mark_code(0x0000, len(memory) + 1)
		rom.mark_data(0x0004, len(memory) + 1)
		self.assertEqual("code", rom.get_type(3))
		self.assertEqual("data", rom.get_type(len(memory)))

	def test_rom_can_be_iterated_by_ranges(self):
		pass
		

if __name__ == '__main__':
    unittest.main()
