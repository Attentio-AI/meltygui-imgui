import logging
import sys

import pytest
import meltygui_imgui
from meltygui_imgui import ImGuiError


class _TestException(Exception):
    pass


@pytest.fixture
def context():
    ctx = meltygui_imgui.get_current_context()
    if ctx is not None:
        meltygui_imgui.destroy_context(ctx)
    ctx = meltygui_imgui.create_context()
    io = meltygui_imgui.get_io()
    io.delta_time = 1.0 / 60.0
    io.display_size = 300, 300

    # setup default font
    io.fonts.get_tex_data_as_rgba32()
    io.fonts.add_font_default()
    io.fonts.texture_id = 0  # set any texture ID to avoid segfaults
    return ctx


@pytest.fixture
def frame(context):
    meltygui_imgui.new_frame()
    yield
    try:
        meltygui_imgui.render()
    except ImGuiError:
        try:
            meltygui_imgui.end_frame()
        except ImGuiError:
            pass


# ------- BEGIN/END ----------
def test_begin_okay(frame):
    meltygui_imgui.begin("Example: empty window")
    meltygui_imgui.end()


def test_begin_with(frame):
    with meltygui_imgui.begin("Example: empty window") as window:
        assert isinstance(window.expanded, bool)
        assert isinstance(window.opened, bool)


def test_begin_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: empty window"):
            raise _TestException


def test_begin_unpacking(frame):
    expanded, opened = meltygui_imgui.begin("Example: empty window")
    assert isinstance(expanded, bool)
    assert isinstance(opened, bool)
    meltygui_imgui.end()


def test_begin_equality(frame):
    window = meltygui_imgui.begin("Example: empty window")
    assert window == window
    assert window == tuple(window)
    meltygui_imgui.end()

# ------- BEGIN_CHILD/END_CHILD ----------
def test_child_okay(frame):
    meltygui_imgui.begin("Example: child region")

    meltygui_imgui.begin_child("region", 150, -50, border=True)
    meltygui_imgui.text("inside region")
    meltygui_imgui.end_child()

    meltygui_imgui.text("outside region")
    meltygui_imgui.end()


def test_child_with(frame):
    with meltygui_imgui.begin("Example: child region"):
        with meltygui_imgui.begin_child("region", 150, -50, border=True):
            meltygui_imgui.text("inside region")
        meltygui_imgui.text("outside region")


def test_child_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: child region"):
            with meltygui_imgui.begin_child("region", 150, -50, border=True):
                raise _TestException
            meltygui_imgui.text("outside region")


def test_child_as_bool(frame):
    meltygui_imgui.begin("Example: child region")
    child = meltygui_imgui.begin_child("region", 150, -50, border=True)
    assert bool(child) is child.visible
    assert child == child
    assert child == bool(child)
    meltygui_imgui.end_child()
    meltygui_imgui.end()


# ------- BEGIN_TOOLTIP/END_TOOLTIP ----------
def test_tooltip_okay(frame):
    meltygui_imgui.begin("Example: tooltip")
    meltygui_imgui.button("Click me!")
    if meltygui_imgui.is_item_hovered():
        meltygui_imgui.begin_tooltip()
        meltygui_imgui.text("This button is clickable.")
        meltygui_imgui.end_tooltip()
    meltygui_imgui.end()


def test_tooltip_with(frame):
    with meltygui_imgui.begin("Example: tooltip"):
        meltygui_imgui.button("Click me!")
        if meltygui_imgui.is_item_hovered():
            with meltygui_imgui.begin_tooltip():
                meltygui_imgui.text("This button is clickable.")


def test_tooltip_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: tooltip"):
            meltygui_imgui.button("Click me!")
            with meltygui_imgui.begin_tooltip():
                raise _TestException


# ------- BEGIN_MAIN_MENU_BAR/END_MAIN_MENU_BAR ----------
def test_main_menu_bar_okay(frame):
    if meltygui_imgui.begin_main_menu_bar():
        meltygui_imgui.end_main_menu_bar()
    else:
        assert False


def test_main_menu_bar_with(frame):
    with meltygui_imgui.begin_main_menu_bar() as menu:
        assert menu.opened is True


def test_main_menu_bar_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin_main_menu_bar():
            raise _TestException


def test_main_menu_bar_as_bool(frame):
    menu = meltygui_imgui.begin_main_menu_bar()
    assert isinstance(menu.opened, bool)
    assert bool(menu) is menu.opened is True
    assert menu == menu
    assert menu == bool(menu)
    meltygui_imgui.end_main_menu_bar()


