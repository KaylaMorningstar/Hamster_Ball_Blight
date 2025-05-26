from Code.utilities import CaseBreak, ONE_FRAME_AT_60_FPS, angle_in_range, atan2, rgba_to_glsl, get_blended_color_float, get_blended_color_int, percent_to_rgba, point_is_in_ltwh, move_number_to_desired_range, get_text_width, get_text_height, get_time, str_can_be_int, str_can_be_float, str_can_be_hex, switch_to_base10, base10_to_hex, add_characters_to_front_of_string, get_rect_minus_borders, COLORS
import pygame
import math
from copy import deepcopy
from abc import ABC
from array import array
from bresenham import bresenham
from typing import Any
from random import choice, shuffle, randint
from enum import unique, Enum


@unique
class FooterInfo(Enum):
    SEPARATOR = 0
    MAP_SIZE = 1
    CURSOR_POSITION = 2
    ACTIVE_COLOR = 3

@unique
class MapModes(Enum):
    PRETTY = 1
    COLLISION = 2

@unique
class EditorModes(Enum):
    DRAW = 1
    BLOCK = 2
    OBJECT = 3

class CollisionMode:
    UTF_8 = 'utf-8'
    NEW_LINE = '\n'

    NO_COLLISION = 0
    COLLISION = 1
    GRAPPLEABLE = 2
    PLATFORM = 3
    WATER = 4

    NO_COLLISION_BINARY = b'\x00'
    COLLISION_BINARY = b'\x01'
    GRAPPLEABLE_BINARY = b'\x02'
    PLATFORM_BINARY = b'\x03'
    WATER_BINARY = b'\x04'

    NO_COLLISION_BYTEARRAY = bytearray(b'\x00')
    COLLISION_BYTEARRAY = bytearray(b'\x01')
    GRAPPLEABLE_BYTEARRAY = bytearray(b'\x02')
    PLATFORM_BYTEARRAY = bytearray(b'\x03')
    WATER_BYTEARRAY = bytearray(b'\x04')

    NO_COLLISION_COLOR = COLORS['WHITE']
    COLLISION_COLOR = COLORS['BLACK']
    GRAPPLEABLE_COLOR = COLORS['RED']
    PLATFORM_COLOR = COLORS['YELLOW']
    WATER_COLOR = COLORS['BLUE']


