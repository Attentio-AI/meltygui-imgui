import inspect

import pytest

import meltygui_imgui


IMGUI_DATA_DESCRIPTORS = [
    attribute_name for attribute_name in dir(meltygui_imgui.GuiStyle)
    if inspect.isdatadescriptor(getattr(meltygui_imgui.GuiStyle, attribute_name))
]


@pytest.fixture
def context():
    return meltygui_imgui.create_context()


@pytest.fixture(params=IMGUI_DATA_DESCRIPTORS)
def data_descriptor(request):
    if request.param == "colors":
        pytest.skip("'{}' isn't a writable property".format(request.param))
    return request.param


def gui_style_property():
    pass


def test_gui_style_attribute_access_without_create(context, data_descriptor):
    style = meltygui_imgui.GuiStyle()

    with pytest.raises(RuntimeError):
        setattr(style, data_descriptor, getattr(style, data_descriptor))


def test_gui_style_data_descriptor_symmetry(context, data_descriptor):
    style = meltygui_imgui.GuiStyle.create()

    value = getattr(style, data_descriptor)
    setattr(style, data_descriptor, getattr(style, data_descriptor))
    assert getattr(style, data_descriptor) == value


def test_gui_style_equality(context):
    assert meltygui_imgui.get_style() == meltygui_imgui.get_style()
    assert meltygui_imgui.get_style() is not meltygui_imgui.get_style()


def test_gui_style_inequality(context):
    assert meltygui_imgui.GuiStyle.create() != meltygui_imgui.GuiStyle.create()
    assert meltygui_imgui.GuiStyle.create() is not meltygui_imgui.GuiStyle.create()
