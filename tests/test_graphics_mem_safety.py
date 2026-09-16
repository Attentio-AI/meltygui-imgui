"""Note: This tests are potential crashers (may result in segfaults)"""
import pytest
import meltygui_imgui

@pytest.fixture
def context():
    return meltygui_imgui.create_context()

@pytest.fixture
def io():
    # setup io
    io = meltygui_imgui.get_io()
    io.delta_time = 1.0 / 60.0
    io.display_size = 300, 300

    # setup default font
    io.fonts.get_tex_data_as_rgba32()
    io.fonts.add_font_default()
    io.fonts.texture_id = 42  # set any texture ID to avoid segfaults

    return io

def test_texture_id_int_reference(context, io):

    # See issue #248 (https://github.com/pyimgui/pyimgui/issues/248)

    texture_id = 0
    for i in range(0, 1000, 50):
        meltygui_imgui.new_frame()

        meltygui_imgui.begin("tests")
        io.fonts.texture_id = texture_id
        meltygui_imgui.image(texture_id, 640, 480)
        meltygui_imgui.image_button(texture_id, 200, 50)
        draw_list = meltygui_imgui.get_background_draw_list()
        draw_list.add_image(texture_id, (20, 35), (180, 80))
        meltygui_imgui.end()

        texture_id += 1

        meltygui_imgui.render()
        
        draw_data = meltygui_imgui.get_draw_data()
        for commands in draw_data.commands_lists:
            for command in commands.commands:
                assert type(command.texture_id) is int

def test_texture_id_keep_type(context, io):

    texture_id = { 'dummy':42 }

    meltygui_imgui.new_frame()
    meltygui_imgui.image(texture_id, 640, 480)
    meltygui_imgui.render()
    draw_data = meltygui_imgui.get_draw_data()
    for commands in draw_data.commands_lists:
        for command in commands.commands:

            # Skip font atlas texture id
            if command.texture_id == io.fonts.texture_id:
                continue

            assert type(command.texture_id) == type(texture_id)    
