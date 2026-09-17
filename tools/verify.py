"""Verify the release artifacts (a wheel per CPython and the sdist), package boundary, and included license notices."""
from email.parser import BytesParser
from pathlib import Path
import argparse
import os
import tarfile
import zipfile

KIND = "imgui"
VERSION = "2.0.0.post3"
PYTHONS = ["cp311", "cp312", "cp313"]
NAMESPACE = "meltygui_" + KIND
# platform -> (wheel platform tag prefix, extension module suffix)
PLATFORMS = {"linux": ("manylinux", ".so"), "windows": ("win_amd64", ".pyd")}


def verify_wheel(wheel, platform):
    tag, extension = PLATFORMS[platform]
    assert f"-{wheel.name.split('-')[2]}-{tag}" in wheel.name
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        metadata = BytesParser().parsebytes(archive.read(next(n for n in names if n.endswith(".dist-info/METADATA"))))
        assert metadata["Name"].replace("_", "-") == "meltygui-" + KIND
        assert metadata["Version"] == VERSION
        assert "3.11" in metadata["Requires-Python"] and "3.14" in metadata["Requires-Python"]
        assert metadata["Home-page"] == "https://github.com/Attentio-AI/meltygui-" + KIND
        assert any(n.startswith(NAMESPACE + "/") for n in names)
        assert not any(n.startswith(KIND + "/") for n in names), "Must not overwrite upstream package"
        assert any(n.endswith(extension) for n in names)
        if platform == "windows":
            # CPython ships vcruntime140 but not the C++ runtime the extension links.
            assert any(".libs/msvcp140" in n for n in names)
        assert any("/licenses/LICENSE" in n for n in names)
        assert not any(n.startswith(("meltygui/", "meltygui_pro/", "meltyprivate/")) for n in names)
        if KIND == "pycuda":
            assert any(d.startswith("numpy") for d in metadata.get_all("Requires-Dist", []))
            assert any("NVIDIA-CUDA-12.1-EULA" in n for n in names)
            assert any("libcurand" in n for n in names)
            assert not any(Path(n).name.startswith("libcuda.so") for n in names)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("dist"))
    parser.add_argument("--platform", choices=sorted(PLATFORMS), nargs="+", default=["linux"],
                        help="Platforms whose wheels the directory must hold")
    args = parser.parse_args()
    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/tags/"):
        assert ref == "refs/tags/v" + VERSION, "Tag must match the package version"
    wheels = list(args.directory.glob("*.whl"))
    archives = list(args.directory.glob("*.tar.gz"))
    assert len(archives) == 1, "Expected exactly one sdist"
    platform_of = {w: next((p for p, (tag, _) in PLATFORMS.items() if f"-{tag}" in w.name), "") for w in wheels}
    expected = sorted((platform, tag) for platform in args.platform for tag in PYTHONS)
    assert sorted((platform_of[w], w.name.split("-")[2]) for w in wheels) == expected, \
        "Expected one wheel per supported CPython and platform"
    for wheel in wheels:
        metadata = verify_wheel(wheel, platform_of[wheel])
    with tarfile.open(archives[0]) as archive:
        names = archive.getnames()
        assert any(n.endswith("/UPSTREAM.json") for n in names)
        assert any(n.endswith("/LICENSE") for n in names)
        assert any("/" + NAMESPACE + "/" in n for n in names)
    print(f"Verified {metadata['Name']} {VERSION} for {', '.join(args.platform)}: wheels, sdist, namespace and licenses")


if __name__ == "__main__":
    main()
