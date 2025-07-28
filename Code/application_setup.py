import pygame
import pyperclip
from Code.utilities import move_number_to_desired_range, get_time
from Code.Editor.editor_loop import editor_loop, EditorSingleton
from Code.Game.game_loop import game_loop, GameSingleton
from typing import Callable, Iterable
from Code.utilities import COLORS


def application_setup(Render):
    pygame.init()
    #
    # timing
    Time = TimingClass()
    #
    # keys
    Keys = KeysClass()
    #
    # cursor
    Cursor = CursorClass(Render)
    #
    return Time, Keys, Cursor


class ApiObject():
    EDITOR = 'Editor'
    GAME = 'Game'
    MENU = 'Menu'

    def __init__(self, Render):
        self.scroll_x = 0
        self.scroll_y = 0
        self.setup_required = True
        self.current_api = ApiObject.EDITOR
        self.stored_api = None
        self.api_options = {ApiObject.EDITOR: editor_loop,
                            ApiObject.GAME: game_loop, 
                            ApiObject.MENU: False,}
        self.api_singletons = {ApiObject.EDITOR: EditorSingleton,
                               ApiObject.GAME: GameSingleton, 
                               ApiObject.MENU: False,}
        self.api_initiated_singletons = {ApiObject.EDITOR: 0,
                                         ApiObject.GAME: 0, 
                                         ApiObject.MENU: 0,}
    
    def initiate_api_switch(self, new_api: str):
        self.setup_required = True
        self.stored_api = new_api

    def run_api(self, *args):
        if self.stored_api is not None:
            self.current_api = self.stored_api
            self.stored_api = None
        self.api_options[self.current_api](*args)


class TimingClass():
    _TEXT_PIXEL_SIZE = 4
    DESIRED_FPS = 60

    def __init__(self):
        self.clock = pygame.time.Clock()
        self.previous_tick = pygame.time.get_ticks()
        self.current_tick = pygame.time.get_ticks()
        self.fps = TimingClass.DESIRED_FPS
        self.delta_time = (self.current_tick - self.previous_tick) / 1000
    #
    def update(self):
        self.previous_tick = self.current_tick
        self.current_tick = pygame.time.get_ticks()
        self.delta_time = (self.current_tick - self.previous_tick) / 1000
        self.delta_time = move_number_to_desired_range(0.001, self.delta_time, 99999999999)
        self.fps = 1 / self.delta_time
        self.clock.tick(TimingClass.DESIRED_FPS)
    #
    def display_fps(self, Screen, Render, gl_context, lt: list[int, int]):
        fps = str(round(self.fps / 10) * 10)
        Render.draw_string_of_characters(Screen, gl_context, fps, lt, TimingClass._TEXT_PIXEL_SIZE, COLORS['BLACK'])


class Cursor():
    def __init__(self, name: str, offset_x: int, offset_y: int, priority: int, images: Iterable[str], render_functions: Iterable[Callable] | None):
        self.name: str = name
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y
        self.priority: int = priority
        self.images: Iterable[str] = images
        self.render_functions: Iterable[Callable] = render_functions


