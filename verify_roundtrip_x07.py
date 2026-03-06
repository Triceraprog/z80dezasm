import os
import subprocess
import time

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG = {
    "input_file": "x07-comments.txt",
    "input_rom": "x07.bin",
    "output_rom": "x07-output.bin",
    "output_asm": "x07-output.asm",
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
    p = subprocess.run(["sjasmplus", "--nologo", f"--raw={output_rom}", from_asm],
                       stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)

    if p.returncode != 0:
        print(p.stdout.decode())
        print(p.stderr.decode())
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
    import argparse
    parser = argparse.ArgumentParser(description="Verify X07 ROM round-trip: disassemble, reassemble, diff.")
    parser.add_argument("--watch", action="store_true", help="Watch for changes and re-run automatically")
    args = parser.parse_args()

    run(CONFIG)

    if args.watch:
        event_handler = RoundtripEventHandler(CONFIG)
        observer = Observer()
        path_to_watch = os.path.dirname(CONFIG["input_file"]) or "."
        print(f"Watching {path_to_watch} for changes to {CONFIG['input_file']}...")
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
