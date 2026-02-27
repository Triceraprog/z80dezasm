import argparse
import os
import subprocess
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

VERSIONS = {
    "1.0": {
        "input_file": "../../vg5000_rom_comments/vg5000-rom-comments-1.0.txt",
        "input_rom": "vg5k10.bin",
        "output_rom": "rom-1.0.bin",
        "output_asm": "rom-1.0.asm",
    },
    "1.1": {
        "input_file": "../../vg5000_rom_comments/vg5000-rom-comments-1.1.txt",
        "input_rom": "vg5000_1.1.rom",
        "output_rom": "rom-1.1.bin",
        "output_asm": "rom-1.1.asm",
    },
}


def disassemble(input_file, from_rom, to_asm):
    p = subprocess.run(["python3", "dissasm.py", "--romfile", from_rom, "--comments", input_file],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise RuntimeError
    else:
        print("Writing assembly to " + to_asm)
        with open(to_asm, "wt") as f:
            f.write(bytes.decode(p.stdout, encoding="UTF-8"))


def assemble(from_asm, output_rom):
    print("Assemble " + from_asm)
    p = subprocess.run(["/home/mokona/Developpement/z80/z88dk/bin/z80asm", "-b", from_asm],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr)
        raise RuntimeError
    else:
        print("Done assembly")

        source_stat = os.stat(from_asm)
        dest_stat = os.stat(output_rom)

        if source_stat.st_ctime > dest_stat.st_ctime:
            print("Binary file older than source... error in assembling")
            raise RuntimeError


def diff(reference_rom, rebuilt_rom):
    with open(reference_rom, "rb") as f:
        reference_bytes = f.read()

    with open(rebuilt_rom, "rb") as f:
        rebuilt_bytes = f.read()

    if len(reference_bytes) != len(rebuilt_bytes):
        print("Files differ in size")

    for address, (a, b) in enumerate(zip(reference_bytes, rebuilt_bytes)):
        if a != b:
            print(f"Difference at address ${address:>04x}")
            raise RuntimeError

    print("Files are identical.")


def run(config):
    disassemble(config["input_file"], config["input_rom"], config["output_asm"])
    assemble(config["output_asm"], config["output_rom"])
    diff(config["input_rom"], config["output_rom"])


class RoundtripEventHandler(FileSystemEventHandler):
    def __init__(self, config):
        self.config = config

    def on_modified(self, event):
        if event.src_path.endswith(os.path.basename(self.config["input_file"])):
            run(self.config)


def main():
    parser = argparse.ArgumentParser(description="Verify ROM round-trip: disassemble, reassemble, diff.")
    parser.add_argument("version", choices=list(VERSIONS.keys()), help="ROM version to verify")
    parser.add_argument("--watch", action="store_true", help="Watch for changes and re-run automatically")
    args = parser.parse_args()

    config = VERSIONS[args.version]

    run(config)

    if args.watch:
        event_handler = RoundtripEventHandler(config)
        observer = Observer()
        path_to_watch = os.path.dirname(config["input_file"])
        print(f"Watching {path_to_watch} for changes...")
        observer.schedule(event_handler, path_to_watch, recursive=False)
        observer.start()
        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


if __name__ == '__main__':
    main()
