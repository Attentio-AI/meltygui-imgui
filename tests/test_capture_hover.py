"""A retained view that skipped a frame still has the pointer in its child window when it runs again."""
import meltygui_imgui as imgui


def run(capture):
    """One execution of a view at (30, 40) with a child window; whether the child's button is hovered."""
    capture.begin(300, 200, 30, 40)
    imgui.begin_child('list', 0, 100, False)
    imgui.invisible_button('row', 200, 18)
    hovered = imgui.is_item_hovered()
    imgui.end_child()
    capture.end()
    return hovered


def test_child_window_is_hovered_after_a_frame_the_view_did_not_run_in():
    context = imgui.create_context()
    io = imgui.get_io()
    io.ini_file_name = None
    io.display_size = (800, 600)
    io.fonts.get_tex_data_as_rgba32()
    capture = imgui.DrawCapture('hover')
    seen = []
    try:
        # The view runs in frames 0, 1 and 2, is cached in 3 and 4, and runs for a press in 5.
        for frame in range(6):
            io.mouse_pos = (50, 50) if frame else (500, 500)   # over the row, in the host's coordinates
            imgui.new_frame()
            imgui.set_next_window_position(0, 0)
            imgui.set_next_window_size(400, 300)
            imgui.begin('host', flags=imgui.WINDOW_NO_TITLE_BAR)
            if frame not in (3, 4):
                seen.append(run(capture))
            imgui.end()
            imgui.render()
        assert seen == [False, True, True, True]
    finally:
        capture.close()
        imgui.destroy_context(context)