class CursorClass():

    DEFAULT_OFFSET = 0
    DEFAULT_PRIORITY = 0
    DEFAULT_IMAGE = 'black_pixel'

    def __init__(self, Render):
        self.cursors = {
            'black_pixel': Cursor(name='black_pixel', offset_x=0, offset_y=0, priority=9999, images=['black_pixel'], render_functions=[Render.invert_white]),  # used for debugging
            'cursor_arrow': Cursor(name='cursor_arrow', offset_x=0, offset_y=0, priority=1, images=['cursor_arrow'], render_functions=[Render.basic_rect_ltwh_to_quad]),
            'cursor_crosshair': Cursor(name='cursor_crosshair', offset_x=-3, offset_y=-3, priority=5, images=['cursor_crosshair'], render_functions=[Render.basic_rect_ltwh_to_quad]),
            'cursor_big_crosshair': Cursor(name='cursor_big_crosshair', offset_x=-10, offset_y=-10, priority=7, images=['cursor_big_crosshair'], render_functions=[Render.invert_white]),
            'cursor_nesw': Cursor(name='cursor_nesw', offset_x=-13, offset_y=-13, priority=99, images=['cursor_nesw'], render_functions=[Render.basic_rect_ltwh_to_quad]),
            'cursor_eyedrop': Cursor(name='cursor_eyedrop', offset_x=0, offset_y=-21, priority=6, images=['cursor_eyedrop'], render_functions=[Render.basic_rect_ltwh_to_quad]),
            'cursor_i_beam': Cursor(name='cursor_i_beam', offset_x=-6, offset_y=-9, priority=2, images=['cursor_i_beam'], render_functions=[Render.invert_white])
            }
        self.current_cursor: Cursor | None = None
    #
    def update_cursor(self, Screen, gl_context, Render, Keys):
        # check that a cursor was added this frame
        if self.current_cursor is None:
            return
        # draw every layer of the cursor
        for image, render_function in zip(self.current_cursor.images, self.current_cursor.render_functions):
            render_function(Screen, gl_context, image, [Keys.cursor_x_pos.value + self.current_cursor.offset_x, Keys.cursor_y_pos.value + self.current_cursor.offset_y, Render.renderable_objects[image].ORIGINAL_WIDTH, Render.renderable_objects[image].ORIGINAL_HEIGHT])
        # reset the cursor for next frame
        self.current_cursor = None
    #
    def add_cursor_this_frame(self, added_cursor: str):
        # check that the new cursor exists
        new_cursor = self.cursors.get(added_cursor)
        if new_cursor is None:
            return
        # select which cursor should be used based on priority
        if self.current_cursor is None:
            self.current_cursor = new_cursor
        elif self.current_cursor.priority < new_cursor.priority:
            self.current_cursor = new_cursor
    #
    @staticmethod
    def set_cursor_pos(Keys, x_pos: int | None = None, y_pos: int | None = None):
        if x_pos is None:
            x_pos = Keys.cursor_x_pos.value
        if y_pos is None:
            y_pos = Keys.cursor_y_pos.value
        pygame.mouse.set_pos(x_pos, y_pos)
    #
    @staticmethod
    def set_cursor_visibility(visible: bool):
        pygame.mouse.set_visible(visible)
    #
    @staticmethod
    def cursor_is_visible():
        return pygame.mouse.get_visible()


class IOKey():
    def __init__(self, mapping):
        self.mapping = mapping
        self.pressed = False
        self.last_pressed = False
        self.newly_pressed = False
        self.released = False
    #
    def update(self, new_value):
        self.last_pressed = self.pressed
        self.pressed = new_value
        self.newly_pressed = self.pressed and not self.last_pressed
        self.released = not self.pressed and self.last_pressed


class AnalogKey():
    def __init__(self, mapping):
        self.mapping = mapping
        self.value = -1
        self.last_value = -1
        self.delta = -1
    #
    def update(self, new_value):
        self.last_value = self.value
        self.value = new_value
        self.delta = self.value - self.last_value


