from z80tools import decode_full
from z80opcode_strings import decoded_to_string

with open("vg5000_1.1.rom", "rb") as romFile:
	romContent = romFile.read()

size = len(romContent)

data_ranges = {0x0003: 0x0008, 0x0026: 0x0028, 0x1148: 0x1945, 0x2000: 0x2214}

pc = 0
while (pc < size):

	if pc in data_ranges:
		pc = data_ranges[pc]

	decoded = decode_full(romContent[pc:])
	decoded_size = decoded[-1]

	byte_list = ["%02x" % x for x in romContent[pc:pc+decoded_size]]
	byte_string = " ".join(byte_list)

	string = decoded_to_string(decoded[:-1])

	label = ""

	line = "{label:<12} {mnemonic:<8} {args:<15} ; 0x{pc:0<4x} {bytes:<15} ;".format(
		label=label,
		pc=pc,
		bytes=byte_string,
		mnemonic=string[0].lower(),
		args=string[1].lower())
	print(line)
	# print("0x%04x %14s | %-6s %-30s ; %s" % (pc, byte_string, string[0].lower(), string[1].lower(), decoded))

	if "TODO" in decoded[0]:
		size = pc + 5

	if decoded_size == 0:
		exit(0)
	pc += decoded_size

