# meltygui-imgui

Namespaced imgui bindings maintained for MeltyGUI, based on the upstream source
recorded in [UPSTREAM.json](UPSTREAM.json). Original authorship and licenses are
preserved. This repository contains the binding source and its release tooling.

```sh
uv pip install meltygui-imgui
```

```python
import meltygui_imgui
```

The current release is **2.0.0.post3**, with wheels for Linux x86-64 (glibc 2.28
or newer) and Windows x86-64 on CPython 3.11, 3.12 and 3.13. It installs `meltygui_imgui` without
overwriting the upstream `imgui` package. The 3.13 wheel is generated with
Cython 3.2; 3.11 and 3.12 keep the Cython 0.29 bindings.

### When no wheel matches

On any other platform or Python, pip and uv fall back to the source archive
without saying that no wheel matched. The build prints a banner naming your
platform and the prebuilt targets (installers show it with `-v`, or when the
build fails). A source build needs a C++ compiler and takes a few minutes. uv
ignores the upper Python bound, so on a newer Python it also builds from
source; pip refuses instead. Pass `--only-binary meltygui-imgui` to make a
missing wheel an error rather than a compilation.

The bundled Dear ImGui and font-helper license notices are included in the artifacts.

## IntelliJ IDEA / PyCharm

The package ships `.pyi` signatures for its native extensions, including the
top-level re-exports. These give the IDE the real Python keyword names, such as
`begin(label, closable=False, flags=0)`, instead of names reconstructed from
Cython's C-style docstrings (`str_label`, `ImGuiWindowFlags_flags`). Runtime
functions and calling conventions are unchanged. Types that are not fully
modeled remain `Any` to avoid rejecting supported conversions and callbacks.
The stubs also retain the positional-only restrictions of Cython 0.29 builds on
Python 3.11/3.12; Python 3.13 builds use Cython 3's keyword support.

Install the updated package into the IDE's selected Python interpreter. If an
existing project still shows the old generated skeleton, reload the interpreter
paths or invalidate the IDE caches and restart.

After editing the Cython API, regenerate the checked-in stubs:

```sh
uv run --no-project --with Cython==0.29.37 python tools/generate_stubs.py
```

CI checks for stale stubs and verifies that wheels and the source archive contain
both `.pyi` files and the `py.typed` marker.

## Build

Docker is required. The manylinux image and Python build dependencies are pinned.
The wheel is built from the generated source archive, which is also published
for local compilation when a matching wheel is unavailable.

```sh
python3 tools/build.py
python3 tools/verify.py dist
uvx --from twine==7.0.0 twine check --strict dist/*.whl dist/*.tar.gz
```

Use `--sudo-docker` if Docker requires sudo. Source builds require a C++ compiler.

The Windows wheels are built on Windows from that same source archive. With the
MSVC build tools and uv installed, and the archive from `tools/build.py` in `dist`:

```sh
python tools/build_windows.py
python tools/verify.py dist --platform windows
```

delvewheel bundles the MSVC C++ runtime, so the wheels need no redistributable.

## Publish

Pushes to `main` and pull requests build and test without uploading. A `v*` tag
or a manual run with `publish=true` publishes the verified Linux and Windows wheels and the source
archive through PyPI trusted publishing. Published versions cannot be replaced.

Configure a pending GitHub publisher at https://pypi.org/manage/account/publishing/:

| Field | Value |
| --- | --- |
| PyPI project | `meltygui-imgui` |
| Owner | `Attentio-AI` |
| Repository | `meltygui-imgui` |
| Workflow | `release.yml` |
| Environment | `pypi` |

Then, after the main-branch build passes, create and push `v2.0.0.post3`.
No API token belongs in this repository.

## Licenses and changes

See [LICENSE](LICENSE), [LICENSES](LICENSES), and [MELTYGUI.md](MELTYGUI.md).
The primary changes are the Python namespace, pinned build dependencies,
Python 3.12 support, and rebuilt Cython extensions.
