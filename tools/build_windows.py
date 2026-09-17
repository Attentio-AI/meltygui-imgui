"""Build Windows x86-64 wheels (one per supported CPython) from the release source archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import zipfile

from build import KIND, PYTHONS, ROOT

# Bundles the MSVC C++ runtime (msvcp140.dll), which CPython does not ship.
DELVEWHEEL = "delvewheel==1.13.1"
TARGET = "win_amd64"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist",
                        help="Directory holding the sdist from tools/build.py; the wheels land beside it")
    args = parser.parse_args()
    output = args.output.resolve()
    archives = list(output.glob("*.tar.gz"))
    if len(archives) != 1:
        parser.error("Expected exactly one sdist from tools/build.py in the output directory")
    if any(output.glob(f"*-{TARGET}.whl")):
        parser.error("Use an output directory without existing Windows wheels")
    # The release build is the one compilation that is not a missing-wheel fallback.
    environment = {**os.environ, f"MELTYGUI_{KIND.upper()}_RELEASE_BUILD": "1"}
    with tempfile.TemporaryDirectory(prefix="meltygui-native-") as work:
        # Every wheel is built from the source archive users fall back to.
        with tarfile.open(archives[0]) as archive:
            archive.extractall(work, filter="data")
        source = next(Path(work).iterdir())
        raw = Path(work) / "raw"
        for tag in PYTHONS:
            version = f"{tag[2]}.{tag[3:]}"
            subprocess.run(["uv", "build", "--wheel", "--python", version, str(source), "--out-dir", str(raw)],
                           check=True, env=environment)
        for wheel in sorted(raw.glob("*.whl")):
            subprocess.run(["uvx", "--from", DELVEWHEEL, "delvewheel", "repair", "--wheel-dir", str(output),
                            str(wheel)], check=True)
    wheels = sorted(output.glob(f"*-{TARGET}.whl"))
    # The auditwheel.txt counterpart: the DLLs each repaired wheel carries.
    report = []
    for wheel in wheels:
        with zipfile.ZipFile(wheel) as archive:
            bundled = sorted(Path(n).name for n in archive.namelist() if ".libs/" in n and n.lower().endswith(".dll"))
        report.append(f"{wheel.name}\n" + "".join(f"  bundles {name}\n" for name in bundled))
    (output / "delvewheel.txt").write_text("\n".join(report))
    receipt = {"kind": KIND, "sdist": archives[0].name, "repair": DELVEWHEEL, "python": PYTHONS, "target": TARGET,
               "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [archives[0], *wheels]}}
    (output / "build-windows.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
