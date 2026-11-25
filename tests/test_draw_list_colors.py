"""A draw list colour is floats: packed by the binding inside [0, 1], by the host's packer outside it."""
import ctypes

import pytest

import meltygui_imgui as imgui

SDR = 0x80000000


@pytest.fixture
def draw_list():
    context = imgui.create_context()
    io = imgui.get_io()
    io.ini_file_name = None
    io.display_size = (800, 600)
    io.fonts.get_tex_data_as_rgba32()
    imgui.new_frame()
    imgui.begin('host')
    try:
        yield imgui.get_window_draw_list()
    finally:
        imgui.set_wide_color(None)
        imgui.end()
        imgui.render()
        imgui.destroy_context(context)


def colour(draw_list, value):
    """The packed colour the draw list wrote for `value`: that of a rectangle's last vertex."""
    draw_list.add_rect_filled(0, 0, 10, 10, value)
    vertex = ctypes.sizeof(ctypes.c_float) * 4 + 4                     # position, uv, colour
    end = draw_list.vtx_buffer_data + draw_list.vtx_buffer_size * vertex
    return ctypes.c_uint32.from_address(end - 4).value


def test_floats_inside_the_range_are_packed_under_the_sdr_bit(draw_list):
    assert colour(draw_list, (1.0, 0.5, 0.0)) == SDR | 0x7F000000 | 0x80 << 8 | 0xFF
    assert colour(draw_list, (0.2, 0.4, 0.6, 0.5)) == SDR | 64 << 24 | 153 << 16 | 102 << 8 | 51
    assert colour(draw_list, (0.0, 0.0, 0.0, 0.0)) == SDR
    assert colour(draw_list, (0.0, 0.0, 0.0, 7.0)) == SDR | 0x7F000000
    assert colour(draw_list, (0.0, 0.0, 0.0, float('nan'))) == SDR
    assert colour(draw_list, 0x7F336699) == 0x7F336699


def test_floats_and_a_packed_colour_are_both_taken(draw_list):
    for value in ((0.2, 0.4, 0.6), (0.2, 0.4, 0.6, 0.5), [1.0, 0.0, 0.0], SDR | 0x7F336699):
        draw_list.add_rect_filled(0, 0, 10, 10, value)
        draw_list.add_rect(0, 0, 10, 10, value)
        draw_list.add_line(0, 0, 10, 10, value)
        draw_list.add_text(0, 0, value, 'text')


def test_a_colour_outside_the_range_goes_to_the_registered_packer(draw_list):
    with pytest.raises(ValueError):
        draw_list.add_rect_filled(0, 0, 10, 10, (2.0, 0.5, 0.2))
    seen = []
    imgui.set_wide_color(lambda r, g, b, a: seen.append((r, g, b, a)) or 0x7F102030)
    draw_list.add_rect_filled(0, 0, 10, 10, (2.0, 0.5, 0.25))
    draw_list.add_rect_filled(0, 0, 10, 10, (0.5, -0.5, 0.25, 0.5))
    draw_list.add_rect_filled(0, 0, 10, 10, (0.5, 0.5, 0.25))          # inside the range: not asked
    assert seen == [(2.0, 0.5, 0.25, 1.0), (0.5, -0.5, 0.25, 0.5)]


def test_what_is_no_colour_is_refused(draw_list):
    for value in ('red', None, (0.5, 0.5)):
        with pytest.raises((TypeError, IndexError)):
            draw_list.add_rect_filled(0, 0, 10, 10, value)