class TextInput():
    _STOPPING_CHARACTERS = ' ,.?!:;/\\[](){}'
    def __init__(self, 
                 background_ltwh: list[int], 
                 background_color: list[float], 
                 text_color: list[float], 
                 highlighted_text_color: list[float],
                 highlight_color: list[float],
                 text_pixel_size: int, 
                 text_padding: int, 
                 allowable_range: list[float | int, float | int] = [-math.inf, math.inf], 
                 is_an_int: bool = False, 
                 is_a_float: bool = False,
                 is_a_hex: bool = False,
                 show_front_zeros: bool = False,
                 number_of_digits: int = 0,
                 must_fit: bool = False,
                 default_value: str = '0',
                 ending_characters: str = ''):

        self.background_ltwh = background_ltwh
        self.background_color = background_color
        self.text_color = text_color
        self.highlighted_text_color = highlighted_text_color
        self.highlight_color = highlight_color
        self.text_pixel_size = text_pixel_size
        self.text_padding = text_padding
        self.allowable_range = allowable_range
        self.is_a_float = is_a_float
        self.is_an_int = is_an_int
        self.is_a_hex = is_a_hex
        self.show_front_zeros = show_front_zeros
        self.number_of_digits = number_of_digits
        self.must_fit = must_fit
        self.default_value = default_value
        if self.is_a_float:
            self.allowable_keys = ['RETURN', 'DELETE', 'BACKSPACE', 'UP', 'DOWN', 'CTRL_A', 'CTRL_C', 'CTRL_V', 'CTRL_X', 'CTRL_BACKSPACE', 'CTRL_DELETE', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '.']
        if self.is_an_int:
            self.allowable_keys = ['RETURN', 'DELETE', 'BACKSPACE', 'UP', 'DOWN', 'CTRL_A', 'CTRL_C', 'CTRL_V', 'CTRL_X', 'CTRL_BACKSPACE', 'CTRL_DELETE', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        if self.is_a_hex:
            self.allowable_keys = ['RETURN', 'DELETE', 'BACKSPACE', 'UP', 'DOWN', 'CTRL_A', 'CTRL_C', 'CTRL_V', 'CTRL_X', 'CTRL_BACKSPACE', 'CTRL_DELETE', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
        #
        self.text_height = get_text_height(self.text_pixel_size) - (2 * self.text_pixel_size)
        self.highlighted_index_range = [2, 5]
        self.blinking_cycle_duration = 1.15 # whole blinking cycle
        self.fast_time = 0.05 # time before moving left/right again when holding down an arrow key
        self.time_before_fast = 0.5
        self.last_move_time = get_time()
        self.last_edit_time = get_time()
        self.time_when_left_or_right_was_newly_pressed = get_time()
        self.time_when_edit_key_was_newly_pressed = get_time()
        self.blinking_line_time = get_time()
        self.last_new_primary_click_time = get_time()
        self.double_click_time = 0.3
        self.double_clicked = False
        self.double_clicked_last_frame = False
        self.blinking_line_wh = [self.text_pixel_size, background_ltwh[3] - 2]
        self.currently_selected = False
        self.currently_highlighting = False
        self.last_key = ''
        self.selected_index = 0
        self.current_string = self.default_value
        self.should_update_spectrum = False
        self.ending_characters = ending_characters
    #
    def deselect_box(self):
        self.currently_selected = False
        self.validate_value()
    #
    def is_valid(self):
        if self.is_a_float and str_can_be_float(self.current_string):
            if self.allowable_range[0] <= float(self.current_string) <= self.allowable_range[1]:
                return True
        if self.is_an_int and str_can_be_int(self.current_string):
            if self.allowable_range[0] <= round(float(self.current_string)) <= self.allowable_range[1]:
                return True
        if self.is_a_hex and str_can_be_hex(self.current_string):
            if self.allowable_range[0] <= switch_to_base10(self.current_string, 16) <= self.allowable_range[1]:
                return True
    #
    def validate_value(self):
        if self.current_string == '':
            self.current_string = self.default_value
            return
        if self.is_a_float: 
            if str_can_be_float(self.current_string):
                self.current_string = str(float(move_number_to_desired_range(self.allowable_range[0], float(self.current_string), self.allowable_range[1])))
                return
            else:
                self.current_string = self.default_value
                return
        if self.is_an_int:
            if str_can_be_int(self.current_string):
                self.current_string = str(round(move_number_to_desired_range(self.allowable_range[0], float(self.current_string), self.allowable_range[1])))
                return
            else:
                self.current_string = self.default_value
                return
        if self.is_a_hex:
            if str_can_be_hex(self.current_string):
                self.current_string = base10_to_hex(round(move_number_to_desired_range(self.allowable_range[0], switch_to_base10(self.current_string, 16), self.allowable_range[1])))
                if self.show_front_zeros:
                    self.current_string = add_characters_to_front_of_string(self.current_string, self.number_of_digits, '0')
                return
            else:
                self.current_string = self.default_value
                return
    #
    def update(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors, offset_x: int = 0, offset_y: int = 0, enabled: bool = True):
        self.should_update_spectrum = False
        self.double_clicked_last_frame = self.double_clicked
        background_ltwh = self._update(screen_instance, gl_context, keys_class_instance, render_instance, cursors, offset_x, offset_y, enabled)
        if not self.currently_selected:
            render_instance.draw_string_of_characters(screen_instance, gl_context, self.current_string + self.ending_characters, [math.floor(background_ltwh[0] + self.text_padding), math.floor(background_ltwh[1] + self.text_padding)], self.text_pixel_size, self.text_color)
        if self.currently_selected:
            start_left, top = [math.floor(background_ltwh[0] + self.text_padding), math.floor(background_ltwh[1] + self.text_padding)]
            small_highlight_index = min(self.highlighted_index_range)
            big_highlight_index  = max(self.highlighted_index_range)
            if small_highlight_index != big_highlight_index:
                string1 = self.current_string[:small_highlight_index] # not highlighted
                string2 = self.current_string[small_highlight_index:big_highlight_index] # highlighted
                string3 = self.current_string[big_highlight_index:] # not highlighted
                string1_width = get_text_width(render_instance, string1, self.text_pixel_size) + self.text_pixel_size
                string2_width = get_text_width(render_instance, string2, self.text_pixel_size) + self.text_pixel_size
                render_instance.draw_string_of_characters(screen_instance, gl_context, string1, [start_left, top], self.text_pixel_size, self.text_color)
                render_instance.basic_rect_ltwh_with_color_to_quad(screen_instance, gl_context, 'black_pixel', [start_left+string1_width-1, background_ltwh[1] + self.text_padding - 1, string2_width-self.text_pixel_size+2, self.text_height + 2], self.highlight_color)
                render_instance.draw_string_of_characters(screen_instance, gl_context, string2, [start_left+string1_width, top], self.text_pixel_size, self.highlighted_text_color)
                render_instance.draw_string_of_characters(screen_instance, gl_context, string3 + self.ending_characters, [start_left+string1_width+string2_width, top], self.text_pixel_size, self.text_color)
            if small_highlight_index == big_highlight_index:
                render_instance.draw_string_of_characters(screen_instance, gl_context, self.current_string + self.ending_characters, [math.floor(background_ltwh[0] + self.text_padding), math.floor(background_ltwh[1] + self.text_padding)], self.text_pixel_size, self.text_color)
            self.draw_blinking_line(screen_instance, gl_context, render_instance, background_ltwh)
    #
    def _update(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors, offset_x: int = 0, offset_y: int = 0, enabled: bool = False):
        background_ltwh = [self.background_ltwh[0] + offset_x, self.background_ltwh[1] + offset_y, self.background_ltwh[2], self.background_ltwh[3]]
        render_instance.basic_rect_ltwh_with_color_to_quad(screen_instance, gl_context, 'black_pixel', background_ltwh, self.background_color)
        cursor_inside_box = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, background_ltwh)
        if not enabled:
            self.deselect_box()
            return background_ltwh
        if cursor_inside_box:
            cursors.add_cursor_this_frame('cursor_i_beam')
        double_clicked = self.update_double_click(keys_class_instance, background_ltwh)
        if double_clicked:
            return background_ltwh
        # not currently selected
        if not self.currently_selected:
            if not keys_class_instance.editor_primary.pressed:
                return background_ltwh
            if not cursor_inside_box:
                return background_ltwh
            if keys_class_instance.editor_primary.newly_pressed:
                self.currently_selected = True
                self.initial_click(render_instance, keys_class_instance, background_ltwh)
            return background_ltwh
        # currently selected
        if self.currently_selected:
            if keys_class_instance.editor_primary.newly_pressed and not cursor_inside_box:
                self.should_update_spectrum = True
                self.deselect_box()
                return background_ltwh
            if keys_class_instance.editor_left.pressed or keys_class_instance.editor_right.pressed:
                self.update_arrow_key_index(keys_class_instance)
                return background_ltwh
            if keys_class_instance.editor_primary.newly_pressed and cursor_inside_box:
                self.initial_click(render_instance, keys_class_instance, background_ltwh)
                return background_ltwh
            if keys_class_instance.editor_primary.pressed and (self.highlighted_index_range[0] != -1) and not self.double_clicked_last_frame:
                self.released_click(render_instance, keys_class_instance, background_ltwh)
                return background_ltwh

            string_before_edit = self.current_string
            index_before_edit = self.selected_index
            self.update_with_typed_key(keys_class_instance)
            if not self.fits(render_instance, background_ltwh, self.current_string):
                self.current_string = string_before_edit
                self.selected_index = index_before_edit
            return background_ltwh
    #
    def get_typed_key(self, keys_class_instance):
        return keys_class_instance.keyboard_key_to_character()
    #
    def update_arrow_key_index(self, keys_class_instance):
        # just arrow key
        if not keys_class_instance.editor_shift.pressed and not keys_class_instance.editor_control.pressed:
            self.stop_highlighting()
            if keys_class_instance.editor_left.newly_pressed:
                self.new_selected_index(self.selected_index - 1)
                self.time_when_left_or_right_was_newly_pressed = get_time()
                return
            if keys_class_instance.editor_right.newly_pressed:
                self.new_selected_index(self.selected_index + 1)
                self.time_when_left_or_right_was_newly_pressed = get_time()
                return
            current_time = get_time()
            if (current_time - self.time_when_left_or_right_was_newly_pressed > self.time_before_fast) and (current_time - self.last_move_time > self.fast_time):
                if keys_class_instance.editor_left.pressed:
                    self.new_selected_index(self.selected_index - 1)
                    return
                if keys_class_instance.editor_right.pressed:
                    self.new_selected_index(self.selected_index + 1)
                    return
        # shift and arrow key
        if keys_class_instance.editor_shift.pressed and not keys_class_instance.editor_control.pressed:
            if keys_class_instance.editor_left.newly_pressed:
                if (self.highlighted_index_range[0] == -1):
                    self.highlighted_index_range[0] = self.selected_index
                self.new_selected_index(self.selected_index - 1)
                self.highlighted_index_range[1] = self.selected_index
                self.update_currently_highlighting()
                self.time_when_left_or_right_was_newly_pressed = get_time()
                return
            if keys_class_instance.editor_right.newly_pressed:
                if (self.highlighted_index_range[0] == -1):
                    self.highlighted_index_range[0] = self.selected_index
                self.new_selected_index(self.selected_index + 1)
                self.highlighted_index_range[1] = self.selected_index
                self.update_currently_highlighting()
                self.time_when_left_or_right_was_newly_pressed = get_time()
                return
            current_time = get_time()
            if (current_time - self.time_when_left_or_right_was_newly_pressed > self.time_before_fast) and (current_time - self.last_move_time > self.fast_time):
                if keys_class_instance.editor_left.pressed:
                    self.new_selected_index(self.selected_index - 1)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                if keys_class_instance.editor_right.pressed:
                    self.new_selected_index(self.selected_index + 1)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
        # control and arrow key
        if not keys_class_instance.editor_shift.pressed and keys_class_instance.editor_control.pressed:
            self.stop_highlighting()
            if keys_class_instance.editor_left.newly_pressed:
                self.time_when_left_or_right_was_newly_pressed = get_time()
                found_desired_character, space_index = self.reverse_iterate_through_string_for_characters()
                if not found_desired_character:
                    self.new_selected_index(0)
                    return
                if space_index == 0:
                    self.new_selected_index(1)
                    return
                self.new_selected_index(space_index+1)
                return
            if keys_class_instance.editor_right.newly_pressed:
                self.time_when_left_or_right_was_newly_pressed = get_time()
                found_desired_character, space_index = self.iterate_through_string_for_character()
                if not found_desired_character:
                    self.new_selected_index(len(self.current_string))
                    return
                if self.selected_index + 1 + space_index == len(self.current_string):
                    self.new_selected_index(len(self.current_string) - 1)
                    return
                self.new_selected_index(self.selected_index+space_index)
                return
            current_time = get_time()
            if (current_time - self.time_when_left_or_right_was_newly_pressed > self.time_before_fast) and (current_time - self.last_move_time > self.fast_time):
                if keys_class_instance.editor_left.pressed:
                    found_desired_character, space_index = self.reverse_iterate_through_string_for_characters()
                    if not found_desired_character:
                        self.new_selected_index(0)
                        return
                    if space_index == 0:
                        self.new_selected_index(1)
                        return
                    self.new_selected_index(space_index+1)
                    return
                if keys_class_instance.editor_right.pressed:
                    found_desired_character, space_index = self.iterate_through_string_for_character()
                    if not found_desired_character:
                        self.new_selected_index(len(self.current_string))
                        return
                    if self.selected_index + 1 + space_index == len(self.current_string):
                        self.new_selected_index(len(self.current_string) - 1)
                        return
                    self.new_selected_index(self.selected_index+space_index)
                    return
        # control and shift and arrow key
        if keys_class_instance.editor_shift.pressed and keys_class_instance.editor_control.pressed:
            if keys_class_instance.editor_left.newly_pressed:
                self.time_when_left_or_right_was_newly_pressed = get_time()
                if (self.highlighted_index_range[0] == -1):
                    self.highlighted_index_range[0] = self.selected_index
                found_desired_character, space_index = self.reverse_iterate_through_string_for_characters()
                if not found_desired_character:
                    self.new_selected_index(0)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                if space_index == 0:
                    self.new_selected_index(1)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                self.new_selected_index(space_index+1)
                self.highlighted_index_range[1] = self.selected_index
                self.update_currently_highlighting()
                return
            if keys_class_instance.editor_right.newly_pressed:
                self.time_when_left_or_right_was_newly_pressed = get_time()
                if (self.highlighted_index_range[0] == -1):
                    self.highlighted_index_range[0] = self.selected_index
                found_desired_character, space_index = self.iterate_through_string_for_character()
                if not found_desired_character:
                    self.new_selected_index(len(self.current_string))
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                if self.selected_index + 1 + space_index == len(self.current_string):
                    self.new_selected_index(len(self.current_string) - 1)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                self.new_selected_index(self.selected_index+space_index)
                self.highlighted_index_range[1] = self.selected_index
                self.update_currently_highlighting()
                return
            current_time = get_time()
            if (current_time - self.time_when_left_or_right_was_newly_pressed > self.time_before_fast) and (current_time - self.last_move_time > self.fast_time):
                if keys_class_instance.editor_left.pressed:
                    if (self.highlighted_index_range[0] == -1):
                        self.highlighted_index_range[0] = self.selected_index
                    found_desired_character, space_index = self.reverse_iterate_through_string_for_characters()
                    if not found_desired_character:
                        self.new_selected_index(0)
                        self.highlighted_index_range[1] = self.selected_index
                        self.update_currently_highlighting()
                        return
                    if space_index == 0:
                        self.new_selected_index(1)
                        self.highlighted_index_range[1] = self.selected_index
                        self.update_currently_highlighting()
                        return
                    self.new_selected_index(space_index+1)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
                if keys_class_instance.editor_right.pressed:
                    found_desired_character, space_index = self.iterate_through_string_for_character()
                    if (self.highlighted_index_range[0] == -1):
                        self.highlighted_index_range[0] = self.selected_index
                    found_desired_character, space_index = self.iterate_through_string_for_character()
                    if not found_desired_character:
                        self.new_selected_index(len(self.current_string))
                        self.highlighted_index_range[1] = self.selected_index
                        self.update_currently_highlighting()
                        return
                    if self.selected_index + 1 + space_index == len(self.current_string):
                        self.new_selected_index(len(self.current_string) - 1)
                        self.highlighted_index_range[1] = self.selected_index
                        self.update_currently_highlighting()
                        return
                    self.new_selected_index(self.selected_index+space_index)
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return
    #
    def draw_blinking_line(self, screen_instance, gl_context, render_instance, background_ltwh):
        currently_blinking = ((get_time() - self.blinking_line_time) % self.blinking_cycle_duration) <= (self.blinking_cycle_duration / 2)
        if not currently_blinking:
            return
        current_left = math.floor(background_ltwh[0] + 1)
        for index, character in enumerate(self.current_string):
            character_width = get_text_width(render_instance, character, self.text_pixel_size)
            if self.selected_index == index:
                render_instance.basic_rect_ltwh_with_color_to_quad(screen_instance, gl_context, 'black_pixel', [current_left, background_ltwh[1] + 1, self.blinking_line_wh[0], self.blinking_line_wh[1]], self.text_color)
                return
            current_left += character_width + self.text_pixel_size
        render_instance.basic_rect_ltwh_with_color_to_quad(screen_instance, gl_context, 'black_pixel', [current_left, background_ltwh[1] + 1, self.blinking_line_wh[0], self.blinking_line_wh[1]], self.text_color)
    #
    def new_selected_index(self, new_value):
        self.last_move_time = get_time()
        self.blinking_line_time = get_time()
        self.selected_index = new_value
        self.selected_index = move_number_to_desired_range(0, self.selected_index, len(self.current_string))
    #
    def fits(self, render_instance, background_ltwh, string):
        if not self.must_fit:
            return True
        text_width = get_text_width(render_instance, string + self.ending_characters, self.text_pixel_size)
        return text_width <= background_ltwh[2] - (2 * self.text_padding)
    #
    def initial_click(self, render_instance, keys_class_instance, background_ltwh):
        self.blinking_line_time = get_time()
        self.highlighted_index_range[0] = self.highlighted_index_range[1] = self.get_cursor_index(render_instance, keys_class_instance, background_ltwh)
        self.new_selected_index(self.highlighted_index_range[1])
        self.update_currently_highlighting()
    #
    def released_click(self, render_instance, keys_class_instance, background_ltwh):
        self.blinking_line_time = get_time()
        self.highlighted_index_range[1] = self.get_cursor_index(render_instance, keys_class_instance, background_ltwh)
        self.new_selected_index(self.highlighted_index_range[1])
        self.update_currently_highlighting()
    #
    def get_cursor_index(self, render_instance, keys_class_instance, background_ltwh):
        current_left = math.floor(background_ltwh[0] + self.text_padding)
        if keys_class_instance.cursor_x_pos.value < current_left:
            return 0
        for index, character in enumerate(self.current_string):
            character_width = get_text_width(render_instance, character, self.text_pixel_size)
            if keys_class_instance.cursor_x_pos.value <= current_left + (character_width / 2):
                return index
            if current_left + (character_width / 2) < keys_class_instance.cursor_x_pos.value <= current_left + character_width:
                return index + 1
            current_left += character_width + self.text_pixel_size
        return len(self.current_string)
    #
    def update_currently_highlighting(self):
        self.currently_highlighting = (self.highlighted_index_range[0] != self.highlighted_index_range[1]) and (self.highlighted_index_range[0] != -1) and (self.highlighted_index_range[1] != -1)
    #
    def stop_highlighting(self):
        self.highlighted_index_range[0] = self.highlighted_index_range[1] = -1
        self.currently_highlighting = False
    #
    def update_with_typed_key(self, keys_class_instance):
        current_key = self.get_typed_key(keys_class_instance)
        if current_key is None:
            self.last_key = ''
            return
        if not (current_key in self.allowable_keys):
            return
        new_press = False
        if current_key != self.last_key:
            new_press = True
            self.time_when_edit_key_was_newly_pressed = get_time()
        self.last_key = current_key
        current_time = get_time()
        editing_this_frame = new_press or ((current_time - self.time_when_edit_key_was_newly_pressed > self.time_before_fast) and (current_time - self.last_edit_time > self.fast_time))
        if not editing_this_frame:
            return
        self.should_update_spectrum = True

        match current_key:
            case 'RETURN':
                self.deselect_box()
                return
            
            case 'DELETE':
                if self.currently_highlighting:
                    self.last_edit_time = get_time()
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    self.current_string = self.current_string[:lower_index] + self.current_string[higher_index:]
                    self.new_selected_index(lower_index)
                    self.stop_highlighting()
                    return
                if self.selected_index == len(self.current_string):
                    self.last_edit_time = get_time()
                    self.new_selected_index(len(self.current_string))
                    return
                if self.selected_index != len(self.current_string):
                    self.last_edit_time = get_time()
                    self.new_selected_index(self.selected_index)
                    self.current_string = self.current_string[:self.selected_index] + self.current_string[self.selected_index + 1:]
                    return

            case 'BACKSPACE':
                if self.currently_highlighting:
                    self.last_edit_time = get_time()
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    self.current_string = self.current_string[:lower_index] + self.current_string[higher_index:]
                    self.new_selected_index(lower_index)
                    self.stop_highlighting()
                    return
                if self.selected_index == 0:
                    self.last_edit_time = get_time()
                    self.new_selected_index(0)
                    return
                if self.selected_index != 0:
                    self.last_edit_time = get_time()
                    self.new_selected_index(self.selected_index - 1)
                    self.current_string = self.current_string[:self.selected_index] + self.current_string[self.selected_index + 1:]
                    return

            case 'UP':
                if self.is_an_int:
                    if not str_can_be_int(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = str(move_number_to_desired_range(self.allowable_range[0], int(self.current_string) + 1, self.allowable_range[1]))
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                    return
                if self.is_a_float:
                    if not str_can_be_float(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = str(move_number_to_desired_range(self.allowable_range[0], float(self.current_string) + 1, self.allowable_range[1]))
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                    return
                if self.is_a_hex:
                    if not str_can_be_hex(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = base10_to_hex(round(move_number_to_desired_range(self.allowable_range[0], switch_to_base10(self.current_string, 16) + 1, self.allowable_range[1])))
                    if self.show_front_zeros:
                        self.current_string = add_characters_to_front_of_string(self.current_string, self.number_of_digits, '0')
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                    return
                return

            case 'DOWN':
                if self.is_an_int:
                    if not str_can_be_int(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = str(move_number_to_desired_range(self.allowable_range[0], int(self.current_string) - 1, self.allowable_range[1]))
                    self.new_selected_index(len(self.current_string))
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                if self.is_a_float:
                    if not str_can_be_float(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = str(move_number_to_desired_range(self.allowable_range[0], float(self.current_string) - 1, self.allowable_range[1]))
                    self.new_selected_index(len(self.current_string))
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                    return
                if self.is_a_hex:
                    if not str_can_be_hex(self.current_string):
                        return
                    self.last_edit_time = get_time()
                    self.current_string = base10_to_hex(round(move_number_to_desired_range(self.allowable_range[0], switch_to_base10(self.current_string, 16) - 1, self.allowable_range[1])))
                    if self.show_front_zeros:
                        self.current_string = add_characters_to_front_of_string(self.current_string, self.number_of_digits, '0')
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = len(self.current_string)
                    self.update_currently_highlighting()
                    self.new_selected_index(len(self.current_string))
                    return
                return

            case 'CTRL_A':
                self.highlighted_index_range[0] = 0
                self.highlighted_index_range[1] = len(self.current_string)
                self.update_currently_highlighting()
                self.new_selected_index(len(self.current_string))
                return

            case 'CTRL_C':
                if not self.currently_highlighting:
                    return
                lower_index = min(self.highlighted_index_range)
                higher_index = max(self.highlighted_index_range)
                keys_class_instance.copy_text(self.current_string[lower_index:higher_index])
                return

            case 'CTRL_V':
                pasted_text = keys_class_instance.paste_text()
                for character in pasted_text:
                    if character not in self.allowable_keys:
                        return
                if not self.currently_highlighting:
                    potential_new_text = self.current_string[:self.selected_index] + pasted_text + self.current_string[self.selected_index:]
                if self.currently_highlighting:
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    potential_new_text = self.current_string[:lower_index] + pasted_text + self.current_string[higher_index:]
                if self.is_a_float:
                    if not str_can_be_float(potential_new_text):
                        return
                    self.current_string = potential_new_text
                    if not self.currently_highlighting:
                        self.new_selected_index(self.selected_index + len(pasted_text))
                    if self.currently_highlighting:
                        self.new_selected_index(lower_index + len(pasted_text))
                        self.stop_highlighting()
                        return
                if self.is_an_int:
                    if not str_can_be_int(potential_new_text):
                        return
                    self.current_string = potential_new_text
                    if not self.currently_highlighting:
                        self.new_selected_index(self.selected_index + len(pasted_text))
                    if self.currently_highlighting:
                        self.new_selected_index(lower_index + len(pasted_text))
                        self.stop_highlighting()
                        return
                if self.is_a_hex:
                    if not str_can_be_hex(potential_new_text):
                        return
                    self.current_string = potential_new_text
                    if not self.currently_highlighting:
                        self.new_selected_index(self.selected_index + len(pasted_text))
                    if self.currently_highlighting:
                        self.new_selected_index(lower_index + len(pasted_text))
                        self.stop_highlighting()
                        return
                return

            case 'CTRL_X':
                if not self.currently_highlighting:
                    return
                lower_index = min(self.highlighted_index_range)
                higher_index = max(self.highlighted_index_range)
                keys_class_instance.copy_text(self.current_string[lower_index:higher_index])
                self.current_string = self.current_string[:lower_index] + self.current_string[higher_index:]
                self.selected_index = lower_index
                self.stop_highlighting()
                return

            case 'CTRL_BACKSPACE':
                if self.currently_highlighting:
                    self.last_edit_time = get_time()
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    self.current_string = self.current_string[:lower_index] + self.current_string[higher_index:]
                    self.new_selected_index(lower_index)
                    self.stop_highlighting()
                    return
                found_desired_character, space_index = self.reverse_iterate_through_string_for_characters()
                if not found_desired_character:
                    self.current_string = self.current_string[self.selected_index:]
                    self.new_selected_index(0)
                    return
                if space_index == 0:
                    self.current_string = ' ' + self.current_string[self.selected_index:]
                    self.new_selected_index(1)
                    return
                self.current_string = self.current_string[:space_index+1] + self.current_string[self.selected_index:]
                self.new_selected_index(space_index+1)

            case 'CTRL_DELETE':
                if self.currently_highlighting:
                    self.last_edit_time = get_time()
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    self.current_string = self.current_string[:lower_index] + self.current_string[higher_index:]
                    self.new_selected_index(lower_index)
                    self.stop_highlighting()
                    return
                found_desired_character, space_index = self.iterate_through_string_for_character()
                if not found_desired_character:
                    self.current_string = self.current_string[:self.selected_index]
                    self.new_selected_index(len(self.current_string))
                    return
                if self.selected_index + 1 + space_index == len(self.current_string):
                    self.current_string = self.current_string[:self.selected_index] + ' '
                    self.new_selected_index(len(self.current_string) - 1)
                    return
                self.current_string = self.current_string[:self.selected_index] + self.current_string[self.selected_index+space_index:]
                self.new_selected_index(self.selected_index)
            
            case _:
                self.last_edit_time = get_time()
                if self.currently_highlighting:
                    lower_index = min(self.highlighted_index_range)
                    higher_index = max(self.highlighted_index_range)
                    self.current_string = self.current_string[:lower_index] + current_key + self.current_string[higher_index:]
                    self.new_selected_index(lower_index + 1)
                    self.stop_highlighting()
                    return
                if not self.currently_highlighting:
                    self.current_string = self.current_string[:self.selected_index] + current_key + self.current_string[self.selected_index:]
                    self.new_selected_index(self.selected_index + 1)
                    return
    #
    def update_double_click(self, keys_class_instance, background_ltwh):
        if keys_class_instance.editor_primary.newly_pressed and point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, background_ltwh):
            current_time = get_time()
            if self.currently_selected:
                self.double_clicked = (current_time - self.last_new_primary_click_time) < self.double_click_time
                self.last_new_primary_click_time = current_time
                if self.double_clicked:
                    self.new_selected_index(len(self.current_string))
                    self.highlighted_index_range[0] = 0
                    self.highlighted_index_range[1] = self.selected_index
                    self.update_currently_highlighting()
                    return True
                return False
            else:
                self.last_new_primary_click_time = current_time
                return False
    #
    def reverse_iterate_through_string_for_characters(self):
        space_index = 0
        found_desired_character = False
        first_loop = True
        for index, character in reversed(list(enumerate(self.current_string[:self.selected_index]))):
            if character in self._STOPPING_CHARACTERS:
                if first_loop:
                    continue
                space_index = index
                found_desired_character = True
                break
            first_loop = False
        return found_desired_character, space_index
    #
    def iterate_through_string_for_character(self):
        space_index = 0
        found_desired_character = False
        first_loop = True
        for index, character in enumerate(self.current_string[self.selected_index:]):
            if character in self._STOPPING_CHARACTERS:
                if first_loop:
                    continue
                space_index = index
                found_desired_character = True
                break
            first_loop = False
        return found_desired_character, space_index


class CurrentlySelectedColor():
    def __init__(self, color, palette_index, base_box_size):
        #
        # input parameters
        self.color = color
        self.color_max_saturation = color
        self.color_min_saturation = color
        self.color_max_alpha = color
        self.color_no_alpha = color
        self.palette_index = palette_index
        self.palette_ltwh = [0, 0, base_box_size, base_box_size]
        #
        # mode of selection; palette/spectrum
        self.selected_through_palette = False
        #
        # palette selection properties
        self.outline1_color = COLORS['YELLOW']
        self.outline1_thickness = 2
        self.outline1_ltwh = [0, 0, base_box_size + (2 * self.outline1_thickness), base_box_size + (2 * self.outline1_thickness)]
        self.outline2_color = COLORS['BLACK']
        self.outline2_thickness = 4
        self.outline2_ltwh = [0, 0, base_box_size + (2 * self.outline2_thickness), base_box_size + (2 * self.outline2_thickness)]
        self.checker_pattern_repeat = 5
        self.checker_color1 = COLORS['GREY']
        self.checker_color2 = COLORS['WHITE']
        #
        # spectrum selection properties
        self.red = 0.0
        self.green = 0.0
        self.blue = 0.0
        self.saturation = 1.0
        self.alpha = 1.0
        self.calculate_color(0.0, 0.0, self.alpha)

    def update_outline_ltwh(self):
        self.outline1_ltwh[0] = self.palette_ltwh[0] - self.outline1_thickness
        self.outline1_ltwh[1] = self.palette_ltwh[1] - self.outline1_thickness
        self.outline2_ltwh[0] = self.palette_ltwh[0] - self.outline2_thickness
        self.outline2_ltwh[1] = self.palette_ltwh[1] - self.outline2_thickness

    def update_colors_with_saturation(self):
        self.color_max_saturation = (self.red, self.green, self.blue, 1.0)
        max_color = max([self.red, self.green, self.blue])
        min_color = min([self.red, self.green, self.blue])
        middle_color = ((max_color - min_color) / 2) + min_color
        adjustment = (middle_color * (1 - self.saturation))
        self.red = (self.red * self.saturation) + adjustment
        self.green = (self.green * self.saturation) + adjustment
        self.blue = (self.blue * self.saturation) + adjustment
        self.color_min_saturation = (middle_color, middle_color, middle_color, 1.0)

    def update_color(self):
        self.color = (self.red, self.green, self.blue, self.alpha)
        self.color_max_alpha = (self.red, self.green, self.blue, 1.0)
        self.color_no_alpha = (self.red, self.green, self.blue, 0.0)

    def calculate_color(self, spectrum_x, spectrum_y, alpha):
        self.alpha = alpha
        # in top half of spectrum
        if 0 <= spectrum_y <= 0.5:
            spectrum_y *= 2
            # section 0 across
            if (0 / 6) <= spectrum_x < (1 / 6):
                spectrum_x = (spectrum_x - (0 / 6)) * 6
                self.red = 1.0
                self.green = 1 - ((1 - spectrum_x) * spectrum_y)
                self.blue = (1 - spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 1 across
            if (1 / 6) <= spectrum_x < (2 / 6):
                spectrum_x = (spectrum_x - (1 / 6)) * 6
                self.red = 1.0 - (spectrum_x * spectrum_y)
                self.green = 1.0
                self.blue = (1 - spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 2 across
            if (2 / 6) <= spectrum_x < (3 / 6):
                spectrum_x = (spectrum_x - (2 / 6)) * 6
                self.red = (1.0 - spectrum_y)
                self.green = 1.0
                self.blue = 1.0 - ((1.0 - spectrum_x) * spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 3 across
            if (3 / 6) <= spectrum_x < (4 / 6):
                spectrum_x = (spectrum_x - (3 / 6)) * 6
                self.red = (1.0 - spectrum_y)
                self.green = 1.0 - (spectrum_x * spectrum_y)
                self.blue = 1.0
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 4 across
            if (4 / 6) <= spectrum_x < (5 / 6):
                spectrum_x = (spectrum_x - (4 / 6)) * 6
                self.red = 1.0 - ((1.0 - spectrum_x) * spectrum_y)
                self.green = (1.0 - spectrum_y)
                self.blue = 1.0
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 5 across
            if (5 / 6) <= spectrum_x <= (6 / 6):
                spectrum_x = (spectrum_x - (5 / 6)) * 6
                self.red = 1.0
                self.green = (1.0 - spectrum_y)
                self.blue = 1.0 - (spectrum_x * spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
        # in bottom half of spectrum
        else:
            spectrum_y = (spectrum_y - 0.5) * 2
            # section 0 across
            if (0 / 6) <= spectrum_x < (1 / 6):
                spectrum_x = (spectrum_x - (0 / 6)) * 6
                self.red = (1.0 - spectrum_y)
                self.green = spectrum_x * (1.0 - spectrum_y)
                self.blue = 0.0
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 1 across
            if (1 / 6) <= spectrum_x < (2 / 6):
                spectrum_x = (spectrum_x - (1 / 6)) * 6
                self.red = (1.0-spectrum_x) * (1.0-spectrum_y)
                self.green = (1.0 - spectrum_y)
                self.blue = 0.0
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 2 across
            if (2 / 6) <= spectrum_x < (3 / 6):
                spectrum_x = (spectrum_x - (2 / 6)) * 6
                self.red = 0.0
                self.green = (1.0 - spectrum_y)
                self.blue = spectrum_x * (1.0 - spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 3 across
            if (3 / 6) <= spectrum_x < (4 / 6):
                spectrum_x = (spectrum_x - (3 / 6)) * 6
                self.red = 0.0
                self.green = (1.0-spectrum_x) * (1.0-spectrum_y)
                self.blue = (1.0 - spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 4 across
            if (4 / 6) <= spectrum_x < (5 / 6):
                spectrum_x = (spectrum_x - (4 / 6)) * 6
                self.red = spectrum_x * (1.0 - spectrum_y)
                self.green = 0.0
                self.blue = (1.0 - spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return
            # section 5 across
            if (5 / 6) <= spectrum_x <= (6 / 6):
                spectrum_x = (spectrum_x - (5 / 6)) * 6
                self.red = (1.0 - spectrum_y)
                self.green = 0.0
                self.blue = (1.0-spectrum_x) * (1.0-spectrum_y)
                self.update_colors_with_saturation()
                self.update_color()
                return

    def rgb_to_hsl(self, rgb: list[float]):
        max_color = max([rgb[0], rgb[1], rgb[2]])
        min_color = min([rgb[0], rgb[1], rgb[2]])
        luminance = (max_color + min_color) / 2
        chroma = max_color - min_color
        if chroma == 0:
            hue = 0
            saturation = 0
        else:
            saturation = chroma / (1 - abs(2 * luminance - 1))
            # red is biggest
            if (rgb[0] >= rgb[1]) and (rgb[0] >= rgb[2]): # red is biggest
                hue = (((rgb[1] - rgb[2]) / chroma) % 6) / 6
            # green is biggest
            if (rgb[1] >= rgb[0]) and (rgb[1] >= rgb[2]):
                hue = ((rgb[2] - rgb[0]) / chroma + 2) / 6
            # blue is biggest
            if (rgb[2] >= rgb[0]) and (rgb[2] >= rgb[1]):
                hue = ((rgb[0] - rgb[1]) / chroma + 4) / 6
        hue = move_number_to_desired_range(0, hue, 1)
        saturation = move_number_to_desired_range(0, saturation, 1)
        luminance = move_number_to_desired_range(0, luminance, 1)
        return [hue, saturation, luminance]


class HeaderManager():
    def __init__(self,
                 render_instance,
                 option_names_and_responses: dict,
                 text_pixel_size: int,
                 padding: int,
                 padding_between_items: int,
                 border_thickness: int,
                 text_color: tuple[int, int, int, int],
                 background_color: tuple[int, int, int, int],
                 highlighted_background_color: tuple[int, int, int, int],
                 edge_color: tuple[int, int, int, int],
                 left: int,
                 top: int):

        self.option_names_and_responses: dict = option_names_and_responses
        self.text_pixel_size: int = text_pixel_size
        self.padding: int = padding
        self.padding_between_items: int = padding_between_items
        self.border_thickness: int = border_thickness
        self.text_color: tuple[int, int, int, int] = text_color
        self.background_color: tuple[int, int, int, int] = background_color
        self.highlighted_background_color: tuple[int, int, int, int] = highlighted_background_color
        self.edge_color: tuple[int, int, int, int] = edge_color
        self.text_height: int = get_text_height(self.text_pixel_size) - (2 * self.text_pixel_size)
        self.box_ltwh: list[int, int, int, int] = [
            left,
            top,
            max([get_text_width(render_instance, key, self.text_pixel_size) for key in self.option_names_and_responses.keys()]) + (2 * self.padding) + (2 * self.border_thickness),
            (len(self.option_names_and_responses) * self.text_height) + ((len(self.option_names_and_responses) - 1) * self.padding_between_items) + (2 * self.border_thickness) + (2 * self.padding)
        ]
        self.options_text_lt = []
        self.options_highlight_ltwh = []
        for index in range(len(self.option_names_and_responses.keys())):
            self.options_text_lt.append([left + self.border_thickness + self.padding, top + self.border_thickness + self.padding + (index * (self.text_height + self.padding_between_items))])
            if index == 0:
                self.options_highlight_ltwh.append([left + self.border_thickness, top + self.border_thickness, self.box_ltwh[2] - (2 * self.border_thickness), (self.padding) + self.text_height + (self.padding_between_items / 2)])
                continue
            if index == len(self.option_names_and_responses.keys()) - 1:
                self.options_highlight_ltwh.append([left + self.border_thickness, top + self.box_ltwh[3] - self.border_thickness - self.padding - self.text_height - (self.padding_between_items / 2), self.box_ltwh[2] - (2 * self.border_thickness), (self.padding_between_items / 2) + self.text_height + (self.padding)])
                continue
            self.options_highlight_ltwh.append([left + self.border_thickness, top + self.border_thickness + self.padding + self.text_height + (self.padding_between_items / 2) + ((index - 1) * (self.padding_between_items + self.text_height)), self.box_ltwh[2] - (2 * self.border_thickness), (self.padding_between_items) + self.text_height])
    #
    def update(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors):
        deselect_headers = not point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.box_ltwh)
        render_instance.draw_rectangle(screen_instance, gl_context, self.box_ltwh, self.border_thickness, self.edge_color, True, self.background_color, True)
        hovered_over_item = False
        for string, option_text_lt, option_highlight_ltwh in zip(self.option_names_and_responses.keys(), self.options_text_lt, self.options_highlight_ltwh):
            hovering_over_item = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, option_highlight_ltwh)
            if hovering_over_item and not hovered_over_item:
                hovered_over_item = True
                render_instance.basic_rect_ltwh_with_color_to_quad(screen_instance, gl_context, 'blank_pixel', option_highlight_ltwh, self.highlighted_background_color)
                if keys_class_instance.editor_primary.newly_pressed:
                    self._execute_response_function_by_name(string)
            render_instance.draw_string_of_characters(screen_instance, gl_context, string, option_text_lt, self.text_pixel_size, self.text_color)
        return deselect_headers
    #
    def _execute_response_function_by_name(self, name):
        self.option_names_and_responses[name]()


class ScrollBar():
    _SCROLL_PARTITIONS = 20

    _UNHIGHLIGHTED = 0
    _CURSOR_OVER_SCROLL_AREA = 1
    _CURSOR_OVER_SCROLL = 2
    _SCROLL_GRABBED = 3

    def __init__(self,
                 scroll_area_lt: list[int, int, int, int],
                 is_vertical: bool,
                 scroll_thickness: int,
                 scroll_length: int,
                 scroll_area_border_thickness: int,
                 scroll_border_thickness: int,
                 border_color: list[float, float, float, float],
                 background_color: list[float, float, float, float],
                 scroll_border_color: list[float, float, float, float],
                 unhighlighted_color: list[float, float, float, float],
                 shaded_color: list[float, float, float, float],
                 highlighted_color: list[float, float, float, float],
                 pixels_scrolled: int = 0):

        self.state: int = 0
        self.is_vertical: bool = is_vertical
        self.scroll_area_border_thickness: int = scroll_area_border_thickness
        self.scroll_border_thickness: int = scroll_border_thickness
        self.pixels_scrolled: int = pixels_scrolled
        self.scroll_percentage: float = 0
        self.grabbed_location: int = 0
        self.grabbed: bool = False
        self.scroll_area_ltwh: list[int, int, int, int] = [scroll_area_lt[0], scroll_area_lt[1], scroll_thickness + (2 * scroll_area_border_thickness), 0] if self.is_vertical else [scroll_area_lt[0], scroll_area_lt[1], 0, scroll_thickness + (2 * scroll_area_border_thickness)]
        self.scroll_ltwh: list[int, int, int, int] = [0, 0, scroll_thickness, scroll_length] if self.is_vertical else [0, 0, scroll_length, scroll_thickness]
        self._update_scroll_ltwh()
        self.border_color = border_color
        self.background_color = background_color
        self.scroll_border_color = scroll_border_color
        self.unhighlighted_color = unhighlighted_color
        self.shaded_color = shaded_color
        self.highlighted_color = highlighted_color
        self.inside_scroll_color = self.unhighlighted_color
        self._coloring_area_border = True if self.scroll_area_border_thickness > 0 else False
        self.mouse_scroll: bool = False
    #
    def update(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors) -> float:
        # check for state changes
        previous_state = self.state
        self._update_state(keys_class_instance)

        # update scroll depending on previous and current state
        update_mouse_scroll = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.scroll_area_ltwh)
        match (previous_state, self.state):
            case (0, 0):  # unhighlighted -> unhighlighted
                pass
            case (0, 1):  # unhighlighted -> cursor over scroll area
                self.inside_scroll_color = self.shaded_color
                update_mouse_scroll = True
            case (0, 2):  # unhighlighted -> cursor over scroll
                self.inside_scroll_color = self.shaded_color
                update_mouse_scroll = True
            case (0, 3):  # unhighlighted -> scroll grabbed
                self.inside_scroll_color = self.highlighted_color
                update_mouse_scroll = False
            case (1, 0):  # cursor over scroll area -> unhighlighted
                self.inside_scroll_color = self.unhighlighted_color
            case (1, 1):  # cursor over scroll area -> cursor over scroll area
                update_mouse_scroll = True
            case (1, 2):  # cursor over scroll area -> cursor over scroll
                update_mouse_scroll = True
            case (1, 3):  # cursor over scroll area -> scroll grabbed
                self.inside_scroll_color = self.highlighted_color
                update_mouse_scroll = False
                if self.is_vertical:
                    self.pixels_scrolled = keys_class_instance.cursor_y_pos.value - self.scroll_area_ltwh[1] - self.scroll_area_border_thickness - (self.scroll_ltwh[3] / 2)
                else:
                    self.pixels_scrolled = keys_class_instance.cursor_x_pos.value - self.scroll_area_ltwh[0] - self.scroll_area_border_thickness - (self.scroll_ltwh[2] / 2)
            case (2, 0):  # cursor over scroll -> unhighlighted
                self.inside_scroll_color = self.unhighlighted_color
            case (2, 1):  # cursor over scroll -> cursor over scroll area
                update_mouse_scroll = True
            case (2, 2):  # cursor over scroll -> cursor over scroll
                update_mouse_scroll = True
            case (2, 3):  # cursor over scroll -> scroll grabbed
                self.inside_scroll_color = self.highlighted_color
                update_mouse_scroll = False
            case (3, 0):  # scroll grabbed -> unhighlighted
                self.inside_scroll_color = self.unhighlighted_color
            case (3, 1):  # scroll grabbed -> cursor over scroll area
                self.inside_scroll_color = self.shaded_color
                update_mouse_scroll = True
            case (3, 2):  # scroll grabbed -> cursor over scroll
                self.inside_scroll_color = self.shaded_color
                update_mouse_scroll = True
            case (3, 3):  # scroll grabbed -> scroll grabbed
                update_mouse_scroll = False
                if self.is_vertical:
                    mouse_last_y = keys_class_instance.cursor_y_pos.last_value
                    mouse_current_y = keys_class_instance.cursor_y_pos.value
                    top_scroll_area = self.scroll_area_ltwh[1] + self.scroll_area_border_thickness
                    bottom_scroll_area = self.scroll_area_ltwh[1] + self.scroll_area_ltwh[3] - self.scroll_area_border_thickness
                    if (mouse_current_y < top_scroll_area):
                        self.pixels_scrolled = 0
                    elif (mouse_current_y > bottom_scroll_area):
                        self.pixels_scrolled = self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3]
                    elif (mouse_last_y < top_scroll_area) and (mouse_current_y >= top_scroll_area):
                        self.pixels_scrolled = mouse_current_y - top_scroll_area
                    elif (mouse_last_y > bottom_scroll_area) and (mouse_current_y <= bottom_scroll_area):
                        self.pixels_scrolled = mouse_current_y - bottom_scroll_area + self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3]
                    else:
                        self.pixels_scrolled += keys_class_instance.cursor_y_pos.delta
                else:
                    mouse_last_x = keys_class_instance.cursor_x_pos.last_value
                    mouse_current_x = keys_class_instance.cursor_x_pos.value
                    left_scroll_area = self.scroll_area_ltwh[0] + self.scroll_area_border_thickness
                    right_scroll_area = self.scroll_area_ltwh[0] + self.scroll_area_ltwh[2] - self.scroll_area_border_thickness
                    if (mouse_current_x < left_scroll_area):
                        self.pixels_scrolled = 0
                    elif (mouse_current_x > right_scroll_area):
                        self.pixels_scrolled = self.scroll_area_ltwh[2] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[2]
                    elif (mouse_last_x < left_scroll_area) and (mouse_current_x >= left_scroll_area):
                        self.pixels_scrolled = mouse_current_x - left_scroll_area
                    elif (mouse_last_x > right_scroll_area) and (mouse_current_x <= right_scroll_area):
                        self.pixels_scrolled = mouse_current_x - right_scroll_area + self.scroll_area_ltwh[2] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[2]
                    else:
                        self.pixels_scrolled += keys_class_instance.cursor_x_pos.delta
        # update the scroll bar position
        if update_mouse_scroll:
            self._update_mouse_scroll(keys_class_instance)
        self._update_scroll_ltwh()
        self._update_scroll_percentage()
        
        # draw the scroll
        render_instance.draw_rectangle(screen_instance, gl_context, self.scroll_area_ltwh, self.scroll_area_border_thickness, self.border_color, self._coloring_area_border, self.background_color, True)
        render_instance.draw_rectangle(screen_instance, gl_context, self.scroll_ltwh, self.scroll_border_thickness, self.scroll_border_color, True, self.inside_scroll_color, True)
    #
    def _update_state(self, keys_class_instance):
        # user continues to grab scroll bar
        if (self.state == ScrollBar._SCROLL_GRABBED) and keys_class_instance.editor_primary.pressed:
            return
        hovered_over_scroll_area = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, get_rect_minus_borders(self.scroll_area_ltwh, self.scroll_area_border_thickness))
        hovered_over_scroll = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.scroll_ltwh)
        # newly grabbing scroll
        if hovered_over_scroll_area and keys_class_instance.editor_primary.newly_pressed:
            self.state = ScrollBar._SCROLL_GRABBED
            return
        # hovering over scroll
        if hovered_over_scroll:
            self.state = ScrollBar._CURSOR_OVER_SCROLL
            return
        # hovering over scroll area
        if hovered_over_scroll_area:
            self.state = ScrollBar._CURSOR_OVER_SCROLL_AREA
            return
        # not hovering over scroll area
        self.state = ScrollBar._UNHIGHLIGHTED
    #
    def _update_mouse_scroll(self, keys_class_instance):
        if self.is_vertical:
            partitions = min(self._SCROLL_PARTITIONS, self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3])
            partition_size = math.ceil((self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3]) / partitions)
            self.pixels_scrolled -= int(partition_size * keys_class_instance.editor_scroll_y.value)
            if keys_class_instance.editor_scroll_y.value == 0:
                self.mouse_scroll = False
            else:
                self.mouse_scroll = True
        else:
            pass
    #
    def _update_scroll_ltwh(self):
        if self.is_vertical:
            self.pixels_scrolled = move_number_to_desired_range(0, self.pixels_scrolled, self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3])
            self.scroll_ltwh[0] = self.scroll_area_ltwh[0] + self.scroll_area_border_thickness
            self.scroll_ltwh[1] = self.scroll_area_ltwh[1] + self.scroll_area_border_thickness + self.pixels_scrolled
        else:
            self.pixels_scrolled = move_number_to_desired_range(0, self.pixels_scrolled, self.scroll_area_ltwh[2] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[2])
            self.scroll_ltwh[0] = self.scroll_area_ltwh[0] + self.scroll_area_border_thickness + self.pixels_scrolled
            self.scroll_ltwh[1] = self.scroll_area_ltwh[1] + self.scroll_area_border_thickness
    #
    def _update_scroll_percentage(self):
        if self.is_vertical:
            self.scroll_percentage = self.pixels_scrolled / (self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3])
        else:
            self.scroll_percentage = self.pixels_scrolled / (self.scroll_area_ltwh[2] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[2])
    #
    def update_pixels_scrolled_with_percentage(self, scroll_percentage: float):
        if self.is_vertical:
            max_scroll = self.scroll_area_ltwh[3] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[3]
        else:
            max_scroll = self.scroll_area_ltwh[2] - (2 * self.scroll_area_border_thickness) - self.scroll_ltwh[2]
        self.pixels_scrolled = int(move_number_to_desired_range(0, max_scroll * scroll_percentage, max_scroll))
        self.scroll_percentage = scroll_percentage


def get_tf_circle(diameter: int):
    tf_circle = []
    radius = (diameter - 0.5) / 2  # smaller than the actual radius for a better looking circle
    center = diameter / 2
    for row in range(diameter):
        row += 0.5
        current_row = []
        for column in range(diameter):
            column += 0.5
            if (column - center) ** 2 + (row - center) ** 2 <= radius ** 2:
                current_row.append(True)
            else:
                current_row.append(False)
        tf_circle.append(current_row)
    return tf_circle


def get_circle_tf_indexes(diameter: int):
    true_indexes = []
    radius = (diameter - 0.5) / 2  # smaller than the actual radius for a better looking circle
    center = diameter / 2
    for row_index, row in enumerate(range(diameter)):
        row += 0.5
        for column_index, column in enumerate(range(diameter)):
            column += 0.5
            if (column - center) ** 2 + (row - center) ** 2 <= radius ** 2:
                true_indexes.append([column_index, row_index])
            else:
                continue
    return true_indexes


def get_perfect_circle_with_edge_angles(diameter: int):
    # get which pixels are part of the circle
    center = diameter / 2
    tf_circle = get_tf_circle(diameter)
    # find edges
    circle = []
    for column_index, column in enumerate(tf_circle):
        current_row = []
        for row_index, draw in enumerate(column):
            if draw:
                if diameter < 4:
                    current_row.append(array('f', [0, 360.0]))
                    continue
                # pixels on the edge of circle
                if ((row_index == 0) or (row_index == len(tf_circle) - 1) or (column_index == 0) or (column_index == len(tf_circle) - 1) or 
                    (not tf_circle[row_index-1][column_index]) or (not tf_circle[row_index+1][column_index]) or (not tf_circle[row_index][column_index-1]) or (not tf_circle[row_index][column_index+1]) or
                    (not tf_circle[row_index-1][column_index-1]) or (not tf_circle[row_index-1][column_index+1]) or (not tf_circle[row_index+1][column_index-1]) or (not tf_circle[row_index+1][column_index+1])):
                    # calculate angle range that is should skip bresenham algorithm
                    angle_from_center = atan2((column_index + 0.5 - center), -(row_index + 0.5 - center))
                    angle_range = array('f', ((angle_from_center - 90) % 360, (angle_from_center + 90) % 360))
                    current_row.append(angle_range)
                    continue
                else:
                    current_row.append(1)
            else:
                current_row.append(0)
        circle.append(current_row)
    return circle


def get_perfect_circle_edge_angles_for_drawing_lines(diameter: int):
    # get which pixels are part of the circle
    center = diameter / 2
    tf_circle = get_tf_circle(diameter)
    # [column_index, row_index, angle, [lower_angle, upper_angle]]
    circle = []
    for column_index, column in enumerate(tf_circle):
        for row_index, draw in enumerate(column):
            if draw:
                if diameter < 4:
                    circle.append([column_index, row_index, atan2((column_index + 0.5 - center), -(row_index + 0.5 - center)), [0.0, 360.0]])
                    continue
                # pixels on the edge of circle
                if ((row_index == 0) or (row_index == len(tf_circle) - 1) or (column_index == 0) or (column_index == len(tf_circle) - 1) or 
                    (not tf_circle[row_index-1][column_index]) or (not tf_circle[row_index+1][column_index]) or (not tf_circle[row_index][column_index-1]) or (not tf_circle[row_index][column_index+1])):
                    # calculate angle range that is should skip bresenham algorithm
                    angle_from_center = atan2((column_index + 0.5 - center), -(row_index + 0.5 - center))
                    angle_range = array('f', ((angle_from_center - 90) % 360, (angle_from_center + 90) % 360))
                    circle.append([column_index, row_index, angle_from_center, [angle_range[0], angle_range[1]]])
                else:
                    continue
            else:
                continue
    return circle


def get_perfect_square_edge_angles_for_drawing_lines(length: int):
    return [[length-1, 0, 45.0, [0.0, 360.0]],
            [0, 0, 135.0, [0.0, 360.0]],
            [length-1, length-1, 225.0, [0.0, 360.0]],
            [0, length-1, 315.0, [0.0, 360.0]]]


def get_square_with_edge_angles(length: int):
    if length == 1:
        return [[array('f', [0.0, 360.0])]]
    center = length / 2
    # get which pixels are part of the circle
    square = []
    for column_index in range(length):
        current_row = []
        for row_index in range(length):
            # pixels on the edge of circle
            if ((row_index == 0) or (row_index == length - 1) or (column_index == 0) or (column_index == length - 1)):
                # calculate angle range that is should skip bresenham algorithm
                angle_from_center = atan2((column_index + 0.5 - center), -(row_index + 0.5 - center))
                # right-side
                if (315.0 < angle_from_center <= 360.0) or (0.0 <= angle_from_center < 45.0):
                    angle_range = array('f', (90.0, 270.0))
                elif angle_from_center == 45.0:
                    angle_range = array('f', [0.0, 360.0])
                # top-side
                elif 45.0 < angle_from_center < 135.0:
                    angle_range = array('f', (180.0, 360.0))
                elif angle_from_center == 135.0:
                    angle_range = array('f', [0.0, 360.0])
                # left-side
                elif 135.0 < angle_from_center < 225.0:
                    angle_range = array('f', (270.0, 90.0))
                elif angle_from_center == 225.0:
                    angle_range = array('f', [0.0, 360.0])
                # bottom-side
                elif 225.0 < angle_from_center < 315.0:
                    angle_range = array('f', (0.0, 180.0))
                elif angle_from_center == 315.0:
                    angle_range = array('f', [0.0, 360.0])
                current_row.append(angle_range)
            else:
                current_row.append(1)
        square.append(current_row)
    return square


def get_perfect_circle_with_edges(diameter: int):
    # get which pixels are part of the circle
    tf_circle = []
    radius = (diameter - 0.5) / 2  # smaller than the actual radius for a better looking circle
    center = diameter / 2
    for row in range(diameter):
        row += 0.5
        current_row = []
        for column in range(diameter):
            column += 0.5
            if (column - center) ** 2 + (row - center) ** 2 <= radius ** 2:
                current_row.append(True)
            else:
                current_row.append(False)
        tf_circle.append(current_row)
    # find edges
    circle = []
    for row_index, row in enumerate(tf_circle):
        current_row = []
        for column_index, draw in enumerate(row):
            if draw:
                if ((row_index == 0) or (row_index == len(tf_circle) - 1) or (column_index == 0) or (column_index == len(tf_circle) - 1) or 
                    (not tf_circle[row_index-1][column_index]) or (not tf_circle[row_index+1][column_index]) or (not tf_circle[row_index][column_index-1]) or (not tf_circle[row_index][column_index+1])):
                    # [left, top, right, bottom]
                    edges = []
                    # left
                    if column_index == 0:
                        edges.append(True)
                    elif not tf_circle[row_index][column_index-1]:
                        edges.append(True)
                    else:
                        edges.append(False)
                    # top
                    if row_index == 0:
                        edges.append(True)
                    elif not tf_circle[row_index-1][column_index]:
                        edges.append(True)
                    else:
                        edges.append(False)
                    # right
                    if column_index == len(tf_circle) - 1:
                        edges.append(True)
                    elif not tf_circle[row_index][column_index+1]:
                        edges.append(True)
                    else:
                        edges.append(False)
                    # bottom
                    if row_index == len(tf_circle) - 1:
                        edges.append(True)
                    elif not tf_circle[row_index+1][column_index]:
                        edges.append(True)
                    else:
                        edges.append(False)
                    current_row.append(edges)
                else:
                    current_row.append(1)
            else:
                current_row.append(0)
        circle.append(current_row)
    return circle


class EditorTool(ABC):
    """Tool base class"""
    STARTING_TOOL_INDEX = 4
    ATTRIBUTE_TEXT_PIXEL_SIZE = 3
    ATTRIBUTE_TEXT_COLOR = COLORS['BLACK']
    _TEXT_BACKGROUND_COLOR = COLORS['LIGHT_GREY']
    _TEXT_COLOR = COLORS['BLACK']
    _TEXT_HIGHLIGHT_COLOR = COLORS['WHITE']
    _HIGHLIGHT_COLOR = COLORS['RED']

    def __init__(self, active: bool):
        self.active: bool = active

    def __str__(self):
        return self.NAME
    
    def __int__(self):
        return self.INDEX


class MarqueeRectangleTool(EditorTool):
    NAME = 'Marquee rectangle'
    INDEX = 0
    def __init__(self, active: bool):
        super().__init__(active)


class LassoTool(EditorTool):
    NAME = 'Lasso'
    INDEX = 1
    def __init__(self, active: bool):
        super().__init__(active)


class PencilTool(EditorTool):
    NAME = 'Pencil'
    INDEX = 2

    _MIN_BRUSH_THICKNESS = 1
    _MAX_BRUSH_THICKNESS = 64
    CIRCLE_REFERENCE = 'pencil_tool_circle'

    BRUSH_THICKNESS = 'Thickness: '

    BRUSH_STYLE = 'Style: '
    CIRCLE_BRUSH = 1
    SQUARE_BRUSH = 2
    _MIN_BRUSH_STYLE = 1
    _MAX_BRUSH_STYLE = 2

    MIN_BRUSH_THICKNESS_TO_FIT_IN_ATTRIBUTE_BOX = 1
    MAX_BRUSH_THICKNESS_TO_FIT_IN_ATTRIBUTE_BOX = 11

    NOT_DRAWING = 0
    DRAWING = 1

    NOT_DRAW_PIXEL = 0
    DRAW_PIXEL = 1

    def __init__(self, active: bool, render_instance, screen_instance, gl_context):
        self.state = PencilTool.NOT_DRAWING  # (NOT_DRAWING = 0, DRAWING = 1)
        self.BRUSH_STYLE_WIDTH = get_text_width(render_instance, PencilTool.BRUSH_STYLE, PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.BRUSH_THICKNESS_WIDTH = get_text_width(render_instance, PencilTool.BRUSH_THICKNESS, PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.brush_style = PencilTool.CIRCLE_BRUSH  # (CIRCLE_BRUSH = 1, SQUARE_BRUSH = 2)
        self._brush_thickness: int = PencilTool._MIN_BRUSH_THICKNESS
        self.circle: list[list[int | list[float, float]]]
        self.update_brush_thickness(render_instance, screen_instance, gl_context, self._brush_thickness)
        self.brush_thickness_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(brush_size) + 'px', PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for brush_size in range(PencilTool._MIN_BRUSH_THICKNESS, PencilTool._MAX_BRUSH_THICKNESS + 1)]) + (2 * PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(PencilTool._MAX_BRUSH_THICKNESS)) - 1) * PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], PencilTool._TEXT_BACKGROUND_COLOR, PencilTool._TEXT_COLOR, PencilTool._TEXT_HIGHLIGHT_COLOR, PencilTool._HIGHLIGHT_COLOR, PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE, PencilTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [PencilTool._MIN_BRUSH_THICKNESS, PencilTool._MAX_BRUSH_THICKNESS], True, False, False, True, len(str(PencilTool._MAX_BRUSH_THICKNESS)), True, str(self.brush_thickness), ending_characters='px')
        self.last_xy: array = array('i', [0, 0])
        super().__init__(active)

    @property
    def brush_thickness(self):
        return self._brush_thickness

    def update_brush_style(self, render_instance, screen_instance, gl_context):
        self.brush_style += 1
        if self.brush_style > PencilTool._MAX_BRUSH_STYLE:
            self.brush_style = PencilTool._MIN_BRUSH_STYLE
        self.update_brush_thickness(render_instance, screen_instance, gl_context, self._brush_thickness)
    
    def update_brush_thickness(self, render_instance, screen_instance, gl_context, brush_thickness: int):
        try:
            render_instance.remove_moderngl_texture_from_renderable_objects_dict(PencilTool.CIRCLE_REFERENCE)
        except:
            pass
        self._brush_thickness = move_number_to_desired_range(PencilTool._MIN_BRUSH_THICKNESS, brush_thickness, PencilTool._MAX_BRUSH_THICKNESS)

        match self.brush_style:
            case PencilTool.CIRCLE_BRUSH:
                self.circle = get_perfect_circle_with_edge_angles(self._brush_thickness)
            case PencilTool.SQUARE_BRUSH:
                self.circle = get_square_with_edge_angles(self._brush_thickness)
        
        pygame_circle_image = pygame.Surface((self.brush_thickness, self.brush_thickness), pygame.SRCALPHA)
        for left, row in enumerate(self.circle):
            for top, draw in enumerate(row):
                if draw:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 255))
                else:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 0))
        render_instance.add_moderngl_texture_with_surface(screen_instance, gl_context, pygame_circle_image, PencilTool.CIRCLE_REFERENCE)

    def brush_thickness_is_valid(self, brush_thickness: Any):
        try:
            int(brush_thickness)
        except:
            return False
        if not (PencilTool._MIN_BRUSH_THICKNESS <= int(brush_thickness) <= PencilTool._MAX_BRUSH_THICKNESS):
            return False
        if int(brush_thickness) == self._brush_thickness:
            return False
        return True


