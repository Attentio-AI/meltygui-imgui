"""Exercise an installed binding without a display server."""
import importlib.metadata
import importlib.util

import meltygui_imgui as imgui

assert importlib.metadata.version('meltygui-imgui') == '2.0.0.post3'
assert importlib.util.find_spec('imgui') is None
context = imgui.create_context()
try:
    io = imgui.get_io()
    io.display_size = (640, 480)
    io.delta_time = 1 / 60
    width, height, pixels = io.fonts.get_tex_data_as_rgba32()
    assert width > 0 and height > 0 and pixels
    imgui.new_frame()
    imgui.set_next_window_position(10, 10)
    imgui.set_next_window_size(300, 200)
    imgui.begin('Wheel smoke test')
    imgui.text('MeltyGUI ImGui')
    imgui.end()
    imgui.render()
    assert imgui.get_draw_data().total_vtx_count > 0
    assert imgui.get_version() == '1.82'
finally:
    imgui.destroy_context(context)
print('Installed ImGui wheel: context, font atlas and frame rendering passed')
