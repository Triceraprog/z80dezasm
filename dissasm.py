from z80tools import decode_full

with open("vg5000_1.1.rom", "rb") as romFile:
	romContent = romFile.read()

size = len(romContent)

pc = 0
while (pc < size):
	decoded = decode_full(romContent[pc:])
	decoded_size = decoded[-1]

	byte_list = ["%02x" % x for x in romContent[pc:pc+decoded_size]]
	byte_string = " ".join(byte_list)
	print("0x%04x %14s %s" % (pc, byte_string, decoded))

	if "TODO" in decoded[0]:
		exit(0)

	if decoded_size == 0:
		exit(0)
	pc += decoded_size

