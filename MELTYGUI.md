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

The first release is **2.0.0.post1**, supporting Linux x86-64, CPython 3.12 and
glibc 2.28 or newer. It installs `meltygui_imgui` without overwriting the upstream
`imgui` package. Other platforms and Python versions are not supported yet.

The bundled Dear ImGui and font-helper license notices are included in the artifacts.

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

## Publish

Pushes to `main` and pull requests build and test without uploading. A `v*` tag
or a manual run with `publish=true` publishes the verified wheel and source
archive through PyPI trusted publishing. Published versions cannot be replaced.

Configure a pending GitHub publisher at https://pypi.org/manage/account/publishing/:

| Field | Value |
| --- | --- |
| PyPI project | `meltygui-imgui` |
| Owner | `Attentio-AI` |
| Repository | `meltygui-imgui` |
| Workflow | `release.yml` |
| Environment | `pypi` |

Then, after the main-branch build passes, create and push `v2.0.0.post1`.
No API token belongs in this repository.

## Licenses and changes

See [LICENSE](LICENSE), [LICENSES](LICENSES), and [MELTYGUI.md](MELTYGUI.md).
The primary changes are the Python namespace, pinned build dependencies,
Python 3.12 support, and rebuilt Cython extensions.