class SprayTool(EditorTool):
    NAME = 'Spray'
    INDEX = 3

    SPRAY_SIZE = 'Size: '
    SPRAY_THICKNESS = 'Drop width: '
    SPRAY_SPEED = 'Speed: '

    _MIN_SPRAY_SIZE = 1
    _MAX_SPRAY_SIZE = 64
    SPRAY_OUTLINE_REFERENCE = 'spray_tool_outline'
    _MIN_SPRAY_THICKNESS = 1
    _MAX_SPRAY_THICKNESS = 64
    _MIN_SPRAY_SPEED = 1
    _MAX_SPRAY_SPEED = 16
    _MIN_SPRAY_TIME = 1  # drops/s
    _MAX_SPRAY_TIME = 1000  # drops/s
    _SPRAY_TIME_INCREMENT = 0.001  # s
    _SPRAY_TIME_ROUND_DIGITS = 3
    MAX_DROPS_PER_FRAME = 24

    NOT_SPRAYING = 0
    SPRAYING = 1

    SPEED_IS_DROPS = 0
    SPEED_IS_TIME = 1
    _MIN_TIME_TYPE = 0
    _MAX_TIME_TYPE = 1

    SPEED_IS_DROPS_ATTRIBUTE_DROP_PADDING = 2
    _SPEED_DROPS_INDEXES = [x for x in range(1, _MAX_SPRAY_SPEED + 1)]
    shuffle(_SPEED_DROPS_INDEXES)
    _SPEED_DROPS_ATTRIBUTE_XY = {'3_2': None, '9_1': None, '13_2': None, '7_4': None, '11_4': None, '1_5': None, '5_6': None, '10_7': None, '2_8': None, '7_9': None, '13_8': None, '1_11': None, '10_11': None, '4_10': None, '6_13': None, '12_13': None}
    for key in _SPEED_DROPS_ATTRIBUTE_XY.keys():
        _SPEED_DROPS_ATTRIBUTE_XY[key] = _SPEED_DROPS_INDEXES.pop()
    SPEED_IS_DROPS_ATTRIBUTE_IMAGE_REFERENCE = 'speed_is_drops_attribute_image'

    DROPS = ' drops'
    DROP = ' drop'

    def __init__(self, active: bool, render_instance, screen_instance, gl_context):
        self.state = SprayTool.NOT_SPRAYING  # (NOT_SPRAYING = 0, SPRAYING = 1)
        # surfaces used while spraying
        self.spray_circle_true_indexes: list[list[int, int]]
        self.drop_thickness_true_indexes: list[list[int, int]]
        # attributes
        self._spray_size: int = SprayTool._MIN_SPRAY_SIZE # width of the spray tool
        self._spray_thickness: int = SprayTool._MIN_SPRAY_THICKNESS  # width of each drop of spray
        self._spray_speed: int = SprayTool._MIN_SPRAY_SPEED  # number of spray drops
        self._spray_time: int = SprayTool._MIN_SPRAY_TIME  # time between drops in seconds
        # tool attribute word width
        self.SPRAY_SIZE_WIDTH = get_text_width(render_instance, SprayTool.SPRAY_SIZE, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.SPRAY_THICKNESS_WIDTH = get_text_width(render_instance, SprayTool.SPRAY_THICKNESS, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.SPRAY_SPEED_WIDTH = get_text_width(render_instance, SprayTool.SPRAY_SPEED, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        # text inputs for attributes
        self.spray_size_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(spray_size) + 'px', SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for spray_size in range(SprayTool._MIN_SPRAY_SIZE, SprayTool._MAX_SPRAY_SIZE + 1)]) + (2 * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(SprayTool._MAX_SPRAY_SIZE)) - 1) * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], SprayTool._TEXT_BACKGROUND_COLOR, SprayTool._TEXT_COLOR, SprayTool._TEXT_HIGHLIGHT_COLOR, SprayTool._HIGHLIGHT_COLOR, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [SprayTool._MIN_SPRAY_SIZE, SprayTool._MAX_SPRAY_SIZE], True, False, False, True, len(str(SprayTool._MAX_SPRAY_SIZE)), True, str(self.spray_size), ending_characters='px')
        self.spray_thickness_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(spray_thickness) + 'px', SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for spray_thickness in range(SprayTool._MIN_SPRAY_THICKNESS, SprayTool._MAX_SPRAY_THICKNESS + 1)]) + (2 * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(SprayTool._MAX_SPRAY_THICKNESS)) - 1) * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], SprayTool._TEXT_BACKGROUND_COLOR, SprayTool._TEXT_COLOR, SprayTool._TEXT_HIGHLIGHT_COLOR, SprayTool._HIGHLIGHT_COLOR, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [SprayTool._MIN_SPRAY_THICKNESS, SprayTool._MAX_SPRAY_THICKNESS], True, False, False, True, len(str(SprayTool._MAX_SPRAY_THICKNESS)), True, str(self.spray_thickness), ending_characters='px')
        speed_text_input_width = max(max([get_text_width(render_instance, str(spray_speed) + SprayTool.DROPS, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for spray_speed in range(SprayTool._MIN_SPRAY_SPEED, SprayTool._MAX_SPRAY_SPEED + 1)]) + (2 * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(SprayTool._MAX_SPRAY_SPEED)) - 1) * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE), max([get_text_width(render_instance, str(brush_size) + ' drops/sec', SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for brush_size in range(SprayTool._MIN_SPRAY_TIME, SprayTool._MAX_SPRAY_TIME + 1)]) + (2 * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(SprayTool._MAX_SPRAY_SPEED)) - 1) * SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE))
        self.spray_speed_text_input = TextInput([0, 0, speed_text_input_width, get_text_height(SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], SprayTool._TEXT_BACKGROUND_COLOR, SprayTool._TEXT_COLOR, SprayTool._TEXT_HIGHLIGHT_COLOR, SprayTool._HIGHLIGHT_COLOR, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [SprayTool._MIN_SPRAY_SPEED, SprayTool._MAX_SPRAY_SPEED], True, False, False, True, len(str(SprayTool._MAX_SPRAY_SPEED)), True, str(self.spray_speed), ending_characters=SprayTool.DROPS)
        self.spray_time_text_input = TextInput([0, 0, speed_text_input_width, get_text_height(SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], SprayTool._TEXT_BACKGROUND_COLOR, SprayTool._TEXT_COLOR,SprayTool._TEXT_HIGHLIGHT_COLOR, SprayTool._HIGHLIGHT_COLOR, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, SprayTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [SprayTool._MIN_SPRAY_TIME, SprayTool._MAX_SPRAY_TIME], True, False, False, True, len(str(SprayTool._MAX_SPRAY_TIME)), True, str(self.spray_time), ending_characters=' drops/sec')
        # update tool attribute values
        self.update_spray_size(SprayTool._MIN_SPRAY_SIZE)
        self.update_spray_thickness(SprayTool._MIN_SPRAY_THICKNESS)
        self.update_spray_speed(SprayTool._MIN_SPRAY_SPEED, render_instance, screen_instance, gl_context)
        self.update_spray_time(SprayTool._MIN_SPRAY_TIME)
        # attributes needed to make 'speed' tool attribute work
        self.speed_type = SprayTool._MIN_TIME_TYPE
        self.outline: list[list[int | list[bool]]]
        self.image_wh: list[int, int] = [0, 0]
        self.last_xy: array = array('i', [-1, -1])
        self.last_frame_time = get_time()
        self.time_since_last_drop = 0
        super().__init__(active)

    @property
    def spray_size(self):
        return self._spray_size

    @property
    def spray_thickness(self):
        return self._spray_thickness

    @property
    def spray_speed(self):
        return self._spray_speed

    @property
    def spray_time(self):
        return self._spray_time

    def spray_size_is_valid(self, spray_size: Any):
        try:
            int(spray_size)
        except:
            return False
        if not (SprayTool._MIN_SPRAY_SIZE <= int(spray_size) <= SprayTool._MAX_SPRAY_SIZE):
            return False
        if int(spray_size) == self._spray_size:
            return False
        return True

    def spray_thickness_is_valid(self, spray_thickness: Any):
        try:
            int(spray_thickness)
        except:
            return False
        if not (SprayTool._MIN_SPRAY_THICKNESS <= int(spray_thickness) <= SprayTool._MAX_SPRAY_THICKNESS):
            return False
        if int(spray_thickness) == self._spray_thickness:
            return False
        return True

    def spray_speed_is_valid(self, spray_speed: Any):
        try:
            int(spray_speed)
        except:
            return False
        if not (SprayTool._MIN_SPRAY_SPEED <= int(spray_speed) <= SprayTool._MAX_SPRAY_SPEED):
            return False
        if int(spray_speed) == self._spray_speed:
            return False
        return True

    def spray_time_is_valid(self, spray_time: Any):
        try:
            int(spray_time)
        except:
            return False
        if not (SprayTool._MIN_SPRAY_TIME <= int(spray_time) <= SprayTool._MAX_SPRAY_TIME):
            return False
        if int(spray_time) == self._spray_time:
            return False
        return True

    def update_spray_size(self, spray_size):
        self._spray_size = int(spray_size)
        self.spray_circle_true_indexes = get_circle_tf_indexes(self._spray_size)

    def update_spray_thickness(self, spray_thickness):
        self._spray_thickness = int(spray_thickness)
        self.drop_thickness_true_indexes = get_circle_tf_indexes(self._spray_thickness)

    def update_spray_speed(self, spray_speed, render_instance, screen_instance, gl_context):
        # update the spray speed
        self._spray_speed = int(spray_speed)
        # update label as drop vs. drops
        if self._spray_speed == 1:
            self.spray_speed_text_input.ending_characters = SprayTool.DROP
        else:
            self.spray_speed_text_input.ending_characters = SprayTool.DROPS
        # update the drops in the image
        try:
            render_instance.remove_moderngl_texture_from_renderable_objects_dict(SprayTool.SPEED_IS_DROPS_ATTRIBUTE_IMAGE_REFERENCE)
        except:
            pass
        pygame_image_wh = render_instance.renderable_objects['tool_attribute_outline'].ORIGINAL_WIDTH - (2 * SprayTool.SPEED_IS_DROPS_ATTRIBUTE_DROP_PADDING)
        pygame_image = pygame.Surface((pygame_image_wh, pygame_image_wh), pygame.SRCALPHA)
        for column in range(pygame_image_wh):
            for row in range(pygame_image_wh):
                if SprayTool._SPEED_DROPS_ATTRIBUTE_XY.get(f"{column}_{row}") is None:
                    continue
                if SprayTool._SPEED_DROPS_ATTRIBUTE_XY[f"{column}_{row}"] > self._spray_speed:
                    continue
                pygame_image.set_at((column, row), (0, 0, 0, 255))
                pygame_image.set_at((column+1, row), (0, 0, 0, 255))
                pygame_image.set_at((column-1, row), (0, 0, 0, 255))
                pygame_image.set_at((column, row+1), (0, 0, 0, 255))
                pygame_image.set_at((column, row-1), (0, 0, 0, 255))
        render_instance.add_moderngl_texture_with_surface(screen_instance, gl_context, pygame_image, SprayTool.SPEED_IS_DROPS_ATTRIBUTE_IMAGE_REFERENCE)

    def update_spray_time(self, spray_time):
        self._spray_time = int(spray_time)
        if self._spray_time == 1:
            self.spray_time_text_input.ending_characters = f"{SprayTool.DROP}/sec"
        else:
            self.spray_time_text_input.ending_characters = f"{SprayTool.DROPS}/sec"

    def update_speed_type(self):
        self.speed_type += 1
        if self.speed_type > SprayTool._MAX_TIME_TYPE:
            self.speed_type = SprayTool._MIN_TIME_TYPE

    def reset_last_xy(self):
        self.last_xy[0] = -1
        self.last_xy[1] = -1


class HandTool(EditorTool):
    NAME = 'Hand'
    INDEX = 4
    def __init__(self, active: bool):
        super().__init__(active)


class BucketTool(EditorTool):
    NAME = 'Bucket'
    INDEX = 5
    def __init__(self, active: bool):
        super().__init__(active)


class LineTool(EditorTool):
    NAME = 'Line'
    INDEX = 6

    _MIN_BRUSH_THICKNESS = 1
    _MAX_BRUSH_THICKNESS = 64
    CIRCLE_REFERENCE = 'line_tool_circle'
    LINE_REFERENCE = 'line_tool_line'

    BRUSH_THICKNESS = 'Thickness: '

    BRUSH_STYLE = 'Style: '
    CIRCLE_BRUSH = 1
    SQUARE_BRUSH = 2
    _MIN_BRUSH_STYLE = 1
    _MAX_BRUSH_STYLE = 2

    MIN_BRUSH_THICKNESS_TO_FIT_IN_ATTRIBUTE_BOX = 1
    MAX_BRUSH_THICKNESS_TO_FIT_IN_ATTRIBUTE_BOX = 11

    NOT_DRAWING = 0
    DRAWING = 1

    NOT_DRAW_PIXEL = 0
    DRAW_PIXEL = 1

    def __init__(self, active: bool, render_instance, screen_instance, gl_context):
        self.state = LineTool.NOT_DRAWING  # (NOT_DRAWING = 0, DRAWING = 1)
        self.BRUSH_STYLE_WIDTH = get_text_width(render_instance, LineTool.BRUSH_STYLE, LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.BRUSH_THICKNESS_WIDTH = get_text_width(render_instance, LineTool.BRUSH_THICKNESS, LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.brush_style = LineTool.CIRCLE_BRUSH  # (CIRCLE_BRUSH = 1, SQUARE_BRUSH = 2)
        self._brush_thickness: int = LineTool._MIN_BRUSH_THICKNESS
        self.circle: list[list[int | list[float, float]]]
        self.circle_for_line_drawing: list[list[int, int, float, list[float, float]]]
        self.update_brush_thickness(render_instance, screen_instance, gl_context, self._brush_thickness)
        self.brush_thickness_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(brush_size) + 'px', LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for brush_size in range(LineTool._MIN_BRUSH_THICKNESS, LineTool._MAX_BRUSH_THICKNESS + 1)]) + (2 * LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(LineTool._MAX_BRUSH_THICKNESS)) - 1) * LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], LineTool._TEXT_BACKGROUND_COLOR, LineTool._TEXT_COLOR, LineTool._TEXT_HIGHLIGHT_COLOR, LineTool._HIGHLIGHT_COLOR, LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE, LineTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [LineTool._MIN_BRUSH_THICKNESS, LineTool._MAX_BRUSH_THICKNESS], True, False, False, True, len(str(LineTool._MAX_BRUSH_THICKNESS)), True, str(self.brush_thickness), ending_characters='px')
        self.start_xy: array = array('i', [0, 0])
        self.start_left_top_xy: array = array('i', [0, 0])
        super().__init__(active)

    @property
    def brush_thickness(self):
        return self._brush_thickness

    def update_brush_style(self, render_instance, screen_instance, gl_context):
        self.brush_style += 1
        if self.brush_style > LineTool._MAX_BRUSH_STYLE:
            self.brush_style = LineTool._MIN_BRUSH_STYLE
        self.update_brush_thickness(render_instance, screen_instance, gl_context, self._brush_thickness)
    
    def update_brush_thickness(self, render_instance, screen_instance, gl_context, brush_thickness: int):
        try:
            render_instance.remove_moderngl_texture_from_renderable_objects_dict(LineTool.CIRCLE_REFERENCE)
        except:
            pass
        self._brush_thickness = move_number_to_desired_range(LineTool._MIN_BRUSH_THICKNESS, brush_thickness, LineTool._MAX_BRUSH_THICKNESS)

        match self.brush_style:
            case LineTool.CIRCLE_BRUSH:
                self.circle = get_perfect_circle_with_edge_angles(self._brush_thickness)
                self.circle_for_line_drawing = get_perfect_circle_edge_angles_for_drawing_lines(self._brush_thickness)
            case LineTool.SQUARE_BRUSH:
                self.circle = get_square_with_edge_angles(self._brush_thickness)
                self.circle_for_line_drawing = get_perfect_square_edge_angles_for_drawing_lines(self._brush_thickness)
        
        pygame_circle_image = pygame.Surface((self.brush_thickness, self.brush_thickness), pygame.SRCALPHA)
        for left, row in enumerate(self.circle):
            for top, draw in enumerate(row):
                if draw:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 255))
                else:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 0))
        render_instance.add_moderngl_texture_with_surface(screen_instance, gl_context, pygame_circle_image, LineTool.CIRCLE_REFERENCE)

    def brush_thickness_is_valid(self, brush_thickness: Any):
        try:
            int(brush_thickness)
        except:
            return False
        if not (LineTool._MIN_BRUSH_THICKNESS <= int(brush_thickness) <= LineTool._MAX_BRUSH_THICKNESS):
            return False
        if int(brush_thickness) == self._brush_thickness:
            return False
        return True
    
    def get_outer_pixels(self, drawing_angle, x1, y1, x2, y2):
        if ((x1 == x2) or (y1 == y2)):
            return (None, None), (None, None)
        above_line_xy = [x1, y1, 0]
        below_line_xy = [x1, y1, 0]
        center_x, center_y = self.brush_thickness / 2, self.brush_thickness / 2
        slope = ((y2 - y1) / (x2 - x1))
        intercept = (slope * -center_x) + center_y
        perpendicular_slope = -(1 / slope)
        for edge_pixel in self.circle_for_line_drawing:
            [column_index, row_index, radial_angle, [lower_angle, upper_angle]] = edge_pixel
            if (not angle_in_range(lower_angle, drawing_angle, upper_angle)) or (self.brush_thickness < 4) or (self.brush_style == LineTool.SQUARE_BRUSH):
                pixel_x = column_index + 0.5
                pixel_y = row_index + 0.5
                perpendicular_intercept = (perpendicular_slope * -pixel_x) + pixel_y
                intersection_x = (perpendicular_intercept - intercept) / (slope - perpendicular_slope)
                intersection_y = (slope * intersection_x) + intercept
                distance_from_line = math.sqrt(((intersection_x - pixel_x) ** 2) + ((intersection_y - pixel_y) ** 2))
                # above line
                if pixel_y > (slope * pixel_x) + intercept:
                    if distance_from_line > above_line_xy[2]:
                        above_line_xy = [column_index, row_index, distance_from_line]
                # below line
                else:
                    if distance_from_line > below_line_xy[2]:
                        below_line_xy = [column_index, row_index, distance_from_line]
        return above_line_xy[0:2], below_line_xy[0:2]


