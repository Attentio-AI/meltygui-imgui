"""A retained view that runs twice in one frame keeps the draws of its child windows."""
import meltygui_imgui as imgui


def run(capture, width):
    """One execution of a view with a child window; the child's vertex count as captured."""
    capture.begin(width, 200, 30, 40)
    imgui.begin_child('list', 0, 100, False)
    imgui.text('a row in the child')
    size = tuple(imgui.get_window_size())
    imgui.end_child()
    capture.end()
    lists = capture.draw_lists
    return size, [draw.vtx_buffer_size for draw in lists[1:]]


def test_child_window_survives_a_second_run_in_the_frame():
    context = imgui.create_context()
    io = imgui.get_io()
    io.ini_file_name = None
    io.display_size = (800, 600)
    io.fonts.get_tex_data_as_rgba32()
    capture = imgui.DrawCapture('rerun')
    try:
        for _ in range(2):      # the second frame: the child is no longer appearing
            imgui.new_frame()
            imgui.begin('host')
            first = run(capture, 300)
            again = run(capture, 220)       # resized by its parent, as in a tile being dragged
            imgui.end()
            imgui.render()
            assert first[1] and first[1][0] > 0
            assert again[1] == first[1]     # the child's draws are captured again
            assert again[0][0] == 220 and first[0][0] == 300    # at the size of this run
    finally:
        capture.close()
        imgui.destroy_context(context)
