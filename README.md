# z80decomp

`z80decomp` is a tool to help disassemble and annotate Z80 binary files.
The project is focused in understanding old computer ROMs and produce a human-readable
assembly source file that can be reassembled to the original binary.

See [History](#a-bit-of-history-on-the-project) below for more information.

## Dependencies

### For disassembly and annotation:
- 
- Python 3.10 or later

### For round-trip verification:

- [sjasmplus](https://github.com/z00m128/sjasmplus) (must be in PATH)
- Python package `watchdog` (for watch mode)

## Disassembler

`dissasm.py` produces sjasmplus-compatible assembly from a ROM file and a
comments/labels file:

```
python3 dissasm.py --romfile vg5k10.bin --comments vg5000-rom-comments-1.0.txt
```

Output is written to stdout. The generated assembly includes:

- `OPT --syntax=a` to disambiguate instructions like `sub a,d` from
  sjasmplus's multi-argument syntax
- `ORG $0000` to set the origin (can be modified to a different address if needed)
- `EQU` definitions for labels pointing outside the ROM
- Inline comments flagging any label names that conflict with sjasmplus
  reserved keywords (`low`, `high`, `or`, etc.), which are replaced by their
  numeric address in the output

## Round-trip verification

`verify_roundtrip.py` disassembles a ROM, reassembles it with sjasmplus, then
diffs the result against the original to confirm they are byte-for-byte identical.

**Batch mode** (one-shot):

```
python3 verify_roundtrip.py 1.0
python3 verify_roundtrip.py 1.1
```

**Watch mode** (re-runs automatically when the comments file changes):

```
python3 verify_roundtrip.py 1.0 --watch
python3 verify_roundtrip.py 1.1 --watch
```

### Required files

The verification script is hardcoded on the VG5000 ROM versions 1.0 and 1.1 at the moment.
It will work with the following files in the current directory:

| Version | ROM input | Comments file | ASM output | Binary output |
|---------|-----------|---------------|------------|---------------|
| 1.0 | `vg5k10.bin` | `vg5000-rom-comments-1.0.txt` | `rom-1.0.asm` | `rom-1.0.bin` |
| 1.1 | `vg5000_1.1.rom` | `vg5000-rom-comments-1.1.txt` | `rom-1.1.asm` | `rom-1.1.bin` |

## Running the tests

```
python3 -m unittest dissasm_tests z80opcode_tests comments_new_tests rom_tests
```

## A bit of history on the project