class CurvyLineTool(EditorTool):
    NAME = 'Curvy line'
    INDEX = 7
    def __init__(self, active: bool):
        super().__init__(active)


class RectangleEllipseTool(EditorTool):
    NAME = 'Empty rectangle'
    INDEX = 8

    RECTANGLE_ELLIPSE_REFERENCE = 'rectangle_ellipse'
    RECTANGLE_ELLIPSE_REFERENCE2 = 'rectangle_ellipse2'  # used for hollow ellipses

    NOT_DRAWING = 0
    DRAWING = 1

    BRUSH_THICKNESS = 'Thickness: '

    BRUSH_STYLE = 'Mode: '
    FULL_RECTANGLE = 0
    HOLLOW_RECTANGLE = 1
    FULL_ELLIPSE = 2
    HOLLOW_ELLIPSE = 3
    _MIN_BRUSH_STYLE = 0
    _MAX_BRUSH_STYLE = 3

    _MIN_BRUSH_THICKNESS = 1
    _MAX_BRUSH_THICKNESS = 64

    def __init__(self, active: bool, render_instance, screen_instance, gl_context):
        self.state = RectangleEllipseTool.NOT_DRAWING  # (NOT_DRAWING = 0, DRAWING = 1)
        self.BRUSH_STYLE_WIDTH = get_text_width(render_instance, RectangleEllipseTool.BRUSH_STYLE, RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self.BRUSH_THICKNESS_WIDTH = get_text_width(render_instance, RectangleEllipseTool.BRUSH_THICKNESS, RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        self._brush_thickness: int = RectangleEllipseTool._MIN_BRUSH_THICKNESS
        self.brush_style: int = RectangleEllipseTool.FULL_RECTANGLE
        self.start_xy: array = array('i', [0, 0])
        self.start_left_top_xy: array = array('i', [0, 0])
        self.brush_thickness_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(brush_size) + 'px', RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for brush_size in range(RectangleEllipseTool._MIN_BRUSH_THICKNESS, RectangleEllipseTool._MAX_BRUSH_THICKNESS + 1)]) + (2 * RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(RectangleEllipseTool._MAX_BRUSH_THICKNESS)) - 1) * RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], RectangleEllipseTool._TEXT_BACKGROUND_COLOR, RectangleEllipseTool._TEXT_COLOR, RectangleEllipseTool._TEXT_HIGHLIGHT_COLOR, RectangleEllipseTool._HIGHLIGHT_COLOR, RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE, RectangleEllipseTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [RectangleEllipseTool._MIN_BRUSH_THICKNESS, RectangleEllipseTool._MAX_BRUSH_THICKNESS], True, False, False, True, len(str(RectangleEllipseTool._MAX_BRUSH_THICKNESS)), True, str(self.brush_thickness), ending_characters='px')
        super().__init__(active)

    @property
    def brush_thickness(self):
        return self._brush_thickness

    def update_brush_style(self, render_instance, screen_instance, gl_context):
        self.brush_style += 1
        if self.brush_style > RectangleEllipseTool._MAX_BRUSH_STYLE:
            self.brush_style = RectangleEllipseTool._MIN_BRUSH_STYLE

    def update_brush_thickness(self, brush_thickness: int):
        self._brush_thickness = move_number_to_desired_range(RectangleEllipseTool._MIN_BRUSH_THICKNESS, brush_thickness, RectangleEllipseTool._MAX_BRUSH_THICKNESS)

    def brush_thickness_is_valid(self, brush_thickness: Any):
        try:
            int(brush_thickness)
        except:
            return False
        if not (RectangleEllipseTool._MIN_BRUSH_THICKNESS <= int(brush_thickness) <= RectangleEllipseTool._MAX_BRUSH_THICKNESS):
            return False
        if int(brush_thickness) == self._brush_thickness:
            return False
        return True


