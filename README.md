# z80dezasm

`z80dezasm` is a tool to help disassemble and annotate Z80 binary files.
The project is focused in understanding old computer ROMs and produce a human-readable
assembly source file that can be reassembled to the original binary.

See [History](#a-bit-of-history-on-the-project) below for more information.

## Dependencies

### For disassembly and annotation:

- [Python 3.10](https://www.python.org/) or later
- [uv](https://docs.astral.sh/uv/)

### For round-trip verification:

- [sjasmplus](https://github.com/z00m128/sjasmplus) (must be in PATH)
- Python package `watchdog` (for watch mode)

## Disassembler

The archive is provided with a test binary, you can make a run of the tool by using:

```
uv run z80dezasm --romfile example.rom --comments example.txt --crossref
```

The result will be emitted on the standard output.

### Command parameters

```
usage: z80dezasm [-h] --romfile ROMFILE [--crossref] --comments COMMENTS [--org ORG]
                 [--entry-point ENTRY_POINT]
```

- `romfile` is mandatory and is the input binary file you want to disassemble
- `comments` is mandatory and is the file with directive and comments that will help generate the result
- `org` is the origin of the binary stream, it defaults to 0x0000. It accepts anything that can be converted to an int.
- `entry-point` is where the binary start code is, it defaults to 0x0000. It accepts anything that can be converted to an int.

About `entry-point`: its usage is mainly interesting when the origin is not zero, for a ROM that is located elsewhere
and jumped to by some mechanism. For exemple, for the `Canon X-07`, the reset mechanism provokes a `jp $c3c3`, which is
the actual entry point for the ROM.

### Emitted assembly

The disassembler will follow all code path to emit code. The default code paths are the entry point
(`$0000` by default) and all restart adresses if the origin is 0. Additional code paths can be
added through the comment file.

The disassembler will also try to detect character strings. You can deactivate the detection for
an adresse or a range in the comment file.

In addition, the generated assembly includes:

- `OPT --syntax=a` to disambiguate instructions like `sub a,d` from sjasmplus's multi-argument syntax
- `ORG $0000` to set the origin (can be modified to a different address if needed)
- `EQU` definitions for labels pointing outside the ROM
- Inline comments flagging any label names that conflict with sjasmplus reserved keywords
  (`low`, `high`, `or`, etc.), which are replaced by their numeric address in the output


### Cross-reference

The `--crossref` parameter will add comments in lines that are called of jump to by
other adresses.

With the sample data, for example, with `--crossref`, you will have:

```asm
start:       ei                            ; $0083 fb              ; / called from: $0001
jump0084:    jp       jump0084             ; $0084 c3 84 00        ; / called from: $0084
```

Without it, you will have:

```asm
start:       ei                            ; $0083 fb              ; 
jump0084:    jp       jump0084             ; $0084 c3 84 00        ; 
```

It can be useful during analysis, but can be cumbersome when publishing. 

## Round-trip verification

`verify_roundtrip.py` disassembles a ROM, reassembles it with `sjasmplus`, then
diffs the result against the original to confirm they are byte-for-byte identical.

It is a way to verify that the result of the disassembly is still producing the
input, and thus, nothing broke by the disassembly and commenting system.

It has parameters similar to the disassembler:

```
usage: verify_roundtrip.py [-h] --romfile ROMFILE --comments COMMENTS --output OUTPUT [--org ORG]
                           [--entry-point ENTRY_POINT] [--watch]
verify_roundtrip.py: error: the following arguments are required: --romfile, --comments, --output
```

- `output` specified a base name that will be used to create the `output.asm` and `output.bin` files
  containing respectively the disassembled file and the reconstructed binary.

**Batch mode** (one-shot):

```bash
> python3 verify_roundtrip.py --romfile example.rom --comments example.txt --output result
Writing assembly to result.asm
Assemble result.asm
Done assembly
Files are identical.
```

**Watch mode** (re-runs automatically when the comments file changes):

```
python3 verify_roundtrip.py 1.0 --watch
python3 verify_roundtrip.py 1.1 --watch
```

The watch mode is useful when analyzing to have a kind of interactive workflow where your
comments are regenerating the output file as they change.

It needs the optional `watchdog` dependency for `python`.

## Running the tests

```
uv run pytest
```

## A bit of history on the project

This project was originally started in 2017 as a set of scripts to disassemble the ROM of the
Philips VG5000µ, a Z80-based home computer from the 1980s.

The idea was to produce a commented assembly source file that could be reassembled to the original binary.
That way, the ROM could be understood and documented. It could also be modified. Mainly, everything
was for fun.

The disassembly was based on this [article](http://z80.info/decoding.htm) on decoding Z80 opcodes.

Ealy on, I wanted to have the comments on a dedicated file that would serve as a source
to be injected in the generated assembly. That way, the comments could be edited and improved without
having to edit, re-read the generated assembly file.

My process was to have a two pane editor with one for editing the comments and the other for reading
the output. A background process would watch for changes in the comments file and re-run the disassembly
and verify that the generated assembly could be reassembled to the original binary.

That's a bit more heavy that annotating the assembly file directly, but would help if I need to
change the comment formatting (which I did a few times).

One early feature was also to follow the code path through the `call`s and `jp`s instructions, to
quickly identify the code blocks from the data. I also added some commands to give indications
to the disassembler. For example marking a block as code. Or specifying that some apparent opcode
was actually data.

I later used the tool to check some information on some other computers, without a full
comment (PHC-25 and X07 for example).
