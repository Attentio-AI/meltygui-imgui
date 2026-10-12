"""Check the installed wheel's IDE contract against real keyword calls."""
import ast
from pathlib import Path
import subprocess
import sys

import meltygui_imgui as imgui
import pytest


def test_wheel_contains_signatures():
    package = Path(imgui.__file__).parent
    assert (package / "py.typed").is_file()
    for module in ("core", "internal"):
        tree = ast.parse((package / f"{module}.pyi").read_text())
        # Version-conditional declarations describe Cython 0.29's positional-only
        # optimizations separately from Cython 3's keyword-friendly defaults.
        def module_declarations(nodes):
            for node in nodes:
                if isinstance(node, ast.If):
                    yield from module_declarations(node.body + node.orelse)
                else:
                    yield node
        nodes = list(module_declarations(tree.body))
        declared = {node.name for node in nodes if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
        runtime = getattr(imgui, module)
        # Missing runtime objects indicate a stub for something C-only, renamed,
        # or removed. Ignore imports used solely to describe the stub.
        assert all(hasattr(runtime, name) for name in declared)
        public_callables = {name for name in dir(runtime)
                            if not name.startswith("_") and callable(getattr(runtime, name))
                            and getattr(getattr(runtime, name), "__module__", None) == runtime.__name__}
        aliases = {target.id for node in tree.body if isinstance(node, ast.Assign)
                   for target in node.targets if isinstance(target, ast.Name)}
        assert public_callables <= declared | aliases


def test_keyword_calls_and_context_manager():
    context = imgui.create_context()
    try:
        io = imgui.get_io()
        io.ini_file_name = None
        io.display_size = (640, 480)
        io.delta_time = 1 / 60
        io.fonts.get_tex_data_as_rgba32()
        imgui.new_frame()
        imgui.set_next_window_position(x=0, y=0)
        imgui.set_next_window_size(width=300, height=200)
        flags = (imgui.WINDOW_NO_DECORATION | imgui.WINDOW_NO_MOVE |
                 imgui.WINDOW_NO_BACKGROUND | imgui.WINDOW_NO_SAVED_SETTINGS)
        with imgui.begin(label="##root", flags=flags) as window:
            assert isinstance(window.expanded, bool)
            imgui.push_style_var(variable=imgui.STYLE_ALPHA, value=0.5)
            imgui.pop_style_var(count=1)
            imgui.text("Keyword argument test")
            if sys.version_info >= (3, 13):
                imgui.text(text="Cython 3 keywords")
            else:
                with pytest.raises(TypeError, match="keyword"):
                    imgui.text(text="Cython 0.29 positional-only")
        imgui.render()
    finally:
        imgui.destroy_context(context)


def test_type_checker_uses_real_keywords(tmp_path):
    code = '''import meltygui_imgui as imgui
from meltygui_imgui import core, internal

imgui.set_next_window_position(x=0, y=0)
with imgui.begin(label="##root", flags=imgui.WINDOW_NO_MOVE) as window:
    expanded, opened = window
    print(window.expanded, window.opened)
core.begin(label="Core", closable=True, flags=0)
imgui.push_style_var(variable=imgui.STYLE_ALPHA, value=0.5)
imgui.pop_style_var(count=1)
imgui.get_io().fonts.texture_id = object()
imgui.get_window_draw_list().add_line(start_x=0, start_y=0, end_x=1, end_y=1, col=0)
imgui.set_cursor_position((0, 0))
internal.push_item_flag(option=internal.ITEM_DISABLED, enabled=True)
with imgui.styled(variable=imgui.STYLE_ALPHA, value=0.5):
    pass
'''
    path = tmp_path / "keywords.py"
    path.write_text(code)
    command = [sys.executable, "-I", "-m", "mypy", "--follow-imports=silent", str(path)]
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    # Prove that success wasn't just due to treating the whole extension as Any.
    path.write_text(code + '\nimgui.begin(label="Bad", ImGuiWindowFlags_flags=0)\n')
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'Unexpected keyword argument "ImGuiWindowFlags_flags"' in result.stdout
    path.write_text(code + '\nimgui.text(text="Text")\nimgui.push_item_width(item_width=100)\n')
    result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True)
    if sys.version_info >= (3, 13):
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode == 1, result.stdout + result.stderr
        assert 'Unexpected keyword argument "text"' in result.stdout
        assert 'Unexpected keyword argument "item_width"' in result.stdout