class BlurTool(EditorTool):
    NAME = 'Blur'
    INDEX = 9
    def __init__(self, active: bool):
        super().__init__(active)


class JumbleTool(EditorTool):
    NAME = 'Jumble'
    INDEX = 10

    NOT_JUMBLING = 0
    JUMBLING = 1

    JUMBLE_SIZE = 'Size: '

    _MIN_JUMBLE_SIZE = 1
    _MAX_JUMBLE_SIZE = 64

    SPEED_IS_MOVEMENT = 0
    SPEED_IS_TIME = 1
    _MIN_TIME_TYPE = 0
    _MAX_TIME_TYPE = 1

    def __init__(self, active: bool, render_instance, screen_instance, gl_context):
        self.state = JumbleTool.NOT_JUMBLING  # (NOT_JUMBLING = 0, JUMBLING = 1)
        # surfaces used while jumbling
        self.jumble_circle_true_indexes: list[list[int, int]]
        # attributes
        self._jumble_size: int = JumbleTool._MIN_JUMBLE_SIZE  # width of the jumble tool
        # tool attribute word width
        self.JUMBLE_SIZE_WIDTH = get_text_width(render_instance, JumbleTool.JUMBLE_SIZE, JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE)
        # text inputs for attributes
        self.jumble_size_text_input = TextInput([0, 0, max([get_text_width(render_instance, str(jumble_size) + 'px', JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE) for jumble_size in range(JumbleTool._MIN_JUMBLE_SIZE, JumbleTool._MAX_JUMBLE_SIZE + 1)]) + (2 * JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE) + ((len(str(JumbleTool._MAX_JUMBLE_SIZE)) - 1) * JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE), get_text_height(JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE)], JumbleTool._TEXT_BACKGROUND_COLOR, JumbleTool._TEXT_COLOR, JumbleTool._TEXT_HIGHLIGHT_COLOR, JumbleTool._HIGHLIGHT_COLOR, JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE, JumbleTool.ATTRIBUTE_TEXT_PIXEL_SIZE, [JumbleTool._MIN_JUMBLE_SIZE, JumbleTool._MAX_JUMBLE_SIZE], True, False, False, True, len(str(JumbleTool._MAX_JUMBLE_SIZE)), True, str(self.jumble_size), ending_characters='px')
        # update tool attribute values
        self.max_jumble_pixel: int
        self.update_jumble_size(JumbleTool._MIN_JUMBLE_SIZE)
        super().__init__(active)

    @property
    def jumble_size(self):
        return self._jumble_size

    def jumble_size_is_valid(self, jumble_size: Any):
        try:
            int(jumble_size)
        except:
            return False
        if not (JumbleTool._MIN_JUMBLE_SIZE <= int(jumble_size) <= JumbleTool._MAX_JUMBLE_SIZE):
            return False
        if int(jumble_size) == self._jumble_size:
            return False
        return True

    def update_jumble_size(self, jumble_size):
        self._jumble_size = int(jumble_size)
        self.jumble_circle_true_indexes = [tuple(indexes) for indexes in get_circle_tf_indexes(self._jumble_size)]
        self.max_jumble_pixel = len(self.jumble_circle_true_indexes) - 1


class EyedropTool(EditorTool):
    NAME = 'Eyedropper'
    INDEX = 11
    def __init__(self, active: bool):
        super().__init__(active)


class CollisionSelector():
    def __init__(self, Render, text_color, color, text, text_pixel_size, mode, active: bool = False):
        self.active = active  # whether this collision selector is currently selected or not
        self.mode = mode
        self.text_color = text_color
        self.color = color
        self.text = text
        self.text_pixel_size = text_pixel_size
        self.text_height = get_text_height(text_pixel_size) - (2 * text_pixel_size)
        self.text_width = get_text_width(Render, text, text_pixel_size)


