# -*- coding: utf-8 -*-
import glfw
import OpenGL.GL as gl

import meltygui_imgui
from meltygui_imgui.integrations.glfw import GlfwRenderer

class callable_class(object):
    def __init__(self, data):
        data.user_data.setSize(data.desired_size)

class foo(object):
    
    def __init__(self):
        self.size = (0,0)
    
    def method(self, data):
        self.size = data.desired_size
    
    @staticmethod
    def static_method(data):
        data.user_data.setSize(data.desired_size)
    
    def __call__(self, data):
        self.size = data.desired_size
    
def generate_lambda():
    return (lambda data : data.user_data.setSize(data.desired_size))

def generate_closure():
    counter = [0]
    def callback(data):
        counter[0] += 1
        data.user_data.setSize(data.desired_size)
        data.user_data.setCounter(counter[0])
    return callback

def my_decorator(func):
    counter = [0]
    def inner(*args, **kwargs):
        counter[0] += 1
        if counter[0] in (10,100,1000):
            print('Decorator counter is %i!' % counter[0])
        func(*args, **kwargs)
    return inner
    
@my_decorator
def my_func(data):
    data.user_data.setSize(data.desired_size)

def text_edit_callback(data):
    if(data.event_flag == meltygui_imgui.INPUT_TEXT_CALLBACK_EDIT):
        print('EDIT')
        print('user_data:', data.user_data)
        print('event_flag:', data.event_flag)
        print('flags:', data.flags)
        print('event_char:', data.event_char)
        print('cursor_pos:', data.cursor_pos)
        print('selection_start:', data.selection_start)
        print('selection_end:', data.selection_end)
        
        print('buf:', data.buffer)
        print('buf text length:', data.buffer_text_length)
        print('buf size:', data.buffer_size)
        #data.selection_start = data.cursor_pos-1
        #data.selection_end = data.cursor_pos
        #data.cursor_pos = 0
        
        
    elif(data.event_flag == meltygui_imgui.INPUT_TEXT_CALLBACK_CHAR_FILTER):
        print('FILTER')
        print('event_char:', data.event_char)
        
        if data.event_char == 'a':
            data.event_char = 'A'
            data.buffer_dirty = True
    else:
        
        if(data.has_selection()):
            print('selection_start:', data.selection_start)
            print('selection_end:', data.selection_end)
            begin = min(data.selection_start,data.selection_end)
            data.delete_chars(begin, abs(data.selection_end-data.selection_start))
            data.insert_chars(begin, "YOLO")
            data.selection_end = begin + len("YOLO")
            
        #data.delete_chars(0, len("Test"))
        #data.insert_chars(0, "Test")
        #data.select_all()
    
    return 0

def force_square_size_callback(data):
    
    #print('user_data:', data.user_data)
    #print('pos:', data.pos)
    #print('current_size:', data.current_size)
    
    data.desired_size = data.desired_size.x, data.desired_size.x
    
    return
    
def force_half_height_size_callback(data):
    data.desired_size = data.desired_size.x, data.desired_size.x/2

class special_info(object):
    
    def __init__(self):
        self.size = (0,0)
        self.counter = 0
    
    def setSize(self, size):
        self.size = size
    
    def setCounter(self, counter):
        self.counter = counter


def main():

    meltygui_imgui.create_context()
    window = impl_glfw_init()
    impl = GlfwRenderer(window)
    
    # Utilities
    text_val = 'Change me!'
    spinf = special_info()
    foo_instance = foo()
    my_closure = generate_closure()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        meltygui_imgui.new_frame()
        
        # === TEXT INPUT CALLBACKS ===
        
        meltygui_imgui.begin('Text Callbacks')
        
        # No Callback
        changed, text_val = meltygui_imgui.input_text('No callback', text_val, 512, 0)
        
        # Only one callback call
        changed, text_val = meltygui_imgui.input_text('One callback', text_val, 512, 
                                                meltygui_imgui.INPUT_TEXT_CALLBACK_CHAR_FILTER,
                                                text_edit_callback)
        
        # Callback is called multiple times depending on events
        changed, text_val = meltygui_imgui.input_text('Multiple callback', text_val, 512, 
                                                meltygui_imgui.INPUT_TEXT_CALLBACK_EDIT | 
                                                meltygui_imgui.INPUT_TEXT_CALLBACK_CHAR_FILTER | 
                                                meltygui_imgui.INPUT_TEXT_CALLBACK_HISTORY, 
                                                text_edit_callback, {'special':42})
        meltygui_imgui.end()
        
        
        # === SIZE CALLBACKS ===
        
        # Multiple set don't leak memory, only last callback is used
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), force_square_size_callback, 'test')
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), force_half_height_size_callback)
        meltygui_imgui.begin('Callback 1')
        meltygui_imgui.end()
        
        # Next begin doesn't have callback anymore
        meltygui_imgui.begin('Without callback after previous callback')
        meltygui_imgui.end()
        
        # We can apply another callback for another begin()/end() pair
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), force_square_size_callback, 'test')
        meltygui_imgui.begin('Callback 2')
        meltygui_imgui.end()
            
        # Class callable
        meltygui_imgui.set_next_window_size_constraints((200,10), (1000,1000), callable_class, spinf )
        meltygui_imgui.begin('Callback: class')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.end()
        
        # Static method callable
        meltygui_imgui.set_next_window_size_constraints((200,10), (1000,1000), foo.static_method, spinf )
        meltygui_imgui.begin('Callback: static method')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.end()
        
        # Method callable - User Data can be sent via instance properties
        meltygui_imgui.set_next_window_size_constraints((200,10), (1000,1000), foo_instance.method )
        meltygui_imgui.begin('Callback: method')
        meltygui_imgui.text("Window Size: %ix%i" % foo_instance.size)
        meltygui_imgui.end()
        
        # Instance callable - User Data can be sent via instance properties
        meltygui_imgui.set_next_window_size_constraints((200,10), (1000,1000), foo_instance )
        meltygui_imgui.begin('Callback: callable instance')
        meltygui_imgui.text("Window Size: %ix%i" % foo_instance.size)
        meltygui_imgui.end()
        
        # Lambda callable
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), lambda data : data.user_data.setSize(data.desired_size), spinf )
        meltygui_imgui.begin('Callback: lambda')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.end()
        
        # Generated lambda callable
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), generate_lambda(), spinf )
        meltygui_imgui.begin('Callback: gen lambda')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.end()
        
        # Closure callable
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), my_closure, spinf )
        meltygui_imgui.begin('Callback: closure')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.text("Counter: %i" % spinf.counter)
        meltygui_imgui.end()
        
        # Decorated callable
        meltygui_imgui.set_next_window_size_constraints((10,10), (1000,1000), my_func, spinf )
        meltygui_imgui.begin('Callback: decorator')
        meltygui_imgui.text("Window Size: %ix%i" % spinf.size)
        meltygui_imgui.end()
        
        # === END OF TESTS ===
        
        gl.glClearColor(1., 1., 1., 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        meltygui_imgui.render()
        impl.render(meltygui_imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


def impl_glfw_init():
    width, height = 1280, 720
    window_name = "minimal ImGui/GLFW3 example"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(
        int(width), int(height), window_name, None, None
    )
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        exit(1)

    return window


if __name__ == "__main__":
    main()