class KeysClass():
    def __init__(self):
        # keyboard
        self.using_keyboard = True
        self.keys = -1
        self.left_click, self.middle_click, self.right_click = -1, -1, -1
        self.mouse_x_pos, self.mouse_y_pos = -1, -1
        self.scroll_x, self.scroll_y = 0, 0
        #
        self.update_io_and_analog: Callable
        self.get_update_function()
        #
        # mapping
        self.ANALOG_MAPPING = {
            # mouse position
            'MOUSE_X_POS': lambda: self.mouse_x_pos,
            'MOUSE_Y_POS': lambda: self.mouse_y_pos,
            'SCROLL_X': lambda: self.scroll_x,
            'SCROLL_Y': lambda: self.scroll_y,
        }
        self.IO_MAPPING = {
            # keyboard
            'BACKSPACE': lambda: self.keys[pygame.K_BACKSPACE],
            'TAB': lambda: self.keys[pygame.K_TAB],
            'RETURN': lambda: self.keys[pygame.K_RETURN],
            'ESCAPE': lambda: self.keys[pygame.K_ESCAPE],
            'SPACE': lambda: self.keys[pygame.K_SPACE],
            ',': lambda: self.keys[pygame.K_COMMA],
            '-': lambda: self.keys[pygame.K_MINUS],
            '.': lambda: self.keys[pygame.K_PERIOD],
            '/': lambda: self.keys[pygame.K_SLASH],
            '0': lambda: self.keys[pygame.K_0],
            '1': lambda: self.keys[pygame.K_1],
            '2': lambda: self.keys[pygame.K_2],
            '3': lambda: self.keys[pygame.K_3],
            '4': lambda: self.keys[pygame.K_4],
            '5': lambda: self.keys[pygame.K_5],
            '6': lambda: self.keys[pygame.K_6],
            '7': lambda: self.keys[pygame.K_7],
            '8': lambda: self.keys[pygame.K_8],
            '9': lambda: self.keys[pygame.K_9],
            ';': lambda: self.keys[pygame.K_SEMICOLON],
            '=': lambda: self.keys[pygame.K_EQUALS],
            '[': lambda: self.keys[pygame.K_LEFTBRACKET],
            ']': lambda: self.keys[pygame.K_RIGHTBRACKET],
            'A': lambda: self.keys[pygame.K_a],
            'B': lambda: self.keys[pygame.K_b],
            'C': lambda: self.keys[pygame.K_c],
            'D': lambda: self.keys[pygame.K_d],
            'E': lambda: self.keys[pygame.K_e],
            'F': lambda: self.keys[pygame.K_f],
            'G': lambda: self.keys[pygame.K_g],
            'H': lambda: self.keys[pygame.K_h],
            'I': lambda: self.keys[pygame.K_i],
            'J': lambda: self.keys[pygame.K_j],
            'K': lambda: self.keys[pygame.K_k],
            'L': lambda: self.keys[pygame.K_l],
            'M': lambda: self.keys[pygame.K_m],
            'N': lambda: self.keys[pygame.K_n],
            'O': lambda: self.keys[pygame.K_o],
            'P': lambda: self.keys[pygame.K_p],
            'Q': lambda: self.keys[pygame.K_q],
            'R': lambda: self.keys[pygame.K_r],
            'S': lambda: self.keys[pygame.K_s],
            'T': lambda: self.keys[pygame.K_t],
            'U': lambda: self.keys[pygame.K_u],
            'V': lambda: self.keys[pygame.K_v],
            'W': lambda: self.keys[pygame.K_w],
            'X': lambda: self.keys[pygame.K_x],
            'Y': lambda: self.keys[pygame.K_y],
            'Z': lambda: self.keys[pygame.K_z],
            'DELETE': lambda: self.keys[pygame.K_DELETE],
            'UP': lambda: self.keys[pygame.K_UP],
            'DOWN': lambda: self.keys[pygame.K_DOWN],
            'LEFT': lambda: self.keys[pygame.K_LEFT],
            'RIGHT': lambda: self.keys[pygame.K_RIGHT],
            'INSERT': lambda: self.keys[pygame.K_INSERT],
            'HOME': lambda: self.keys[pygame.K_HOME],
            'END': lambda: self.keys[pygame.K_END],
            'PAGE_UP': lambda: self.keys[pygame.K_PAGEUP],
            'PAGE_DOWN': lambda: self.keys[pygame.K_PAGEDOWN],
            'F1': lambda: self.keys[pygame.K_F1],
            'F2': lambda: self.keys[pygame.K_F2],
            'F3': lambda: self.keys[pygame.K_F3],
            'F4': lambda: self.keys[pygame.K_F4],
            'F5': lambda: self.keys[pygame.K_F5],
            'F6': lambda: self.keys[pygame.K_F6],
            'F7': lambda: self.keys[pygame.K_F7],
            'F8': lambda: self.keys[pygame.K_F8],
            'F9': lambda: self.keys[pygame.K_F9],
            'F10': lambda: self.keys[pygame.K_F10],
            'F11': lambda: self.keys[pygame.K_F11],
            'F12': lambda: self.keys[pygame.K_F12],
            'CAPSLOCK': lambda: self.keys[pygame.K_CAPSLOCK],
            'SHIFT': lambda: self.keys[pygame.K_RSHIFT] or self.keys[pygame.K_LSHIFT],
            'CONTROL': lambda: self.keys[pygame.K_RCTRL] or self.keys[pygame.K_LCTRL],
            'ALT': lambda: self.keys[pygame.K_RALT] or self.keys[pygame.K_LALT],
            '\\': lambda: self.keys[pygame.K_BACKSLASH],
            '/': lambda: self.keys[pygame.K_SLASH],
            # mouse clicks
            'LEFT_CLICK': lambda: self.left_click,
            'MIDDLE_CLICK': lambda: self.middle_click,
            'RIGHT_CLICK': lambda: self.right_click,
            }
        #
        # controls
        # common
        self.cursor_x_pos = AnalogKey(mapping=self.ANALOG_MAPPING['MOUSE_X_POS'])
        self.cursor_y_pos = AnalogKey(mapping=self.ANALOG_MAPPING['MOUSE_Y_POS'])
        # editor
        self.editor_primary = IOKey(mapping=self.IO_MAPPING['LEFT_CLICK'])
        self.editor_secondary = IOKey(mapping=self.IO_MAPPING['RIGHT_CLICK'])
        self.editor_hand = IOKey(mapping=self.IO_MAPPING['MIDDLE_CLICK'])
        self.editor_up = IOKey(mapping=self.IO_MAPPING['UP'])
        self.editor_left = IOKey(mapping=self.IO_MAPPING['LEFT'])
        self.editor_down = IOKey(mapping=self.IO_MAPPING['DOWN'])
        self.editor_right = IOKey(mapping=self.IO_MAPPING['RIGHT'])
        self.editor_shift = IOKey(mapping=self.IO_MAPPING['SHIFT'])
        self.editor_control = IOKey(mapping=self.IO_MAPPING['CONTROL'])
        self.editor_tab = IOKey(mapping=self.IO_MAPPING['TAB'])
        self.editor_scroll_x = AnalogKey(mapping=self.ANALOG_MAPPING['SCROLL_X'])
        self.editor_scroll_y = AnalogKey(mapping=self.ANALOG_MAPPING['SCROLL_Y'])
        # main game
        self.primary = IOKey(mapping=self.IO_MAPPING['LEFT_CLICK'])
        self.secondary = IOKey(mapping=self.IO_MAPPING['RIGHT_CLICK'])
        self.release_grapple = IOKey(mapping=self.IO_MAPPING['SPACE'])
        self.float_up = IOKey(mapping=self.IO_MAPPING['W'])
        self.left = IOKey(mapping=self.IO_MAPPING['A'])
        self.sink_down = IOKey(mapping=self.IO_MAPPING['S'])
        self.right = IOKey(mapping=self.IO_MAPPING['D'])
        self.select = IOKey(mapping=self.IO_MAPPING['RETURN'])
        self.interact = IOKey(mapping=self.IO_MAPPING['E'])
        self.pause = IOKey(mapping=self.IO_MAPPING['ESCAPE'])
        #
        self.controls = [
            # common
            self.cursor_x_pos, self.cursor_y_pos, 
            # editor
            self.editor_primary, self.editor_secondary, self.editor_hand, self.editor_up, self.editor_left, self.editor_down, self.editor_right, self.editor_shift, self.editor_control, self.editor_tab, self.editor_scroll_x, self.editor_scroll_y,
            # main game
            self.primary, self.secondary, self.release_grapple, self.float_up, self.left, self.sink_down, self.right, self.select, self.interact, self.pause,
        ]
    #
    def copy_text(self, text: str):
        pyperclip.copy(text)
    #
    def paste_text(self):
        return pyperclip.paste()
    #
    def update_controls(self, Api):
        self.update_io_and_analog(Api)
        self.apply_updates_to_controls()

    def get_update_function(self):
        if self.using_keyboard:
            self.update_io_and_analog = self.update_keyboard
            return
    #
    def update_keyboard(self, Api):
        self.keys = pygame.key.get_pressed()
        self.left_click, self.middle_click, self.right_click = pygame.mouse.get_pressed()
        self.mouse_x_pos, self.mouse_y_pos = pygame.mouse.get_pos()
        self.scroll_x, self.scroll_y = Api.scroll_x, Api.scroll_y
    #
    def apply_updates_to_controls(self):
        for control in self.controls:
            control.update(control.mapping())
    #
    def keyboard_key_to_character(self):
        if self.keys[pygame.K_LCTRL] or self.keys[pygame.K_RCTRL]:
            if self.keys[pygame.K_a]: return 'CTRL_A'
            if self.keys[pygame.K_c]: return 'CTRL_C'
            if self.keys[pygame.K_v]: return 'CTRL_V'
            if self.keys[pygame.K_x]: return 'CTRL_X'
            if self.keys[pygame.K_z]: return 'CTRL_Z'
            if self.keys[pygame.K_BACKSPACE]: return 'CTRL_BACKSPACE'
            if self.keys[pygame.K_DELETE]: return 'CTRL_DELETE'
        if self.keys[pygame.K_UP]: return 'UP'
        if self.keys[pygame.K_DOWN]: return 'DOWN'
        if self.keys[pygame.K_DELETE]: return 'DELETE'
        if self.keys[pygame.K_BACKSPACE]: return 'BACKSPACE'
        if self.keys[pygame.K_RETURN]: return 'RETURN'
        if self.keys[pygame.K_SPACE]: return ' '
        if not self.keys[pygame.K_LSHIFT] and not self.keys[pygame.K_RSHIFT]:
            if self.keys[pygame.K_0]: return '0'
            if self.keys[pygame.K_1]: return '1'
            if self.keys[pygame.K_2]: return '2'
            if self.keys[pygame.K_3]: return '3'
            if self.keys[pygame.K_4]: return '4'
            if self.keys[pygame.K_5]: return '5'
            if self.keys[pygame.K_6]: return '6'
            if self.keys[pygame.K_7]: return '7'
            if self.keys[pygame.K_8]: return '8'
            if self.keys[pygame.K_9]: return '9'
            if self.keys[pygame.K_a]: return 'a'
            if self.keys[pygame.K_b]: return 'b'
            if self.keys[pygame.K_c]: return 'c'
            if self.keys[pygame.K_d]: return 'd'
            if self.keys[pygame.K_e]: return 'e'
            if self.keys[pygame.K_f]: return 'f'
            if self.keys[pygame.K_g]: return 'g'
            if self.keys[pygame.K_h]: return 'h'
            if self.keys[pygame.K_i]: return 'i'
            if self.keys[pygame.K_j]: return 'j'
            if self.keys[pygame.K_k]: return 'k'
            if self.keys[pygame.K_l]: return 'l'
            if self.keys[pygame.K_m]: return 'm'
            if self.keys[pygame.K_n]: return 'n'
            if self.keys[pygame.K_o]: return 'o'
            if self.keys[pygame.K_p]: return 'p'
            if self.keys[pygame.K_q]: return 'q'
            if self.keys[pygame.K_r]: return 'r'
            if self.keys[pygame.K_s]: return 's'
            if self.keys[pygame.K_t]: return 't'
            if self.keys[pygame.K_u]: return 'u'
            if self.keys[pygame.K_v]: return 'v'
            if self.keys[pygame.K_w]: return 'w'
            if self.keys[pygame.K_x]: return 'x'
            if self.keys[pygame.K_y]: return 'y'
            if self.keys[pygame.K_z]: return 'z'
            if self.keys[pygame.K_SLASH]: return '/'
            if self.keys[pygame.K_BACKSLASH]: return '\\'
        else:
            if self.keys[pygame.K_0]: return ')'
            if self.keys[pygame.K_1]: return '!'
            if self.keys[pygame.K_2]: return '@'
            if self.keys[pygame.K_3]: return '#'
            if self.keys[pygame.K_4]: return '$'
            if self.keys[pygame.K_5]: return '%'
            if self.keys[pygame.K_6]: return '^'
            if self.keys[pygame.K_7]: return '&'
            if self.keys[pygame.K_8]: return '*'
            if self.keys[pygame.K_9]: return '('
            if self.keys[pygame.K_a]: return 'A'
            if self.keys[pygame.K_b]: return 'B'
            if self.keys[pygame.K_c]: return 'C'
            if self.keys[pygame.K_d]: return 'D'
            if self.keys[pygame.K_e]: return 'E'
            if self.keys[pygame.K_f]: return 'F'
            if self.keys[pygame.K_g]: return 'G'
            if self.keys[pygame.K_h]: return 'H'
            if self.keys[pygame.K_i]: return 'I'
            if self.keys[pygame.K_j]: return 'J'
            if self.keys[pygame.K_k]: return 'K'
            if self.keys[pygame.K_l]: return 'L'
            if self.keys[pygame.K_m]: return 'M'
            if self.keys[pygame.K_n]: return 'N'
            if self.keys[pygame.K_o]: return 'O'
            if self.keys[pygame.K_p]: return 'P'
            if self.keys[pygame.K_q]: return 'Q'
            if self.keys[pygame.K_r]: return 'R'
            if self.keys[pygame.K_s]: return 'S'
            if self.keys[pygame.K_t]: return 'T'
            if self.keys[pygame.K_u]: return 'U'
            if self.keys[pygame.K_v]: return 'V'
            if self.keys[pygame.K_w]: return 'W'
            if self.keys[pygame.K_x]: return 'X'
            if self.keys[pygame.K_y]: return 'Y'
            if self.keys[pygame.K_z]: return 'Z'
        return None
