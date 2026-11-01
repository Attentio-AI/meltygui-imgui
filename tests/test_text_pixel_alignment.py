"""Raster alignment must not quantize ImGui's layout or input state."""
import ctypes
import math
import struct
import unittest

import meltygui_imgui as imgui


def vertices(draw):
    data = ctypes.string_at(draw.vtx_buffer_data, draw.vtx_buffer_size * imgui.VERTEX_SIZE)
    return [struct.unpack_from('ff', data, i * imgui.VERTEX_SIZE + imgui.VERTEX_BUFFER_POS_OFFSET)
            for i in range(draw.vtx_buffer_size)]


class TextPixelAlignmentTests(unittest.TestCase):
    def setUp(self):
        self.context = imgui.create_context()
        self.io = imgui.get_io()
        self.io.ini_file_name = None
        self.io.display_size = (400, 400)
        self.io.delta_time = 1 / 60
        self.io.fonts.get_tex_data_as_rgba32()
        self.io.fonts.texture_id = 1

    def tearDown(self):
        imgui.destroy_context(self.context)

    def draw(self, position, text=True):
        imgui.new_frame()
        draw = imgui.get_foreground_draw_list()
        x, y = position
        if text:
            draw.add_text(x, y, 0xffffffff, 'Crisp text\nSecond line')
        else:
            draw.add_rect_filled(x, y, x + 40, y + 20, 0xffffffff)
        result = vertices(draw)
        imgui.render()
        return result

    def test_fractional_text_matches_pixel_aligned_text_at_each_density(self):
        for scale in ((1, 1), (1.25, 1.5), (2, 2), (3, 3)):
            self.io.display_fb_scale = scale
            for fraction in (.125, .25, .5, .875):
                with self.subTest(scale=scale, fraction=fraction):
                    pos = (50 + fraction, 61 + fraction)
                    aligned = tuple(math.floor(v * s) / s for v, s in zip(pos, scale))
                    actual = self.draw(pos)
                    self.assertTrue(actual)
                    self.assertEqual(actual, self.draw(aligned))

    def test_shapes_and_pointer_coordinates_remain_fractional(self):
        self.io.mouse_pos = (51.25, 62.125)
        before = self.draw((50, 60), text=False)
        after = self.draw((50.125, 60.125), text=False)
        for first, second in zip(before, after):
            self.assertEqual(tuple(b - a for a, b in zip(first, second)), (.125, .125))
        self.assertEqual(tuple(self.io.mouse_pos), (51.25, 62.125))

    def test_child_scroll_and_cursor_keep_subpixel_precision(self):
        def frame():
            imgui.new_frame()
            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(400, 400)
            with imgui.begin('Host', flags=imgui.WINDOW_NO_DECORATION):
                with imgui.begin_child('Child', 250, 250, flags=imgui.WINDOW_HORIZONTAL_SCROLLING_BAR):
                    result = (imgui.get_scroll_x(), imgui.get_scroll_y(), tuple(imgui.get_cursor_screen_pos()))
                    imgui.dummy(1000, 1000)
                    imgui.set_scroll_x(50.125)
                    imgui.set_scroll_y(60.375)
            imgui.render()
            return result
        for _ in range(4):
            x, y, cursor = frame()
        self.assertEqual((x, y), (50.125, 60.375))
        self.assertAlmostEqual(cursor[0] % 1, .875)
        self.assertAlmostEqual(cursor[1] % 1, .625)


if __name__ == '__main__':
    unittest.main()