# ------- BEGIN_MENU_BAR/END_MENU_BAR ----------
def test_menu_bar_okay(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    meltygui_imgui.begin("Child Window - File Browser", flags=flags)

    if meltygui_imgui.begin_menu_bar():
        meltygui_imgui.end_menu_bar()
    else:
        assert False
    meltygui_imgui.end()


def test_menu_bar_with(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    with meltygui_imgui.begin("Child Window - File Browser", flags=flags):
        with meltygui_imgui.begin_menu_bar():
            pass


def test_menu_bar_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        flags = meltygui_imgui.WINDOW_MENU_BAR
        with meltygui_imgui.begin("Child Window - File Browser", flags=flags):
            with meltygui_imgui.begin_menu_bar():
                raise _TestException


def test_menu_bar_as_bool(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    meltygui_imgui.begin("Child Window - File Browser", flags=flags)
    menu = meltygui_imgui.begin_menu_bar()
    assert isinstance(menu.opened, bool)
    assert bool(menu) is menu.opened is True
    assert menu == menu
    assert menu == bool(menu)
    meltygui_imgui.end_menu_bar()
    meltygui_imgui.end()


# ------- BEGIN_TAB_BAR/END_TAB_BAR ----------
def test_tab_bar_okay(frame):
    meltygui_imgui.begin("Example Tab Bar")
    if meltygui_imgui.begin_tab_bar("MyTabBar"):
        meltygui_imgui.end_tab_bar()
    meltygui_imgui.end()


def test_tab_bar_with(frame):
    with meltygui_imgui.begin("Example Tab Bar"):
        with meltygui_imgui.begin_tab_bar("MyTabBar"):
            pass


def test_tab_bar_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example Tab Bar"):
            with meltygui_imgui.begin_tab_bar("MyTabBar"):
                raise _TestException


def test_tab_bar_as_bool(frame):
    meltygui_imgui.begin("Example Tab Bar")
    tab_bar = meltygui_imgui.begin_tab_bar("MyTabBar")
    assert bool(tab_bar) is tab_bar.opened is True
    assert tab_bar == tab_bar
    assert tab_bar == bool(tab_bar)
    meltygui_imgui.end_tab_bar()
    meltygui_imgui.end()


# ------- BEGIN_TAB_ITEM/END_TAB_ITEM ----------
def test_tab_item_okay(frame):
    meltygui_imgui.begin("Example Tab Bar")
    if meltygui_imgui.begin_tab_bar("MyTabBar"):
        if meltygui_imgui.begin_tab_item("Item 1")[0]:
            meltygui_imgui.text("Here is the tab content!")
            meltygui_imgui.end_tab_item()
        meltygui_imgui.end_tab_bar()
    meltygui_imgui.end()


def test_tab_item_with(frame):
    with meltygui_imgui.begin("Example Tab Bar"):
        with meltygui_imgui.begin_tab_bar("MyTabBar") as tab_bar:
            if tab_bar.opened:
                with meltygui_imgui.begin_tab_item("Item 1") as item:
                    if item.selected:
                        pass


def test_tab_item_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example Tab Bar"):
            with meltygui_imgui.begin_tab_bar("MyTabBar") as tab_bar:
                if tab_bar.opened:
                    with meltygui_imgui.begin_tab_item("Item 1") as item:
                        raise _TestException


def test_tab_item_as_bool(frame):
    meltygui_imgui.begin("Example Tab Bar")
    tab_bar = meltygui_imgui.begin_tab_bar("MyTabBar")
    assert tab_bar.opened
    item = meltygui_imgui.begin_tab_item("Item 1")
    assert bool(item) is item.selected is True
    assert item.opened is False
    assert item == item
    assert item == tuple(item)
    meltygui_imgui.end_tab_item()
    meltygui_imgui.end_tab_bar()
    meltygui_imgui.end()


# ------- BEGIN_MENU/END_MENU ----------
def test_menu_okay(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    meltygui_imgui.begin("Child Window - File Browser", flags=flags)

    if meltygui_imgui.begin_menu_bar():
        if meltygui_imgui.begin_menu('File'):
            meltygui_imgui.menu_item('Close')
            meltygui_imgui.end_menu()
        meltygui_imgui.end_menu_bar()
    meltygui_imgui.end()


def test_menu_with(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    with meltygui_imgui.begin("Child Window - File Browser", flags=flags):
        with meltygui_imgui.begin_menu_bar() as menu_bar:
            if menu_bar.opened:
                with meltygui_imgui.begin_menu('File'):
                    pass


def test_menu_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        flags = meltygui_imgui.WINDOW_MENU_BAR
        with meltygui_imgui.begin("Child Window - File Browser", flags=flags):
            with meltygui_imgui.begin_menu_bar() as menu_bar:
                if menu_bar.opened:
                    with meltygui_imgui.begin_menu('File'):
                        raise _TestException


def test_menu_as_bool(frame):
    flags = meltygui_imgui.WINDOW_MENU_BAR
    meltygui_imgui.begin("Child Window - File Browser", flags=flags)
    menu_bar = meltygui_imgui.begin_menu_bar()
    assert menu_bar.opened
    menu = meltygui_imgui.begin_menu('File')
    assert isinstance(menu.opened, bool)
    assert bool(menu) is menu.opened is False
    assert menu == menu
    assert menu == bool(menu)
    meltygui_imgui.end_menu_bar()
    meltygui_imgui.end()


# ------- BEGIN_POPUP{,_CONTEXT_ITEM,_CONTEXT_WINDOW,_CONTEXT_VOID}/END_POPUP ----------
def test_popup_okay(frame):
    meltygui_imgui.begin("Example: simple popup")
    meltygui_imgui.open_popup("select-popup")
    if meltygui_imgui.begin_popup("select-popup"):
        meltygui_imgui.end_popup()
    meltygui_imgui.end()


def test_popup_with(frame):
    with meltygui_imgui.begin("Example: simple popup"):
        meltygui_imgui.open_popup("select-popup")
        with meltygui_imgui.begin_popup("select-popup"):
            pass


def test_popup_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: simple popup"):
            meltygui_imgui.open_popup("select-popup")
            with meltygui_imgui.begin_popup("select-popup"):
                raise _TestException


def test_popup_as_bool(frame):
    meltygui_imgui.begin("Example: simple popup")
    meltygui_imgui.open_popup("select-popup")
    popup = meltygui_imgui.begin_popup("select-popup")
    assert isinstance(popup.opened, bool)
    assert bool(popup) is popup.opened is True
    assert popup == popup
    assert popup == bool(popup)
    meltygui_imgui.end_popup()
    meltygui_imgui.end()


def test_popup_context_item_isinstance(frame):
    meltygui_imgui.begin("Example: popup context view")
    meltygui_imgui.text("Right-click to set value.")
    item = meltygui_imgui.begin_popup_context_item("Item Context Menu")
    assert isinstance(item, meltygui_imgui.core._BeginEndPopup)
    assert item.opened is False
    assert item == item
    assert item == bool(item)
    meltygui_imgui.end()


def test_popup_context_window_isinstance(frame):
    meltygui_imgui.begin("Example: popup context window")
    window = meltygui_imgui.begin_popup_context_window()
    assert isinstance(window, meltygui_imgui.core._BeginEndPopup)
    assert window.opened is False
    assert window == window
    assert window == bool(window)
    meltygui_imgui.end()


def test_popup_context_void_isinstance(frame):
    window = meltygui_imgui.begin_popup_context_void()
    assert isinstance(window, meltygui_imgui.core._BeginEndPopup)
    assert window.opened is False
    assert window == window
    assert window == bool(window)


# ------- BEGIN_POPUP_MODAL/END_POPUP_MODAL ----------
def test_popup_modal_okay(frame):
    meltygui_imgui.begin("Example: simple popup modal")
    meltygui_imgui.open_popup("select-popup")
    if meltygui_imgui.begin_popup_modal("select-popup")[0]:
        meltygui_imgui.end_popup()
    meltygui_imgui.end()


def test_popup_modal_with(frame):
    with meltygui_imgui.begin("Example: simple popup modal"):
        meltygui_imgui.open_popup("select-popup")
        with meltygui_imgui.begin_popup_modal("select-popup"):
            pass


def test_popup_modal_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: simple popup modal"):
            meltygui_imgui.open_popup("select-popup")
            with meltygui_imgui.begin_popup_modal("select-popup"):
                raise _TestException


def test_popup_modal_as_bool(frame):
    meltygui_imgui.begin("Example: simple popup modal")
    meltygui_imgui.open_popup("select-popup")
    popup = meltygui_imgui.begin_popup_modal("select-popup")
    assert popup.opened is True
    assert popup.visible is False
    opened, visible = popup
    assert opened is popup.opened is popup[0]
    assert visible is popup.visible is popup[1]
    assert popup == popup
    assert popup == tuple(popup)
    meltygui_imgui.end_popup()
    meltygui_imgui.end()


# ------- BEGIN_DRAG_DROP_SOURCE/END_DRAG_DROP_SOURCE ----------
def test_drag_drop_source_okay(frame):
    meltygui_imgui.begin("Example: drag and drop")
    meltygui_imgui.button('source')
    if meltygui_imgui.begin_drag_drop_source():
        meltygui_imgui.set_drag_drop_payload('itemtype', b'payload')
        meltygui_imgui.end_drag_drop_source()
    meltygui_imgui.end()


def test_drag_drop_source_with(frame):
    with meltygui_imgui.begin("Example: drag and drop"):
        meltygui_imgui.button('source')
        with meltygui_imgui.begin_drag_drop_source():
            pass


def test_drag_drop_source_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: drag and drop"):
            meltygui_imgui.button('source')
            with meltygui_imgui.begin_drag_drop_source():
                raise _TestException


def test_drag_drop_source_as_bool(frame):
    meltygui_imgui.begin("Example: drag and drop")
    meltygui_imgui.button('source')
    src = meltygui_imgui.begin_drag_drop_source()
    assert bool(src) is src.dragging is False
    assert src == src
    assert src == bool(src)
    meltygui_imgui.end()


# ------- BEGIN_DRAG_DROP_TARGET/END_DRAG_DROP_TARGET ----------
def test_drag_drop_target_okay(frame):
    meltygui_imgui.begin("Example: drag and drop")
    meltygui_imgui.button('dest')
    if meltygui_imgui.begin_drag_drop_target():
        payload = meltygui_imgui.accept_drag_drop_payload('itemtype')
        meltygui_imgui.end_drag_drop_target()
    meltygui_imgui.end()


def test_drag_drop_target_with(frame):
    with meltygui_imgui.begin("Example: drag and drop"):
        meltygui_imgui.button('dest')
        with meltygui_imgui.begin_drag_drop_target():
            pass


def test_drag_drop_target_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: drag and drop"):
            meltygui_imgui.button('dest')
            with meltygui_imgui.begin_drag_drop_target():
                raise _TestException


def test_drag_drop_target_as_bool(frame):
    meltygui_imgui.begin("Example: drag and drop")
    meltygui_imgui.button('dest')
    target = meltygui_imgui.begin_drag_drop_target()
    assert bool(target) is target.hovered is False
    assert target == target
    assert target == bool(target)
    meltygui_imgui.end()


# ------- BEGIN_GROUP/END_GROUP ----------
def test_group_okay(frame):
    meltygui_imgui.begin("Example: item groups")
    meltygui_imgui.begin_group()
    meltygui_imgui.text("First group (buttons):")
    meltygui_imgui.end_group()
    meltygui_imgui.end()


def test_group_with(frame):
    with meltygui_imgui.begin("Example: item groups"):
        with meltygui_imgui.begin_group():
            meltygui_imgui.text("First group (buttons):")


def test_group_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: item groups"):
            with meltygui_imgui.begin_group():
                raise _TestException


# ------- BEGIN_LIST_BOX/END_LIST_BOX ----------
def test_list_box_okay(frame):
    meltygui_imgui.begin("Example: custom listbox")
    if meltygui_imgui.begin_list_box("List", 200, 100):
        meltygui_imgui.selectable("Selected", True)
        meltygui_imgui.selectable("Not Selected", False)
        meltygui_imgui.end_list_box()
    meltygui_imgui.end()


def test_list_box_with(frame):
    with meltygui_imgui.begin("Example: custom listbox"):
        with meltygui_imgui.begin_list_box("List", 200, 100):
            pass


def test_list_box_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: custom listbox"):
            with meltygui_imgui.begin_list_box("List", 200, 100):
                raise _TestException


def test_list_box_as_bool(frame):
    meltygui_imgui.begin("Example: custom listbox")
    list_box = meltygui_imgui.begin_list_box("List", 200, 100)
    assert bool(list_box) is list_box.opened is True
    assert list_box == list_box
    assert list_box == bool(list_box)
    meltygui_imgui.end_list_box()
    meltygui_imgui.end()


# ------- BEGIN_TABLE/END_TABLE ----------
def test_table_okay(frame):
    meltygui_imgui.begin("Example: table")
    if meltygui_imgui.begin_table("data", 2):
        meltygui_imgui.end_table()
    meltygui_imgui.end()


def test_table_with(frame):
    with meltygui_imgui.begin("Example: table"):
        with meltygui_imgui.begin_table("data", 2):
            pass


def test_table_with_exception(frame):
    # the real test is that the frame cleanup doesn't crash
    with pytest.raises(_TestException):
        with meltygui_imgui.begin("Example: table"):
            with meltygui_imgui.begin_table("data", 2):
                raise _TestException


def test_table_as_bool(frame):
    meltygui_imgui.begin("Example: table")
    table = meltygui_imgui.begin_table("data", 2)
    assert bool(table) is table.opened is True
    assert table == table
    assert table == bool(table)
    meltygui_imgui.end_table()
    meltygui_imgui.end()