class EditorMap():
    TILE_WH = 256
    _STARTING_ZOOM_INDEX = 3
    _ZOOM = [
        # [# of pixels, resulting pixel size]
        # e.g. [2, 1] means 2x2 pixels becomes a 1x1 pixel
        [8, 1],
        [4, 1],
        [2, 1],
        [1, 1],
        [1, 2],
        [1, 4],
        [1, 8],
        [1, 16],
        [1, 32],
        [1, 64],
        [1, 128],
    ]
    _MIN_ZOOM = min([(final / initial) for initial, final in _ZOOM])
    _MAX_ZOOM = max([(final / initial) for initial, final in _ZOOM])
    CIRCLE_OUTLINE_THICKNESS_ZOOMED_IN = 1
    CIRCLE_OUTLINE_THICKNESS_ZOOMED_OUT = 2
    CIRCLE_OUTLINE_REFERENCE = 'editor_circle_outline'
    _MAX_LOAD_TIME = 0.02

    _NOT_HELD = 0
    _HAND_TOOL_HELD = 1
    _EDITOR_HAND_HELD = 2

    MAX_CTRL_Z = 100
    _SAVE_PERIOD = 10  # s

    def __init__(self,
                 PATH: str,
                 screen_instance,
                 gl_context,
                 render_instance,
                 base_path: str):

        self.base_path: str = "C:\\Users\\Kayle\\Desktop\\Blight\\Hamster_Ball_Blight\\Projects\\Project1\\Level1\\"
        self.initial_tile_wh: list[int, int] = list(pygame.image.load(f"{self.base_path}t0_0.png").get_size())
        self.tile_wh: list[int, int] = deepcopy(self.initial_tile_wh)
        # internal
        self.image_space_ltwh: list[int, int, int, int] = [0, 0, 0, 0]
        self.original_map_wh: list[int, int] = [11776, 5888]
        self.map_wh: list[int, int] = deepcopy(self.original_map_wh)
        self.tile_array_shape: list[int, int] = [math.ceil(self.original_map_wh[0] / self.initial_tile_wh[0]), math.ceil(self.original_map_wh[1] / self.initial_tile_wh[1])]
        self.tile_array: list[list[EditorTile]] = []
        self._create_editor_tiles()
        self.pixel_scale: int | float = 1
        self.map_offset_xy: list[int, int] = [0, 0]
        self.tile_offset_xy: list[int, int] = [0, 0]
        self.zoom_levels = len(EditorMap._ZOOM) - 1
        self.zoom_index = EditorMap._STARTING_ZOOM_INDEX
        self.left_tile    = -1
        self.top_tile     = -1
        self.right_tile   = -1
        self.bottom_tile  = -1
        self.loaded_x: list[int] = []
        self.loaded_y: list[int] = []
        self.held: int = 0  # (0 = not held, 1 = held with hand tool, 2 = held with editor hand)
        self.window_resize_last_frame: bool = False
        # tools
        self.tools: list = [
            MarqueeRectangleTool(False),
            LassoTool(False),
            PencilTool(False, render_instance, screen_instance, gl_context),
            SprayTool(False, render_instance, screen_instance, gl_context),
            HandTool(True),
            BucketTool(False),
            LineTool(False, render_instance, screen_instance, gl_context),
            CurvyLineTool(False),
            RectangleEllipseTool(False, render_instance, screen_instance, gl_context),
            BlurTool(False),
            JumbleTool(False, render_instance, screen_instance, gl_context),
            EyedropTool(False)
        ]
        self.current_tool: EditorTool = self.tools[5]
        self.map_edits: list[EditorMap.PixelChange | EditorMap.ObjectChange] = []
        #
        self.stored_draw_keys: list = []
        self.stored_circle_outlines: dict = {}
      
    class PixelChange():
        def __init__(self, new_rgba: array):
            self.change_dict: dict = {}
            self.new_rgba: array = new_rgba

    class ObjectChange():
        def __init__(self, xy, object):
            self.xy: array = array('i', xy)
            self.object = object

    def update(self, api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh: list[int, int, int, int], window_resize: bool, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar, current_tool: tuple[str, int], editor_singleton):
        self._update(api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh, window_resize, horizontal_scroll, vertical_scroll, current_tool, editor_singleton)
        return
        try:
            self._update(api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh, window_resize, horizontal_scroll, vertical_scroll, current_tool, editor_singleton)
        except:
            self._reset_map(render_instance)

    def _update(self, api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh: list[int, int, int, int], window_resize: bool, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar, current_tool: tuple[str, int], editor_singleton):
        # update map area width and height in case screen size has changed
        self.image_space_ltwh = image_space_ltwh

        # get the tool currently being used
        self._update_current_tool(current_tool)

        # update map zoom
        self._zoom(render_instance, keys_class_instance, screen_instance, gl_context, window_resize, horizontal_scroll, vertical_scroll)

        # update map hand
        self._hand(keys_class_instance)

        # update map with scroll bars
        self._update_map_with_scroll_bars(horizontal_scroll, vertical_scroll)

        # ensure the map is within its bounds after movement
        self._move_map_offset_to_bounds(horizontal_scroll, vertical_scroll)

        # calculate which tiles should be loaded and unloaded; perform unloading
        self._update_loaded_tiles(render_instance)

        # perform edits to the map
        self._tool(screen_instance, gl_context, keys_class_instance, render_instance, cursors, editor_singleton)
        
        # iterate through tiles that should be loaded; load them; draw them
        self._iterate_through_tiles(render_instance, screen_instance, gl_context, True, True, editor_singleton)

        # execute stored draws
        self._execute_stored_draws(render_instance, screen_instance, gl_context)

    def _zoom(self, render_instance, keys_class_instance, screen_instance, gl_context, window_resize, horizontal_scroll, vertical_scroll):
        if window_resize:
            self._calculate_zoom(render_instance, keys_class_instance, horizontal_scroll, vertical_scroll)
        elif (keys_class_instance.editor_scroll_y.value == 0):
            return
        elif not point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh):
            return
        else:
            self._calculate_zoom(render_instance, keys_class_instance, horizontal_scroll, vertical_scroll)

    def _calculate_zoom(self, render_instance, keys_class_instance, horizontal_scroll, vertical_scroll):
        original_cursor_x, original_cursor_y = self.get_cursor_position_on_map(keys_class_instance)
        cursor_percent_x = (keys_class_instance.cursor_x_pos.value - self.image_space_ltwh[0]) / self.image_space_ltwh[2]
        cursor_percent_y = (keys_class_instance.cursor_y_pos.value - self.image_space_ltwh[1]) / self.image_space_ltwh[3]

        # find whether a zoom occurred; find what the new zoom is
        zoomed = False
        zoom_reduction = 0
        while not zoomed:
            zoom_index = move_number_to_desired_range(0, self.zoom_index+keys_class_instance.editor_scroll_y.value+zoom_reduction, self.zoom_levels)
            pixel_scale = EditorMap._ZOOM[zoom_index][1] / EditorMap._ZOOM[zoom_index][0]
            zoomed = ((self.original_map_wh[0] * pixel_scale) > self.image_space_ltwh[2]) and ((self.original_map_wh[1] * pixel_scale) > self.image_space_ltwh[3])
            if zoomed and (zoom_index == self.zoom_index):
                return
            zoom_reduction += 1
        if not zoomed:
            return

        # get new pixel scale and zoom
        self.pixel_scale = pixel_scale
        self.zoom_index = zoom_index

        # implement the new zoom
        self.tile_wh[0] = int(self.initial_tile_wh[0] * self.pixel_scale)
        self.tile_wh[1] = int(self.initial_tile_wh[1] * self.pixel_scale)
        # reset map from zoom
        for column in self.loaded_x:
            for row in self.loaded_y:
                self.tile_array[column][row].unload(render_instance)
        self.map_wh[0] = self.original_map_wh[0] * self.pixel_scale
        self.map_wh[1] = self.original_map_wh[1] * self.pixel_scale
        self.loaded_x = []
        self.loaded_y = []

        # update map offset
        self.map_offset_xy[0] = math.ceil((-original_cursor_x * self.pixel_scale) + (cursor_percent_x * self.image_space_ltwh[2]))
        self.map_offset_xy[1] = math.ceil((-original_cursor_y * self.pixel_scale) + (cursor_percent_y * self.image_space_ltwh[3]))
        self._move_map_offset_to_bounds(horizontal_scroll, vertical_scroll)

        # update which tiles are loaded and tile offset
        self.left_tile = -self.map_offset_xy[0] // self.tile_wh[0]
        self.top_tile = -self.map_offset_xy[1] // self.tile_wh[1]
        self.tile_offset_xy[0] = ((self.tile_wh[0] - (self.map_offset_xy[0] % self.tile_wh[0])) % self.tile_wh[0])
        self.tile_offset_xy[1] = ((self.tile_wh[1] - (self.map_offset_xy[1] % self.tile_wh[1])) % self.tile_wh[1])
        self.right_tile = self.left_tile + ((self.image_space_ltwh[2] + self.tile_offset_xy[0]) // self.tile_wh[0])
        self.bottom_tile = self.top_tile + ((self.image_space_ltwh[3] + self.tile_offset_xy[1]) // self.tile_wh[1])
        self.loaded_x = [x for x in range(self.left_tile, self.right_tile + 1)]
        self.loaded_y = [x for x in range(self.top_tile, self.bottom_tile + 1)]

    def _update_loaded_tiles(self, render_instance):
        # left_tile, top_tile, number_of_tiles_across, number_of_tiles_high
        last_left_tile = self.left_tile
        last_top_tile = self.top_tile
        last_right_tile = self.right_tile
        last_bottom_tile = self.bottom_tile
        # update tile data
        self.left_tile = -self.map_offset_xy[0] // self.tile_wh[0]
        self.top_tile = -self.map_offset_xy[1] // self.tile_wh[1]
        self.tile_offset_xy[0] = ((self.tile_wh[0] - (self.map_offset_xy[0] % self.tile_wh[0])) % self.tile_wh[0])
        self.tile_offset_xy[1] = ((self.tile_wh[1] - (self.map_offset_xy[1] % self.tile_wh[1])) % self.tile_wh[1])
        self.right_tile = self.left_tile + ((self.image_space_ltwh[2] + self.tile_offset_xy[0]) // self.tile_wh[0])
        self.bottom_tile = self.top_tile + ((self.image_space_ltwh[3] + self.tile_offset_xy[1]) // self.tile_wh[1])
        # update loaded and unloaded tiles
        load_x, load_y, unload_x, unload_y = [], [], [], []
        change_left_tile = last_left_tile - self.left_tile
        change_right_tile = self.right_tile - last_right_tile
        change_top_tile = last_top_tile - self.top_tile
        change_bottom_tile = self.bottom_tile - last_bottom_tile
        # change in left tiles
        if change_left_tile != 0:
            if change_left_tile > 0:
                load_x += [x for x in range(self.left_tile, last_left_tile)]
            else:
                unload_x += [x for x in range(last_left_tile, self.left_tile)]
        # change in right tiles
        if change_right_tile != 0:
            if change_right_tile > 0:
                load_x += [x for x in range(last_right_tile + 1, self.right_tile + 1)]
            else:
                unload_x += [x for x in range(self.right_tile + 1, last_right_tile + 1)]
        # change in top tiles
        if change_top_tile != 0:
            if change_top_tile > 0:
                load_y += [x for x in range(self.top_tile, last_top_tile)]
            else:
                unload_y += [x for x in range(last_top_tile, self.top_tile)]
        # change in bottom tiles
        if change_bottom_tile != 0:
            if change_bottom_tile > 0:
                load_y += [x for x in range(last_bottom_tile + 1, self.bottom_tile + 1)]
            else:
                unload_y += [x for x in range(self.bottom_tile + 1, last_bottom_tile + 1)]
        # update which tiles are unloaded and perform unloading
        if (unload_x != []):
            for column in unload_x:
                for row in self.loaded_y:
                    self.tile_array[column][row].unload(render_instance)
                self.loaded_x = sorted([tile for tile in self.loaded_x if tile not in unload_x])
        if (unload_y != []):
            for row in unload_y:
                for column in self.loaded_x:
                    self.tile_array[column][row].unload(render_instance)
                self.loaded_y = sorted([tile for tile in self.loaded_y if tile not in unload_y])
        # update which tiles are loaded
        if (load_x != []):
            self.loaded_x += [x for x in load_x if x not in unload_x]
            self.loaded_x = sorted(self.loaded_x)
        if (load_y != []):
            self.loaded_y += [y for y in load_y if y not in unload_y]
            self.loaded_y = sorted(self.loaded_y)

    def _iterate_through_tiles(self, render_instance, screen_instance, gl_context, draw_tiles: bool, load_tiles: bool, editor_singleton):
        # iterate through all loaded tiles
        load = True
        started_loading = False
        left = self.image_space_ltwh[0] - self.tile_offset_xy[0]
        for column in self.loaded_x:
            top = self.image_space_ltwh[1] - self.tile_offset_xy[1]
            for row in self.loaded_y:
                if started_loading:
                    if get_time() - start_load > EditorMap._MAX_LOAD_TIME:
                        load = False
                tile = self.tile_array[column][row]
                loaded = tile.draw_image(render_instance, screen_instance, gl_context, [left, top, self.tile_wh[0], self.tile_wh[1]], editor_singleton.map_mode, load and load_tiles, draw_tiles)
                if loaded and not started_loading:
                    started_loading = True
                    start_load = get_time()
                top += self.tile_wh[1]
            left += self.tile_wh[0]

    def _tool(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors, editor_singleton):
        map_mode = editor_singleton.map_mode  # MapModes (PRETTY or COLLISION)
        current_collision = editor_singleton.collision_selector_mode  # CollisionMode
        match current_collision:
            case CollisionMode.NO_COLLISION:
                current_collision_color = CollisionMode.NO_COLLISION_COLOR
            case CollisionMode.COLLISION:
                current_collision_color = CollisionMode.COLLISION_COLOR
            case CollisionMode.GRAPPLEABLE:
                current_collision_color = CollisionMode.GRAPPLEABLE_COLOR
            case CollisionMode.PLATFORM:
                current_collision_color = CollisionMode.PLATFORM_COLOR
            case CollisionMode.WATER:
                current_collision_color = CollisionMode.WATER_COLOR

        try:
            match int(self.current_tool):
                case MarqueeRectangleTool.INDEX:
                    pass

                case LassoTool.INDEX:
                    pass

                case PencilTool.INDEX:
                    cursor_on_map = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh)
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    ltrb = self._get_ltrb_pixels_on_map()

                    # get the leftest pixel that needs to be drawn
                    pixel_offset_x = 1 - ((self.map_offset_xy[0] / self.pixel_scale) % 1)
                    if pixel_offset_x == 1:
                        pixel_offset_x = 0
                    pixel_offset_x *= self.pixel_scale
                    leftest_pixel = self.image_space_ltwh[0] - pixel_offset_x
                    leftest_brush_pixel = pos_x - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_x = leftest_pixel + ((leftest_brush_pixel - ltrb[0]) * self.pixel_scale)

                    # get the topest pixel that needs to be drawn
                    pixel_offset_y = 1 - ((self.map_offset_xy[1] / self.pixel_scale) % 1)
                    if pixel_offset_y == 1:
                        pixel_offset_y = 0
                    pixel_offset_y *= self.pixel_scale
                    topest_pixel = self.image_space_ltwh[1] - pixel_offset_y
                    topest_brush_pixel = pos_y - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_y = topest_pixel + ((topest_brush_pixel - ltrb[1]) * self.pixel_scale)

                    ltwh = [pixel_x, pixel_y, self.current_tool.brush_thickness * self.pixel_scale, self.current_tool.brush_thickness * self.pixel_scale]

                    # condition if cursor is on the map
                    if cursor_on_map:
                        cursors.add_cursor_this_frame('cursor_big_crosshair')
                        render_instance.store_draw(PencilTool.CIRCLE_REFERENCE, render_instance.basic_rect_ltwh_image_with_color, {'object_name': PencilTool.CIRCLE_REFERENCE, 'ltwh': ltwh, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                        self.stored_draw_keys.append(PencilTool.CIRCLE_REFERENCE)
                    current_color_rgba = percent_to_rgba(editor_singleton.currently_selected_color.color)

                    # change drawing state
                    if (self.current_tool.state == PencilTool.NOT_DRAWING) and keys_class_instance.editor_primary.newly_pressed and cursor_on_map:
                        self.current_tool.state = PencilTool.DRAWING
                        self.map_edits.append(self.PixelChange(new_rgba=current_color_rgba))
                    elif (self.current_tool.state == PencilTool.DRAWING) and keys_class_instance.editor_primary.released:
                        self.current_tool.state = PencilTool.NOT_DRAWING
                    
                    match self.current_tool.state:
                        case PencilTool.NOT_DRAWING:
                            pass
                        case PencilTool.DRAWING:
                            reload_tiles = {}
                            draw_angle = math.degrees(math.atan2(self.current_tool.last_xy[1] - topest_brush_pixel, leftest_brush_pixel - self.current_tool.last_xy[0])) % 360
                            map_edit = self.map_edits[-1].change_dict
                            max_tile_x, max_tile_y = self.tile_array_shape[0] - 1, self.tile_array_shape[1] - 1
                            for brush_offset_x, column in enumerate(self.current_tool.circle):
                                for brush_offset_y, draw in enumerate(column):
                                    if draw == PencilTool.NOT_DRAW_PIXEL:
                                        continue
                                    else:
                                        # draw brush pixels
                                        if (draw == PencilTool.DRAW_PIXEL):
                                            if map_edit.get(tile_name := (edited_pixel_x := leftest_brush_pixel+brush_offset_x, edited_pixel_y := topest_brush_pixel+brush_offset_y)) is None:
                                                # get the tile and pixel being edited
                                                tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                # don't try to draw outside of map bounds
                                                if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                    tile = self.tile_array[tile_x][tile_y]
                                                    # load the tile if it isn't loaded
                                                    if tile.pg_image is None:
                                                        tile.load(render_instance, screen_instance, gl_context)
                                                    reload_tiles[tile.image_reference] = tile
                                                    # make the edit
                                                    original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                    tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                    tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                    # collision map edit
                                                    tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                    # record what was edited for ctrl-Z
                                                    map_edit[tile_name] = original_pixel_color
                                        # draw bresenham pixels
                                        else:
                                            # stamp the point if bresenham isn't needed
                                            if angle_in_range(draw[0], draw_angle, draw[1]):
                                                if map_edit.get(tile_name := (edited_pixel_x := leftest_brush_pixel+brush_offset_x, edited_pixel_y := topest_brush_pixel+brush_offset_y)) is None:
                                                    # get the tile and pixel being edited
                                                    tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                    tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                    # don't try to draw outside of map bounds
                                                    if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                        tile = self.tile_array[tile_x][tile_y]
                                                        # load the tile if it isn't loaded
                                                        if tile.pg_image is None:
                                                            tile.load(render_instance, screen_instance, gl_context)
                                                        reload_tiles[tile.image_reference] = tile
                                                        # make the edit
                                                        original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                        tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                        tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                        # collision map edit
                                                        tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                        # record what was edited for ctrl-Z
                                                        map_edit[tile_name] = original_pixel_color
                                                continue
                                            # draw bresenham points if necessary
                                            for edited_pixel_x, edited_pixel_y in bresenham(self.current_tool.last_xy[0]+brush_offset_x, self.current_tool.last_xy[1]+brush_offset_y, leftest_brush_pixel+brush_offset_x, topest_brush_pixel+brush_offset_y):
                                                if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                                    # get the tile and pixel being edited
                                                    tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                    tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                    # don't try to draw outside of map bounds
                                                    if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                        tile = self.tile_array[tile_x][tile_y]
                                                        # load the tile if it isn't loaded
                                                        if tile.pg_image is None:
                                                            tile.load(render_instance, screen_instance, gl_context)
                                                        reload_tiles[tile.image_reference] = tile
                                                        # make the edit
                                                        original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                        tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                        tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                        # collision map edit
                                                        tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                        # record what was edited for ctrl-Z
                                                        map_edit[tile_name] = original_pixel_color

                            for tile in reload_tiles.values():
                                render_instance.write_pixels_from_pg_surface(tile.image_reference, tile.pg_image)
                                render_instance.write_pixels_from_bytearray(tile.collision_image_reference, tile.collision_bytearray)
                                tile.save()

                    # update values to use next loop
                    self.current_tool.last_xy[0] = leftest_brush_pixel
                    self.current_tool.last_xy[1] = topest_brush_pixel

                case SprayTool.INDEX:
                    cursor_on_map = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh)
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    ltrb = self._get_ltrb_pixels_on_map()
                    circle_outline_thickness = EditorMap.CIRCLE_OUTLINE_THICKNESS_ZOOMED_OUT if EditorMap._ZOOM[self.zoom_index][0] != 1 else EditorMap.CIRCLE_OUTLINE_THICKNESS_ZOOMED_IN

                    if self.current_tool.spray_size % 2 == 0:
                        half_spray_size = self.current_tool.spray_size // 2
                    else:
                        half_spray_size = (self.current_tool.spray_size + 1) // 2
                    # get the leftest pixel that needs to be drawn
                    pixel_offset_x = 1 - ((self.map_offset_xy[0] / self.pixel_scale) % 1)
                    if pixel_offset_x == 1:
                        pixel_offset_x = 0
                    pixel_offset_x *= self.pixel_scale
                    leftest_pixel = self.image_space_ltwh[0] - pixel_offset_x
                    leftest_spray_pixel = pos_x - ((self.current_tool.image_wh[0] - 1) // 2)
                    pixel_x = leftest_pixel + ((leftest_spray_pixel - ltrb[0] - half_spray_size) * self.pixel_scale) - circle_outline_thickness

                    # get the topest pixel that needs to be drawn
                    pixel_offset_y = 1 - ((self.map_offset_xy[1] / self.pixel_scale) % 1)
                    if pixel_offset_y == 1:
                        pixel_offset_y = 0
                    pixel_offset_y *= self.pixel_scale
                    topest_pixel = self.image_space_ltwh[1] - pixel_offset_y
                    topest_spray_pixel = pos_y - ((self.current_tool.image_wh[1] - 1) // 2)
                    pixel_y = topest_pixel + ((topest_spray_pixel - ltrb[1] - half_spray_size) * self.pixel_scale) - circle_outline_thickness

                    ltwh = [pixel_x, pixel_y, int((self.current_tool.spray_size * self.pixel_scale) + (2 * circle_outline_thickness)), int((self.current_tool.spray_size * self.pixel_scale) + (2 * circle_outline_thickness))]

                    # condition if cursor is on the map
                    if cursor_on_map:
                        cursors.add_cursor_this_frame('cursor_big_crosshair')
                        render_instance.store_draw(EditorMap.CIRCLE_OUTLINE_REFERENCE, render_instance.editor_circle_outline, {'ltwh': ltwh, 'circle_size': self.current_tool.spray_size, 'circle_outline_thickness': circle_outline_thickness, 'circle_pixel_size': self.pixel_scale})
                        self.stored_draw_keys.append(EditorMap.CIRCLE_OUTLINE_REFERENCE)
                    current_color_rgba = percent_to_rgba(editor_singleton.currently_selected_color.color)

                    # change drawing state
                    if (self.current_tool.state == SprayTool.NOT_SPRAYING) and keys_class_instance.editor_primary.newly_pressed and cursor_on_map:
                        self.current_tool.reset_last_xy()
                        self.current_tool.state = SprayTool.SPRAYING
                        self.current_tool.last_frame_time = get_time() - ONE_FRAME_AT_60_FPS
                        self.current_tool.time_since_last_drop = (self.current_tool.spray_time ** -1)
                        self.map_edits.append(self.PixelChange(new_rgba=current_color_rgba))
                    elif (self.current_tool.state == SprayTool.SPRAYING) and keys_class_instance.editor_primary.released:
                        self.current_tool.state = SprayTool.NOT_SPRAYING

                    try:
                        match self.current_tool.state:
                            case SprayTool.NOT_SPRAYING:
                                pass
                            case SprayTool.SPRAYING:
                                # don't draw if spraying drops and the cursor hasn't moved
                                if (self.current_tool.speed_type == SprayTool.SPEED_IS_DROPS) and (pos_x == self.current_tool.last_xy[0]) and (pos_y == self.current_tool.last_xy[1]):
                                    raise CaseBreak
                                # setup for spraying
                                reload_tiles = {}
                                map_edit = self.map_edits[-1].change_dict
                                max_tile_x, max_tile_y = self.tile_array_shape[0] - 1, self.tile_array_shape[1] - 1
                                outline_left, outline_top = pos_x - ((self.current_tool.spray_size - 1) // 2), pos_y - ((self.current_tool.spray_size - 1) // 2)
                                # get the number of drops being sprayed this frame
                                match self.current_tool.speed_type:
                                    case SprayTool.SPEED_IS_DROPS:
                                        number_of_drops = self.current_tool.spray_speed
                                    case SprayTool.SPEED_IS_TIME:
                                        current_time = get_time()
                                        elapsed_time_this_frame = current_time - self.current_tool.last_frame_time
                                        self.current_tool.time_since_last_drop += elapsed_time_this_frame
                                        number_of_drops = self.current_tool.spray_time * self.current_tool.time_since_last_drop
                                        drop_remainder = number_of_drops % 1
                                        self.current_tool.time_since_last_drop = (self.current_tool.spray_time ** -1) * drop_remainder
                                        number_of_drops = math.floor(number_of_drops)
                                        number_of_drops = move_number_to_desired_range(0, number_of_drops, SprayTool.MAX_DROPS_PER_FRAME)
                                        self.current_tool.last_frame_time = current_time
                                # pick random indexes to spray
                                for _ in range(number_of_drops):
                                    spray_offset_x, spray_offset_y = choice(self.current_tool.spray_circle_true_indexes)
                                    drop_center_x, drop_center_y = outline_left + spray_offset_x, outline_top + spray_offset_y
                                    drop_left, drop_top = drop_center_x - ((self.current_tool.spray_thickness - 1) // 2), drop_center_y - ((self.current_tool.spray_thickness - 1) // 2)
                                    # get the pixel being drawn
                                    for (drop_offset_x, drop_offset_y) in self.current_tool.drop_thickness_true_indexes:
                                        if map_edit.get(tile_name := (edited_pixel_x := drop_left+drop_offset_x, edited_pixel_y := drop_top+drop_offset_y)) is None:
                                            # get the tile and pixel being edited
                                            tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                            tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                            # don't try to draw outside of map bounds
                                            if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                tile = self.tile_array[tile_x][tile_y]
                                                # load the tile if it isn't loaded
                                                if tile.pg_image is None:
                                                    tile.load(render_instance, screen_instance, gl_context)
                                                reload_tiles[tile.image_reference] = tile
                                                # make the edit
                                                original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                # collision map edit
                                                tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                # record what was edited for ctrl-Z
                                                map_edit[tile_name] = original_pixel_color

                                for tile in reload_tiles.values():
                                    render_instance.write_pixels_from_pg_surface(tile.image_reference, tile.pg_image)
                                    render_instance.write_pixels_from_bytearray(tile.collision_image_reference, tile.collision_bytearray)
                                    tile.save()

                                # update values to use next loop
                                self.current_tool.last_xy[0] = pos_x
                                self.current_tool.last_xy[1] = pos_y
                    except CaseBreak:
                        pass

                case HandTool.INDEX:
                    pass

                case BucketTool.INDEX:
                    pass

                case LineTool.INDEX:
                    cursor_on_map = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh)
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    ltrb = self._get_ltrb_pixels_on_map()

                    # get the leftest pixel that needs to be drawn
                    pixel_offset_x = 1 - ((self.map_offset_xy[0] / self.pixel_scale) % 1)
                    if pixel_offset_x == 1:
                        pixel_offset_x = 0
                    pixel_offset_x *= self.pixel_scale
                    leftest_pixel = self.image_space_ltwh[0] - pixel_offset_x
                    leftest_brush_pixel = pos_x - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_x = leftest_pixel + ((leftest_brush_pixel - ltrb[0]) * self.pixel_scale)

                    # get the topest pixel that needs to be drawn
                    pixel_offset_y = 1 - ((self.map_offset_xy[1] / self.pixel_scale) % 1)
                    if pixel_offset_y == 1:
                        pixel_offset_y = 0
                    pixel_offset_y *= self.pixel_scale
                    topest_pixel = self.image_space_ltwh[1] - pixel_offset_y
                    topest_brush_pixel = pos_y - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_y = topest_pixel + ((topest_brush_pixel - ltrb[1]) * self.pixel_scale)

                    ltwh = [pixel_x, pixel_y, self.current_tool.brush_thickness * self.pixel_scale, self.current_tool.brush_thickness * self.pixel_scale]

                    # condition if cursor is on the map
                    if cursor_on_map:
                        cursors.add_cursor_this_frame('cursor_big_crosshair')
                    current_color_rgba = percent_to_rgba(editor_singleton.currently_selected_color.color)

                    # change drawing state
                    if (self.current_tool.state == LineTool.NOT_DRAWING) and keys_class_instance.editor_primary.newly_pressed and cursor_on_map:
                        self.current_tool.state = LineTool.DRAWING
                        self.current_tool.start_xy[0] = pos_x
                        self.current_tool.start_xy[1] = pos_y
                        self.current_tool.start_left_top_xy[0] = leftest_brush_pixel
                        self.current_tool.start_left_top_xy[1] = topest_brush_pixel
                        self.map_edits.append(self.PixelChange(new_rgba=current_color_rgba))
                    elif (self.current_tool.state == LineTool.DRAWING) and keys_class_instance.editor_primary.released:
                        self.current_tool.state = LineTool.NOT_DRAWING
                        # draw the line on the map
                        reload_tiles = {}
                        draw_angle = math.degrees(math.atan2(self.current_tool.start_left_top_xy[1] - topest_brush_pixel, leftest_brush_pixel - self.current_tool.start_left_top_xy[0])) % 360
                        map_edit = self.map_edits[-1].change_dict
                        max_tile_x, max_tile_y = self.tile_array_shape[0] - 1, self.tile_array_shape[1] - 1
                        # # get points used to draw lines in the fragment shader to make the drawn points match
                        # x2 = int(pixel_x + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                        # y2 = int(pixel_y + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                        # x1 = int(x2 + ((self.current_tool.start_xy[0] - pos_x) * self.pixel_scale))
                        # y1 = int(y2 + ((self.current_tool.start_xy[1] - pos_y) * self.pixel_scale))
                        # (stamp1_below_line_x, stamp1_below_line_y), (stamp1_above_line_x, stamp1_above_line_y) = self.current_tool.get_outer_pixels(draw_angle, x1, y1, x2, y2)
                        # valid_slope = all(map(lambda x: x is not None, [stamp1_below_line_x, stamp1_below_line_y, stamp1_above_line_x, stamp1_above_line_y]))
                        # if valid_slope:
                        #     difference_x = leftest_brush_pixel-self.current_tool.start_left_top_xy[0]
                        #     difference_y = topest_brush_pixel-self.current_tool.start_left_top_xy[1]
                        #     (stamp2_above_line_x, stamp2_above_line_y), (stamp2_below_line_x, stamp2_below_line_y) = (stamp1_above_line_x+difference_x, stamp1_above_line_y+difference_y), (stamp1_below_line_x+difference_x, stamp1_below_line_y+difference_y)
                        #     delta_y = stamp1_above_line_y - stamp1_below_line_y
                        #     delta_x = stamp1_above_line_x - stamp1_below_line_x
                        #     stamp_slope = delta_y / delta_x if delta_x != 0 else 99999999
                        #     print(stamp_slope)
                        for brush_offset_x, column in enumerate(self.current_tool.circle):
                            for brush_offset_y, draw in enumerate(column):
                                if draw == LineTool.NOT_DRAW_PIXEL:
                                    continue
                                else:
                                    # draw brush pixels
                                    if (draw == LineTool.DRAW_PIXEL):
                                        for edited_pixel_x, edited_pixel_y in [(self.current_tool.start_left_top_xy[0]+brush_offset_x, self.current_tool.start_left_top_xy[1]+brush_offset_y), (leftest_brush_pixel+brush_offset_x, topest_brush_pixel+brush_offset_y)]:
                                            if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                                # get the tile and pixel being edited
                                                tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                # don't try to draw outside of map bounds
                                                if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                    tile = self.tile_array[tile_x][tile_y]
                                                    # load the tile if it isn't loaded
                                                    if tile.pg_image is None:
                                                        tile.load(render_instance, screen_instance, gl_context)
                                                    reload_tiles[tile.image_reference] = tile
                                                    # make the edit
                                                    original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                    tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                    tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                    # collision map edit
                                                    tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                    # record what was edited for ctrl-Z
                                                    map_edit[tile_name] = original_pixel_color
                                    # draw bresenham pixels
                                    else:
                                        # stamp the point if bresenham isn't needed
                                        if angle_in_range(draw[0], draw_angle, draw[1]):
                                            # point should be stamped on the starting and ending stamps
                                            for edited_pixel_x, edited_pixel_y in [(self.current_tool.start_left_top_xy[0]+brush_offset_x, self.current_tool.start_left_top_xy[1]+brush_offset_y), (leftest_brush_pixel+brush_offset_x, topest_brush_pixel+brush_offset_y)]:
                                                if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                                    # get the tile and pixel being edited
                                                    tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                    tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                    # don't try to draw outside of map bounds
                                                    if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                        tile = self.tile_array[tile_x][tile_y]
                                                        # load the tile if it isn't loaded
                                                        if tile.pg_image is None:
                                                            tile.load(render_instance, screen_instance, gl_context)
                                                        reload_tiles[tile.image_reference] = tile
                                                        # make the edit
                                                        original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                        tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                        tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                        # collision map edit
                                                        tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                        # record what was edited for ctrl-Z
                                                        map_edit[tile_name] = original_pixel_color
                                            continue
                                        # draw bresenham points if necessary
                                        for edited_pixel_x, edited_pixel_y in bresenham(self.current_tool.start_left_top_xy[0]+brush_offset_x, self.current_tool.start_left_top_xy[1]+brush_offset_y, leftest_brush_pixel+brush_offset_x, topest_brush_pixel+brush_offset_y):
                                            if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                                # get the tile and pixel being edited
                                                tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                # don't try to draw outside of map bounds
                                                if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                    tile = self.tile_array[tile_x][tile_y]
                                                    # load the tile if it isn't loaded
                                                    if tile.pg_image is None:
                                                        tile.load(render_instance, screen_instance, gl_context)
                                                    reload_tiles[tile.image_reference] = tile
                                                    # make the edit
                                                    original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                    tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                    tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                    # collision map edit
                                                    tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                    # record what was edited for ctrl-Z
                                                    map_edit[tile_name] = original_pixel_color

                        for tile in reload_tiles.values():
                            render_instance.write_pixels_from_pg_surface(tile.image_reference, tile.pg_image)
                            render_instance.write_pixels_from_bytearray(tile.collision_image_reference, tile.collision_bytearray)
                            tile.save()

                    match self.current_tool.state:
                        case LineTool.NOT_DRAWING:
                            render_instance.store_draw(LineTool.CIRCLE_REFERENCE, render_instance.basic_rect_ltwh_image_with_color, {'object_name': LineTool.CIRCLE_REFERENCE, 'ltwh': ltwh, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                            self.stored_draw_keys.append(LineTool.CIRCLE_REFERENCE)
                        case LineTool.DRAWING:
                            reload_tiles = {}
                            x2 = int(pixel_x + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                            y2 = int(pixel_y + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                            x1 = int(x2 + ((self.current_tool.start_xy[0] - pos_x) * self.pixel_scale))
                            y1 = int(y2 + ((self.current_tool.start_xy[1] - pos_y) * self.pixel_scale))
                            render_instance.store_draw(LineTool.LINE_REFERENCE, render_instance.draw_line, {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'thickness': self.current_tool.brush_thickness, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color, 'pixel_size': self.pixel_scale, 'circle_for_line_drawing': self.current_tool.circle_for_line_drawing, 'brush_style': self.current_tool.brush_style})
                            self.stored_draw_keys.append(LineTool.LINE_REFERENCE)

                case CurvyLineTool.INDEX:
                    pass

                case RectangleEllipseTool.INDEX:
                    cursor_on_map = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh)
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    ltrb = self._get_ltrb_pixels_on_map()

                    # get the leftest pixel that needs to be drawn
                    pixel_offset_x = 1 - ((self.map_offset_xy[0] / self.pixel_scale) % 1)
                    if pixel_offset_x == 1:
                        pixel_offset_x = 0
                    pixel_offset_x *= self.pixel_scale
                    leftest_pixel = self.image_space_ltwh[0] - pixel_offset_x
                    leftest_brush_pixel = pos_x - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_x = leftest_pixel + ((leftest_brush_pixel - ltrb[0]) * self.pixel_scale)

                    # get the topest pixel that needs to be drawn
                    pixel_offset_y = 1 - ((self.map_offset_xy[1] / self.pixel_scale) % 1)
                    if pixel_offset_y == 1:
                        pixel_offset_y = 0
                    pixel_offset_y *= self.pixel_scale
                    topest_pixel = self.image_space_ltwh[1] - pixel_offset_y
                    topest_brush_pixel = pos_y - ((self.current_tool.brush_thickness - 1) // 2)
                    pixel_y = topest_pixel + ((topest_brush_pixel - ltrb[1]) * self.pixel_scale)

                    ltwh = [pixel_x, pixel_y, self.current_tool.brush_thickness * self.pixel_scale, self.current_tool.brush_thickness * self.pixel_scale]

                    # condition if cursor is on the map
                    if cursor_on_map:
                        cursors.add_cursor_this_frame('cursor_big_crosshair')
                    current_color_rgba = percent_to_rgba(editor_singleton.currently_selected_color.color)

                    # change drawing state
                    if (self.current_tool.state == RectangleEllipseTool.NOT_DRAWING) and keys_class_instance.editor_primary.newly_pressed and cursor_on_map:
                        self.current_tool.state = RectangleEllipseTool.DRAWING
                        self.current_tool.start_xy[0] = pos_x
                        self.current_tool.start_xy[1] = pos_y
                        self.current_tool.start_left_top_xy[0] = leftest_brush_pixel
                        self.current_tool.start_left_top_xy[1] = topest_brush_pixel
                        self.map_edits.append(self.PixelChange(new_rgba=current_color_rgba))
                    elif (self.current_tool.state == RectangleEllipseTool.DRAWING) and keys_class_instance.editor_primary.released:
                        self.current_tool.state = RectangleEllipseTool.NOT_DRAWING
                        reload_tiles = {}
                        map_edit = self.map_edits[-1].change_dict
                        max_tile_x, max_tile_y = self.tile_array_shape[0] - 1, self.tile_array_shape[1] - 1

                        # execute draws
                        x1 = min(self.current_tool.start_left_top_xy[0], leftest_brush_pixel)
                        y1 = min(self.current_tool.start_left_top_xy[1], topest_brush_pixel)
                        x2 = max(self.current_tool.start_left_top_xy[0], leftest_brush_pixel) + self.current_tool.brush_thickness - 1
                        y2 = max(self.current_tool.start_left_top_xy[1], topest_brush_pixel) + self.current_tool.brush_thickness - 1
                        match self.current_tool.brush_style:
                            case RectangleEllipseTool.FULL_RECTANGLE:
                                for edited_pixel_x in range(x1, x2 + 1):
                                    for edited_pixel_y in range(y1, y2 + 1):
                                        if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                            # get the tile and pixel being edited
                                            tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                            tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                            # don't try to draw outside of map bounds
                                            if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                tile = self.tile_array[tile_x][tile_y]
                                                # load the tile if it isn't loaded
                                                if tile.pg_image is None:
                                                    tile.load(render_instance, screen_instance, gl_context)
                                                reload_tiles[tile.image_reference] = tile
                                                # make the edit
                                                original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                # collision map edit
                                                tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                # record what was edited for ctrl-Z
                                                map_edit[tile_name] = original_pixel_color
                            case RectangleEllipseTool.HOLLOW_RECTANGLE:
                                for edited_pixel_x in range(x1, x2 + 1):
                                    for edited_pixel_y in range(y1, y2 + 1):
                                        if (x1 + self.current_tool.brush_thickness <= edited_pixel_x <= x2 - self.current_tool.brush_thickness) and (y1 + self.current_tool.brush_thickness <= edited_pixel_y <= y2 - self.current_tool.brush_thickness):
                                            continue
                                        if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                            # get the tile and pixel being edited
                                            tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                            tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                            # don't try to draw outside of map bounds
                                            if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                tile = self.tile_array[tile_x][tile_y]
                                                # load the tile if it isn't loaded
                                                if tile.pg_image is None:
                                                    tile.load(render_instance, screen_instance, gl_context)
                                                reload_tiles[tile.image_reference] = tile
                                                # make the edit
                                                original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                # collision map edit
                                                tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                # record what was edited for ctrl-Z
                                                map_edit[tile_name] = original_pixel_color
                            case RectangleEllipseTool.FULL_ELLIPSE:
                                ellipse_center_x = (x1 + x2 + 1) / 2
                                ellipse_center_y = (y1 + y2 + 1) / 2
                                ellipse_radius_x = (abs(x1 - x2) + 1) / 2
                                ellipse_radius_y = (abs(y1 - y2) + 1) / 2
                                for edited_pixel_x in range(x1, x2 + 1):
                                    for edited_pixel_y in range(y1, y2 + 1):
                                        x_inside_ellipse = ((edited_pixel_x + 0.5 - ellipse_center_x) ** 2) / (ellipse_radius_x ** 2)
                                        y_inside_ellipse = ((edited_pixel_y + 0.5 - ellipse_center_y) ** 2) / (ellipse_radius_y ** 2)
                                        if (x_inside_ellipse + y_inside_ellipse <= 1):
                                            if map_edit.get(tile_name := (edited_pixel_x, edited_pixel_y)) is None:
                                                # get the tile and pixel being edited
                                                tile_x, pixel_x = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                                tile_y, pixel_y = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                                # don't try to draw outside of map bounds
                                                if (0 <= tile_x <= max_tile_x) and (0 <= tile_y <= max_tile_y):
                                                    tile = self.tile_array[tile_x][tile_y]
                                                    # load the tile if it isn't loaded
                                                    if tile.pg_image is None:
                                                        tile.load(render_instance, screen_instance, gl_context)
                                                    reload_tiles[tile.image_reference] = tile
                                                    # make the edit
                                                    original_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                                                    tile.pg_image.set_at((pixel_x, pixel_y), resulting_color := get_blended_color_int(original_pixel_color, current_color_rgba))
                                                    tile.edits[(pixel_x, pixel_y)] = resulting_color
                                                    # collision map edit
                                                    tile.collision_bytearray[(pixel_y * EditorMap.TILE_WH) + pixel_x] = current_collision
                                                    # record what was edited for ctrl-Z
                                                    map_edit[tile_name] = original_pixel_color
                            case RectangleEllipseTool.HOLLOW_ELLIPSE:
                                pass

                        for tile in reload_tiles.values():
                            render_instance.write_pixels_from_pg_surface(tile.image_reference, tile.pg_image)
                            render_instance.write_pixels_from_bytearray(tile.collision_image_reference, tile.collision_bytearray)
                            tile.save()

                    match self.current_tool.state:
                        # shader on the map when not actively drawing
                        case RectangleEllipseTool.NOT_DRAWING:
                            if cursor_on_map:
                                match self.current_tool.brush_style:
                                    case RectangleEllipseTool.FULL_RECTANGLE:
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.basic_rect_ltwh_image_with_color, {'object_name': 'black_pixel', 'ltwh': ltwh, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.HOLLOW_RECTANGLE:
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.basic_rect_ltwh_image_with_color, {'object_name': 'black_pixel', 'ltwh': ltwh, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.FULL_ELLIPSE:
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.draw_ellipse, {'ltwh': [round(dimension) for dimension in ltwh], 'ellipse_wh': [round(ltwh[2] / self.pixel_scale), round(ltwh[2] / self.pixel_scale)], 'pixel_size': self.pixel_scale, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.HOLLOW_ELLIPSE:
                                        pass
                        # shader showing how map will look once draw is released
                        case RectangleEllipseTool.DRAWING:
                            # draw accordng to brush style
                            if cursor_on_map:
                                x2 = int(pixel_x + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                                y2 = int(pixel_y + (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale))
                                x1 = int(x2 + ((self.current_tool.start_xy[0] - pos_x) * self.pixel_scale))
                                y1 = int(y2 + ((self.current_tool.start_xy[1] - pos_y) * self.pixel_scale))
                                rectangle_ellipse_ltwh = [round(min(x1, x2) - (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale)), round(min(y1, y2) - (((self.current_tool.brush_thickness - 1) // 2) * self.pixel_scale)), round(abs(x1 - x2) + (self.current_tool.brush_thickness * self.pixel_scale)), round(abs(y1 - y2) + (self.current_tool.brush_thickness * self.pixel_scale))]
                                match self.current_tool.brush_style:
                                    case RectangleEllipseTool.FULL_RECTANGLE:
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.basic_rect_ltwh_image_with_color, {'object_name': 'black_pixel', 'ltwh': rectangle_ellipse_ltwh, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.HOLLOW_RECTANGLE:
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.draw_rectangle, {'ltwh': rectangle_ellipse_ltwh, 'border_thickness': round(self.current_tool.brush_thickness * self.pixel_scale), 'border_color': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color, 'coloring_border': True, 'inner_color': COLORS['WHITE'], 'coloring_inside': False})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.FULL_ELLIPSE:
                                        x1 = min(self.current_tool.start_left_top_xy[0], leftest_brush_pixel)
                                        y1 = min(self.current_tool.start_left_top_xy[1], topest_brush_pixel)
                                        x2 = max(self.current_tool.start_left_top_xy[0], leftest_brush_pixel) + self.current_tool.brush_thickness - 1
                                        y2 = max(self.current_tool.start_left_top_xy[1], topest_brush_pixel) + self.current_tool.brush_thickness - 1
                                        ellipse_wh = [abs(x1 - x2) + 1, abs(y1 - y2) + 1]
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.draw_ellipse, {'ltwh': rectangle_ellipse_ltwh, 'ellipse_wh': ellipse_wh, 'pixel_size': self.pixel_scale, 'rgba': editor_singleton.currently_selected_color.color if map_mode is MapModes.PRETTY else current_collision_color})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)
                                    case RectangleEllipseTool.HOLLOW_ELLIPSE:
                                        x1 = min(self.current_tool.start_left_top_xy[0], leftest_brush_pixel)
                                        y1 = min(self.current_tool.start_left_top_xy[1], topest_brush_pixel)
                                        x2 = max(self.current_tool.start_left_top_xy[0], leftest_brush_pixel) + self.current_tool.brush_thickness - 1
                                        y2 = max(self.current_tool.start_left_top_xy[1], topest_brush_pixel) + self.current_tool.brush_thickness - 1
                                        ellipse_wh = [abs(x1 - x2) + 1, abs(y1 - y2) + 1]
                                        render_instance.store_draw(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE, render_instance.draw_hollow_ellipse, {'ltwh': rectangle_ellipse_ltwh, 'ellipse_wh': ellipse_wh, 'pixel_size': self.pixel_scale, 'ellipse_thickness': self.current_tool.brush_thickness, 'rgba': rgba_to_glsl(current_color_rgba)})
                                        self.stored_draw_keys.append(RectangleEllipseTool.RECTANGLE_ELLIPSE_REFERENCE)

                case BlurTool.INDEX:
                    pass

                case JumbleTool.INDEX:
                    cursor_on_map = point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh)
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    ltrb = self._get_ltrb_pixels_on_map()
                    circle_outline_thickness = EditorMap.CIRCLE_OUTLINE_THICKNESS_ZOOMED_OUT if EditorMap._ZOOM[self.zoom_index][0] != 1 else EditorMap.CIRCLE_OUTLINE_THICKNESS_ZOOMED_IN

                    if self.current_tool.jumble_size % 2 == 0:
                        half_jumble_size = self.current_tool.jumble_size // 2
                    else:
                        half_jumble_size = (self.current_tool.jumble_size + 1) // 2
                    # get the leftest pixel that needs to be drawn
                    pixel_offset_x = 1 - ((self.map_offset_xy[0] / self.pixel_scale) % 1)
                    if pixel_offset_x == 1:
                        pixel_offset_x = 0
                    pixel_offset_x *= self.pixel_scale
                    leftest_pixel = self.image_space_ltwh[0] - pixel_offset_x
                    leftest_jumble_pixel = pos_x - ((self.current_tool.jumble_size - 1) // 2)
                    pixel_x = leftest_pixel + ((pos_x + 1 - ltrb[0] - half_jumble_size) * self.pixel_scale) - circle_outline_thickness

                    # get the topest pixel that needs to be drawn
                    pixel_offset_y = 1 - ((self.map_offset_xy[1] / self.pixel_scale) % 1)
                    if pixel_offset_y == 1:
                        pixel_offset_y = 0
                    pixel_offset_y *= self.pixel_scale
                    topest_pixel = self.image_space_ltwh[1] - pixel_offset_y
                    topest_jumble_pixel = pos_y - ((self.current_tool.jumble_size - 1) // 2)
                    pixel_y = topest_pixel + ((pos_y + 1 - ltrb[1] - half_jumble_size) * self.pixel_scale) - circle_outline_thickness

                    ltwh = [pixel_x, pixel_y, int((self.current_tool.jumble_size * self.pixel_scale) + (2 * circle_outline_thickness)), int((self.current_tool.jumble_size * self.pixel_scale) + (2 * circle_outline_thickness))]

                    # condition if cursor is on the map
                    if cursor_on_map:
                        cursors.add_cursor_this_frame('cursor_big_crosshair')
                        render_instance.store_draw(EditorMap.CIRCLE_OUTLINE_REFERENCE, render_instance.editor_circle_outline, {'ltwh': ltwh, 'circle_size': self.current_tool.jumble_size, 'circle_outline_thickness': circle_outline_thickness, 'circle_pixel_size': self.pixel_scale})
                        self.stored_draw_keys.append(EditorMap.CIRCLE_OUTLINE_REFERENCE)
                    current_color_rgba = percent_to_rgba(editor_singleton.currently_selected_color.color)

                    # change drawing state
                    if (self.current_tool.state == JumbleTool.NOT_JUMBLING) and keys_class_instance.editor_primary.newly_pressed and cursor_on_map:
                        self.current_tool.state = JumbleTool.JUMBLING
                        self.map_edits.append(self.PixelChange(new_rgba=current_color_rgba))
                    elif (self.current_tool.state == JumbleTool.JUMBLING) and keys_class_instance.editor_primary.released:
                        self.current_tool.state = JumbleTool.NOT_JUMBLING

                    try:
                        match self.current_tool.state:
                            case JumbleTool.NOT_JUMBLING:
                                pass
                            case JumbleTool.JUMBLING:
                                # setup for jumbling
                                reload_tiles = {}
                                map_edit = self.map_edits[-1].change_dict
                                max_tile_x, max_tile_y = self.tile_array_shape[0] - 1, self.tile_array_shape[1] - 1
                                max_pixel_x, max_pixel_y = self.original_map_wh[0] - 1, self.original_map_wh[1] - 1
                                outline_left, outline_top = pos_x - ((self.current_tool.jumble_size - 1) // 2), pos_y - ((self.current_tool.jumble_size - 1) // 2)

                                for (jumble_offset_x, jumble_offset_y) in self.current_tool.jumble_circle_true_indexes:
                                    if map_edit.get(tile_name := (edited_pixel_x := leftest_jumble_pixel+jumble_offset_x, edited_pixel_y := topest_jumble_pixel+jumble_offset_y)) is None:
                                        # skip the pixel if it's outside of the map
                                        if not ((0 <= edited_pixel_x <= max_pixel_x) and (0 <= edited_pixel_y <= max_pixel_y)):
                                            continue
                                        # get a pixel position for (edited_pixel_x, edited_pixel_y) to swap with
                                        while True:
                                            new_offset_x, new_offset_y = self.current_tool.jumble_circle_true_indexes[randint(0, self.current_tool.max_jumble_pixel)]
                                            new_location_x, new_location_y = leftest_jumble_pixel+new_offset_x, topest_jumble_pixel+new_offset_y
                                            if (0 <= new_location_x <= max_pixel_x) and (0 <= new_location_y <= max_pixel_y):
                                                break
                                        # get information about the first pixel
                                        tile_x1, pixel_x1 = divmod(edited_pixel_x, self.initial_tile_wh[0])
                                        tile_y1, pixel_y1 = divmod(edited_pixel_y, self.initial_tile_wh[1])
                                        tile1 = self.tile_array[tile_x1][tile_y1]
                                        if tile1.pg_image is None:
                                            tile1.load(render_instance, screen_instance, gl_context)
                                        color1 = tile1.pg_image.get_at((pixel_x1, pixel_y1))
                                        collision_index1 = (pixel_y1 * EditorMap.TILE_WH) + pixel_x1
                                        collision1 = tile1.collision_bytearray[collision_index1]
                                        reload_tiles[tile1.image_reference] = tile1
                                        # get information about the second pixel
                                        tile_x2, pixel_x2 = divmod(new_location_x, self.initial_tile_wh[0])
                                        tile_y2, pixel_y2 = divmod(new_location_y, self.initial_tile_wh[1])
                                        tile2 = self.tile_array[tile_x2][tile_y2]
                                        if tile2.pg_image is None:
                                            tile2.load(render_instance, screen_instance, gl_context)
                                        color2 = tile2.pg_image.get_at((pixel_x2, pixel_y2))
                                        collision_index2 = (pixel_y2 * EditorMap.TILE_WH) + pixel_x2
                                        collision2 = tile2.collision_bytearray[collision_index2]
                                        reload_tiles[tile2.image_reference] = tile2
                                        # make the swap
                                        tile1.pg_image.set_at((pixel_x1, pixel_y1), color2)
                                        tile1.collision_bytearray[collision_index1] = collision2
                                        tile2.pg_image.set_at((pixel_x2, pixel_y2), color1)
                                        tile2.collision_bytearray[collision_index2] = collision1
                                        # record what was edited for ctrl-Z

                                for tile in reload_tiles.values():
                                    render_instance.write_pixels_from_pg_surface(tile.image_reference, tile.pg_image)
                                    render_instance.write_pixels_from_bytearray(tile.collision_image_reference, tile.collision_bytearray)
                                    tile.save()
                    except CaseBreak:
                        pass

                case EyedropTool.INDEX:
                    if not point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh):
                        raise CaseBreak
                    
                    cursors.add_cursor_this_frame('cursor_eyedrop')

                    # get the tile being hovered over
                    pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
                    tile_x, pixel_x = divmod(pos_x, self.initial_tile_wh[0])
                    tile_y, pixel_y = divmod(pos_y, self.initial_tile_wh[1])
                    tile = self.tile_array[tile_x][tile_y]
                    # check whether the tile is already loaded
                    if tile.pg_image is None:
                        tile.load(render_instance, screen_instance, gl_context)
                    # make the edit
                    eyedrop_pixel_color = tile.pg_image.get_at((pixel_x, pixel_y))
                    eyedrop_pixel_color[3] = 255

                    if keys_class_instance.editor_primary.newly_pressed:
                        # update text input rgba and hex
                        red = eyedrop_pixel_color[0]
                        green = eyedrop_pixel_color[1]
                        blue = eyedrop_pixel_color[2]
                        alpha = eyedrop_pixel_color[3]
                        editor_singleton.add_color_dynamic_inputs[0].current_string = str(red)
                        editor_singleton.add_color_dynamic_inputs[1].current_string = str(green)
                        editor_singleton.add_color_dynamic_inputs[2].current_string = str(blue)
                        editor_singleton.add_color_dynamic_inputs[3].current_string = str(alpha)
                        editor_singleton.add_color_dynamic_inputs[4].current_string = f'{add_characters_to_front_of_string(base10_to_hex(red), 2, "0")}{add_characters_to_front_of_string(base10_to_hex(green), 2, "0")}{add_characters_to_front_of_string(base10_to_hex(blue), 2, "0")}{add_characters_to_front_of_string(base10_to_hex(alpha), 2, "0")}'
                        # update spectrum
                        eyedrop_pixel_color_glsl = rgba_to_glsl(eyedrop_pixel_color)
                        editor_singleton.add_color_spectrum_x_percentage, editor_singleton.add_color_saturation_percentage, editor_singleton.add_color_spectrum_y_percentage = editor_singleton.currently_selected_color.rgb_to_hsl(eyedrop_pixel_color_glsl)
                        editor_singleton.add_color_alpha_percentage = eyedrop_pixel_color_glsl[3]
                        color_spectrum_ltwh = editor_singleton.get_color_spectrum_ltwh()
                        spectrum_x_pos = move_number_to_desired_range(0, editor_singleton.add_color_spectrum_x_percentage * color_spectrum_ltwh[2], color_spectrum_ltwh[2])
                        spectrum_y_pos = move_number_to_desired_range(0, editor_singleton.add_color_spectrum_y_percentage * color_spectrum_ltwh[3], color_spectrum_ltwh[3])
                        mouse_in_bottom_half_of_spectrum = (spectrum_y_pos / color_spectrum_ltwh[3]) < 0.5
                        editor_singleton.add_color_current_circle_color = COLORS['WHITE'] if mouse_in_bottom_half_of_spectrum else COLORS['BLACK']
                        editor_singleton.add_color_circle_center_relative_xy = [spectrum_x_pos, abs(color_spectrum_ltwh[3] - spectrum_y_pos)]
                        editor_singleton.add_color_spectrum_x_percentage = (spectrum_x_pos / color_spectrum_ltwh[2])
                        editor_singleton.add_color_spectrum_y_percentage = abs(1 - (spectrum_y_pos / color_spectrum_ltwh[3]))
                        # update saturation
                        saturation_x_pos = move_number_to_desired_range(0, editor_singleton.add_color_saturation_percentage * color_spectrum_ltwh[2], color_spectrum_ltwh[2])
                        editor_singleton.add_color_saturation_circle_relative_x = saturation_x_pos
                        editor_singleton.currently_selected_color.saturation = editor_singleton.add_color_saturation_circle_relative_x / color_spectrum_ltwh[2]
                        editor_singleton.add_color_saturation_percentage = (saturation_x_pos / color_spectrum_ltwh[2])
                        # update alpha
                        alpha_x_pos = move_number_to_desired_range(0, editor_singleton.add_color_alpha_percentage * color_spectrum_ltwh[2], color_spectrum_ltwh[2])
                        editor_singleton.add_color_alpha_circle_relative_x = alpha_x_pos
                        editor_singleton.currently_selected_color.alpha = editor_singleton.add_color_alpha_circle_relative_x / color_spectrum_ltwh[2]
                        editor_singleton.add_color_alpha_percentage = (alpha_x_pos / color_spectrum_ltwh[2])
                        # update the currently selected color
                        editor_singleton.currently_selected_color.calculate_color(editor_singleton.add_color_spectrum_x_percentage, editor_singleton.add_color_spectrum_y_percentage, editor_singleton.add_color_alpha_percentage)
                        # update the palette
                        eyedrop_color_in_palette = False
                        for palette_index, palette_color in enumerate(editor_singleton.palette_colors):
                            if eyedrop_pixel_color == percent_to_rgba(palette_color):
                                eyedrop_color_in_palette = True
                                break
                        if eyedrop_color_in_palette:
                            editor_singleton.palette_just_clicked_new_color = True
                            editor_singleton.currently_selected_color.selected_through_palette = True
                            editor_singleton.currently_selected_color.palette_index = palette_index
                        else:
                            editor_singleton.currently_selected_color.selected_through_palette = False

        except CaseBreak:
            pass

    def get_color_of_pixel_on_map(self, keys_class_instance, render_instance, screen_instance, gl_context):
        if not point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh):
            return None

        # get the tile being hovered over
        pos_x, pos_y = self.get_cursor_position_on_map(keys_class_instance)
        tile_x, pixel_x = divmod(pos_x, self.initial_tile_wh[0])
        tile_y, pixel_y = divmod(pos_y, self.initial_tile_wh[1])
        tile = self.tile_array[tile_x][tile_y]
        # check whether the tile is already loaded
        if tile.pg_image is None:
            tile.load(render_instance, screen_instance, gl_context)
        # make the edit
        map_color = tile.pg_image.get_at((pixel_x, pixel_y))
        map_color[3] = 255
        return map_color

    def _hand(self, keys_class_instance):
        if not ((int(self.current_tool) == HandTool.INDEX) or (keys_class_instance.editor_hand.pressed)):
            self.held = EditorMap._NOT_HELD
            return

        # this function is for grabbing and moving the map editor
        if point_is_in_ltwh(keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value, self.image_space_ltwh):
            if keys_class_instance.editor_primary.newly_pressed:
                self.held = EditorMap._HAND_TOOL_HELD
                return
            if keys_class_instance.editor_hand.newly_pressed:
                self.held = EditorMap._EDITOR_HAND_HELD
                return

        if self.held:
            if keys_class_instance.editor_primary.released or keys_class_instance.editor_hand.released:
                self.held = EditorMap._NOT_HELD
                return
            self.map_offset_xy[0] += keys_class_instance.cursor_x_pos.delta
            self.map_offset_xy[1] += keys_class_instance.cursor_y_pos.delta
            return

    def get_cursor_position_on_map(self, keys_class_instance):
        # x = 0, y = 0 is top-left; x = image_space_ltwh[2], y = image_space_ltwh[3] is bottom-right; x = -1, y = -1 is invalid
        cursor_x, cursor_y = keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value
        left = math.floor(((cursor_x - self.image_space_ltwh[0]) / self.pixel_scale) - (self.map_offset_xy[0] / self.pixel_scale))
        top = math.floor(((cursor_y - self.image_space_ltwh[1]) / self.pixel_scale) - (self.map_offset_xy[1] / self.pixel_scale))
        return left, top

    def _get_tile_index(self, cursor_x: int, cursor_y: int):
        return cursor_x // self.tile_wh[0], cursor_y // self.tile_wh[1]

    def _get_ltrb_pixels_on_map(self):
        # get the leftest, topest, rightest, and bottomest pixels on the map
        leftest = math.floor(-(self.map_offset_xy[0] / self.pixel_scale))
        topest = math.floor(-(self.map_offset_xy[1] / self.pixel_scale))
        rightest = math.floor(((self.image_space_ltwh[2]) / self.pixel_scale) - (self.map_offset_xy[0] / self.pixel_scale))
        bottomest = math.floor(((self.image_space_ltwh[3]) / self.pixel_scale) - (self.map_offset_xy[1] / self.pixel_scale))
        return leftest, topest, rightest, bottomest

    def _update_map_with_scroll_bars(self, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar):
        if (horizontal_scroll.state == ScrollBar._SCROLL_GRABBED) or horizontal_scroll.mouse_scroll:
            max_scroll = -self.map_wh[0] + 1 + self.image_space_ltwh[2]
            self.map_offset_xy[0] = math.floor(horizontal_scroll.scroll_percentage * max_scroll)

        if (vertical_scroll.state == ScrollBar._SCROLL_GRABBED) or vertical_scroll.mouse_scroll:
            max_scroll = -self.map_wh[1] + 1 + self.image_space_ltwh[3]
            self.map_offset_xy[1] = math.floor(vertical_scroll.scroll_percentage * max_scroll)

    def _move_map_offset_to_bounds(self, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar):
        # update map bounds
        max_map_scroll_xy = [-self.map_wh[0] + 1 + self.image_space_ltwh[2], -self.map_wh[1] + 1 + self.image_space_ltwh[3]]
        self.map_offset_xy[0] = math.ceil(move_number_to_desired_range(max_map_scroll_xy[0], self.map_offset_xy[0], 0))
        self.map_offset_xy[1] = math.ceil(move_number_to_desired_range(max_map_scroll_xy[1], self.map_offset_xy[1], 0))

        # update scrolls with new map bounds
        horizontal_scroll.update_pixels_scrolled_with_percentage(self.map_offset_xy[0] / max_map_scroll_xy[0])
        vertical_scroll.update_pixels_scrolled_with_percentage(self.map_offset_xy[1] / max_map_scroll_xy[1])

    def _update_current_tool(self, current_tool: tuple[str, int]):
        self.current_tool = self.tools[current_tool[1]]

    def _execute_stored_draws(self, render_instance, screen_instance, gl_context):
        for key in self.stored_draw_keys:
            render_instance.execute_stored_draw(screen_instance, gl_context, key)
        self.stored_draw_keys = []

    def _create_editor_tiles(self):
        self.tile_array = []
        for column in range(self.tile_array_shape[0]):
            self.tile_array.append([EditorTile(self.base_path, column, row) for row in range(self.tile_array_shape[1])])

    def _reset_map(self, render_instance):
        # reset map from zoom
        for column in range(self.tile_array_shape[0]):
            for row in range(self.tile_array_shape[1]):
                try:
                    self.tile_array[column][row].unload(render_instance)
                except:
                    continue

        self.tile_wh = deepcopy(self.initial_tile_wh)
        self.image_space_ltwh = [0, 0, 0, 0]
        self.map_wh = deepcopy(self.original_map_wh)
        self.pixel_scale = 1
        self.map_offset_xy = [0, 0]
        self.tile_offset_xy = [0, 0]
        self.zoom_levels = len(EditorMap._ZOOM) - 1
        self.zoom_index = EditorMap._STARTING_ZOOM_INDEX
        self.left_tile    = -1
        self.top_tile     = -1
        self.right_tile   = -1
        self.bottom_tile  = -1
        self.loaded_x = []
        self.loaded_y = []
        self.held = False
        self.window_resize_last_frame = False


class EditorTile():
    PYGAME_IMAGE_FORMAT = "RGBA"
    PRETTY_MAP_BYTES_PER_PIXEL = 4
    COLLISION_MAP_BYTES_PER_PIXEL = 1

    def __init__(self, base_path: str, column: int, row: int):
        self.column: int = column
        self.row: int = row
        self.loaded: bool = False
        self.image_reference: str = f"{self.column}_{self.row}"
        self.collision_image_reference: str = f"c{self.column}_{self.row}"
        # self.image_path: str = f"{base_path}t{self.image_reference}.png"
        self.path: str = f"{base_path}t{self.image_reference}"
        self.pg_image: pygame.Surface | None = None
        self.collision_image: pygame.Surface | None = None
        self.pretty_bytearray: bytearray = None
        self.collision_bytearray: bytearray = None
        self.edits: dict = {}

    def load(self, render_instance, screen_instance, gl_context):
        if not self.loaded:
            self._load_bytearray()
            # load the pretty map
            self.pg_image = render_instance.add_moderngl_texture_using_bytearray(screen_instance, gl_context, self.pretty_bytearray, EditorTile.PRETTY_MAP_BYTES_PER_PIXEL, EditorMap.TILE_WH, EditorMap.TILE_WH, self.image_reference)
            # load the collision map
            render_instance.add_moderngl_texture_using_bytearray(screen_instance, gl_context, self.collision_bytearray, EditorTile.COLLISION_MAP_BYTES_PER_PIXEL, EditorMap.TILE_WH, EditorMap.TILE_WH, self.collision_image_reference)
        self.loaded = True

    def unload(self, render_instance):
        if self.loaded:
            self.pg_image = None
            self.pretty_bytearray = None
            render_instance.remove_moderngl_texture_from_renderable_objects_dict(self.image_reference)
            self.collision_bytearray = None
            self.collision_image = None
        self.loaded = False

    def save(self):
        with open(self.path, "wb") as file:
            # save the pretty image in png format
            file.write(bytearray(pygame.image.tobytes(self.pg_image, EditorTile.PYGAME_IMAGE_FORMAT)))
            # new line
            file.write("\n".encode(CollisionMode.UTF_8))
            # save the collision map
            file.write(self.collision_bytearray)

    def _load_bytearray(self):
        with open(self.path, mode='rb') as file:
            # get the byte array
            byte_array = bytearray(file.read())
            # separate the pretty map byte array
            self.pretty_bytearray = byte_array[0:(EditorMap.TILE_WH**2)*4]  # (256*256*4); 256 = tile width/height; 4 = number of bytes per pixel
            # separate the collision map byte array
            self.collision_bytearray = byte_array[((EditorMap.TILE_WH**2)*4)+1:((EditorMap.TILE_WH**2)*5)+1]

    def draw_image(self, render_instance, screen_instance, gl_context, ltwh: list[int, int, int, int], map_mode: MapModes, load: bool = False, draw_tiles: bool = True):
        loaded = False
        if load and not self.loaded:
            self.load(render_instance, screen_instance, gl_context)
            loaded = True

        if not self.loaded:
            return loaded

        if not draw_tiles:
            return True

        match map_mode:
            case MapModes.PRETTY:
                render_instance.basic_rect_ltwh_to_quad(screen_instance, gl_context, self.image_reference, ltwh)
            case MapModes.COLLISION:
                render_instance.draw_collision_map_tile_in_editor(screen_instance, gl_context, self.collision_image_reference, ltwh)
        return loaded
