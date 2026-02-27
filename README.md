# z80tools

Disassembler and round-trip verification tools for the VG5000µ ROM.

## Dependencies

- Python 3
- [sjasmplus](https://github.com/z00m128/sjasmplus) (must be in PATH)
- Python package `watchdog` (for watch mode)

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

Each version expects the following files in the project directory:

| Version | ROM input | Comments file | ASM output | Binary output |
|---------|-----------|---------------|------------|---------------|
| 1.0 | `vg5k10.bin` | `vg5000-rom-comments-1.0.txt` | `rom-1.0.asm` | `rom-1.0.bin` |
| 1.1 | `vg5000_1.1.rom` | `vg5000-rom-comments-1.1.txt` | `rom-1.1.asm` | `rom-1.1.bin` |

## Disassembler

`dissasm.py` produces sjasmplus-compatible assembly from a ROM file and a
comments/labels file:

```
python3 dissasm.py --romfile vg5k10.bin --comments vg5000-rom-comments-1.0.txt
```

Output is written to stdout. The generated assembly includes:

- `OPT --syntax=a` to disambiguate instructions like `sub a,d` from
  sjasmplus's multi-argument syntax
- `ORG $0000` to set the origin
- `EQU` definitions for labels pointing outside the ROM
- Inline comments flagging any label names that conflict with sjasmplus
  reserved keywords (`low`, `high`, `or`, etc.), which are replaced by their
  numeric address in the output

## Running the tests

```
python3 -m unittest dissasm_tests z80opcode_tests comments_new_tests rom_tests
```
