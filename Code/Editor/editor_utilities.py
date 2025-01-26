from Code.utilities import point_is_in_ltwh, move_number_to_desired_range, get_text_width, get_text_height, get_time, str_can_be_int, str_can_be_float, str_can_be_hex, switch_to_base10, base10_to_hex, add_characters_to_front_of_string, get_rect_minus_borders, COLORS
import pygame
import math
from copy import deepcopy
from abc import ABC


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
                 default_value: str = '0'):

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
            render_instance.draw_string_of_characters(screen_instance, gl_context, self.current_string, [math.floor(background_ltwh[0] + self.text_padding), math.floor(background_ltwh[1] + self.text_padding)], self.text_pixel_size, self.text_color)
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
                render_instance.draw_string_of_characters(screen_instance, gl_context, string3, [start_left+string1_width+string2_width, top], self.text_pixel_size, self.text_color)
            if small_highlight_index == big_highlight_index:
                render_instance.draw_string_of_characters(screen_instance, gl_context, self.current_string, [math.floor(background_ltwh[0] + self.text_padding), math.floor(background_ltwh[1] + self.text_padding)], self.text_pixel_size, self.text_color)
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
        text_width = get_text_width(render_instance, string, self.text_pixel_size)
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


class EditorTool(ABC):
    """Tool base class"""
    STARTING_TOOL_INDEX = 5

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

    def __init__(self, active: bool):
        self._brush_thickness: int = PencilTool._MIN_BRUSH_THICKNESS
        super().__init__(active)

    @property
    def brush_thickness(self):
        return self._brush_thickness
    
    @brush_thickness.setter
    def brush_thickness(self, brush_thickness: int):
        self._brush_thickness = move_number_to_desired_range(PencilTool._MIN_BRUSH_THICKNESS, brush_thickness, PencilTool._MAX_BRUSH_THICKNESS)


class EraserTool(EditorTool):
    NAME = 'Eraser'
    INDEX = 3
    def __init__(self, active: bool):
        super().__init__(active)


class SprayTool(EditorTool):
    NAME = 'Spray'
    INDEX = 4
    def __init__(self, active: bool):
        super().__init__(active)


class HandTool(EditorTool):
    NAME = 'Hand'
    INDEX = 5
    def __init__(self, active: bool):
        super().__init__(active)


class BucketTool(EditorTool):
    NAME = 'Bucket'
    INDEX = 6
    def __init__(self, active: bool):
        super().__init__(active)


class LineTool(EditorTool):
    NAME = 'Line'
    INDEX = 7
    def __init__(self, active: bool):
        super().__init__(active)


class CurvyLineTool(EditorTool):
    NAME = 'Curvy line'
    INDEX = 8
    def __init__(self, active: bool):
        super().__init__(active)


class EmptyRectangleTool(EditorTool):
    NAME = 'Empty rectangle'
    INDEX = 9
    def __init__(self, active: bool):
        super().__init__(active)


class FilledRectangleTool(EditorTool):
    NAME = 'Filled rectangle'
    INDEX = 10
    def __init__(self, active: bool):
        super().__init__(active)


class EmptyEllipseTool(EditorTool):
    NAME = 'Empty ellipse'
    INDEX = 11
    def __init__(self, active: bool):
        super().__init__(active)


class FilledEllipseTool(EditorTool):
    NAME = 'Filled ellipse'
    INDEX = 12
    def __init__(self, active: bool):
        super().__init__(active)


class BlurTool(EditorTool):
    NAME = 'Blur'
    INDEX = 13
    def __init__(self, active: bool):
        super().__init__(active)


class JumbleTool(EditorTool):
    NAME = 'Jumble'
    INDEX = 14
    def __init__(self, active: bool):
        super().__init__(active)


class EyedropTool(EditorTool):
    NAME = 'Eyedropper'
    INDEX = 15
    def __init__(self, active: bool):
        super().__init__(active)


class EditorMap():
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
    _MAX_LOAD_TIME = 0.02

    _NOT_HELD = 0
    _HAND_TOOL_HELD = 1
    _EDITOR_HAND_HELD = 2

    def __init__(self,
                 base_path: str):

        self.base_path: str = "C:\\Users\\Kayle\\Desktop\\Hamster_Ball_Blight\\Projects\\Project1\\Level1\\"
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
            PencilTool(False),
            EraserTool(False),
            SprayTool(False),
            HandTool(True),
            BucketTool(False),
            LineTool(False),
            CurvyLineTool(False),
            EmptyRectangleTool(False),
            FilledRectangleTool(False),
            EmptyEllipseTool(False),
            FilledEllipseTool(False),
            BlurTool(False),
            JumbleTool(False),
            EyedropTool(False)
        ]
        self.current_tool: EditorTool = self.tools[5]

    def update(self, api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh: list[int, int, int, int], window_resize: bool, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar, current_tool: tuple[str, int]):
        self._update(api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh, window_resize, horizontal_scroll, vertical_scroll, current_tool)
        return
        try:
            self._update(api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh, window_resize, horizontal_scroll, vertical_scroll, current_tool)
        except:
            self._reset_map(render_instance)

    def _update(self, api, screen_instance, gl_context, keys_class_instance, render_instance, cursors, image_space_ltwh: list[int, int, int, int], window_resize: bool, horizontal_scroll: ScrollBar, vertical_scroll: ScrollBar, current_tool: tuple[str, int]):
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

        # perform edits to the map
        self._draw(screen_instance, gl_context, keys_class_instance, render_instance, cursors)

        # calculate which tiles should be loaded and unloaded; perform unloading
        self._update_loaded_tiles(render_instance)

        # iterate through tiles that should be loaded; load them; draw them
        self._iterate_through_tiles(render_instance, screen_instance, gl_context, True, True)

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
        original_cursor_x, original_cursor_y = self._get_cursor_position_on_map(keys_class_instance)
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
                self.tile_array[column][row].unload(render_instance, column, row)
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
                    self.tile_array[column][row].unload(render_instance, column, row)
                self.loaded_x = sorted([tile for tile in self.loaded_x if tile not in unload_x])
        if (unload_y != []):
            for row in unload_y:
                for column in self.loaded_x:
                    self.tile_array[column][row].unload(render_instance, column, row)
                self.loaded_y = sorted([tile for tile in self.loaded_y if tile not in unload_y])
        # update which tiles are loaded
        if (load_x != []):
            # self.loaded_x += load_x
            self.loaded_x += [x for x in load_x if x not in unload_x]
            self.loaded_x = sorted(self.loaded_x)
        if (load_y != []):
            # self.loaded_y += load_y
            self.loaded_y += [y for y in load_y if y not in unload_y]
            self.loaded_y = sorted(self.loaded_y)

    def _iterate_through_tiles(self, render_instance, screen_instance, gl_context, draw_tiles: bool, load_tiles: bool):
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
                loaded = tile.draw_image(render_instance, screen_instance, gl_context, self.base_path, column, row, [left, top, self.tile_wh[0], self.tile_wh[1]], self.pixel_scale, load and load_tiles, draw_tiles)
                if loaded and not started_loading:
                    started_loading = True
                    start_load = get_time()
                top += self.tile_wh[1]
            left += self.tile_wh[0]

    def _draw(self, screen_instance, gl_context, keys_class_instance, render_instance, cursors):
        match int(self.current_tool):
            case MarqueeRectangleTool.INDEX:
                pass
            case LassoTool.INDEX:
                pass
            case PencilTool.INDEX:
                pass
            case EraserTool.INDEX:
                pass
            case SprayTool.INDEX:
                pass
            case HandTool.INDEX:
                pass
            case BucketTool.INDEX:
                pass
            case LineTool.INDEX:
                pass
            case CurvyLineTool.INDEX:
                pass
            case EmptyRectangleTool.INDEX:
                pass
            case FilledRectangleTool.INDEX:
                pass
            case EmptyEllipseTool.INDEX:
                pass
            case FilledEllipseTool.INDEX:
                pass
            case BlurTool.INDEX:
                pass
            case JumbleTool.INDEX:
                pass
            case EyedropTool.INDEX:
                pass


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

    def _get_cursor_position_on_map(self, keys_class_instance):
        # x = 0, y = 0 is top-left; x = image_space_ltwh[2], y = image_space_ltwh[3] is bottom-right; x = -1, y = -1 is invalid
        cursor_x, cursor_y = keys_class_instance.cursor_x_pos.value, keys_class_instance.cursor_y_pos.value
        if not point_is_in_ltwh(cursor_x, cursor_y, self.image_space_ltwh):
            return -1, -1
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

    def _create_editor_tiles(self):
        self.tile_array = []
        for _ in range(self.tile_array_shape[0]):
            self.tile_array.append([EditorTile() for _ in range(self.tile_array_shape[1])])

    def _reset_map(self, render_instance):
        # reset map from zoom
        for column in range(self.tile_array_shape[0]):
            for row in range(self.tile_array_shape[1]):
                try:
                    self.tile_array[column][row].unload(render_instance, column, row)
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
    def __init__(self):
        self.loaded: bool = False
        self.gl_image_reference: str | None = None
        self.pg_image: None = None

    def load(self, render_instance, screen_instance, gl_context, path: str, column: int, row: int, scale: int):
        if not self.loaded:
            # render_instance.add_moderngl_texture_to_renderable_objects_dict(screen_instance, gl_context, f"{path}t{column}_{row}.png", f"{column}_{row}")
            render_instance.add_moderngl_texture_scaled(screen_instance, gl_context, f"{path}t{column}_{row}.png", f"{column}_{row}", move_number_to_desired_range(0, scale, 1))
        self.loaded = True

    def unload(self, render_instance, column: int, row: int):
        if self.loaded:
            render_instance.remove_moderngl_texture_from_renderable_objects_dict(f"{column}_{row}")
        self.loaded = False

    def draw_image(self, render_instance, screen_instance, gl_context, path: str, column: int, row: int, ltwh: list[int, int, int, int], scale: int, load: bool = False, draw_tiles: bool = True):
        loaded = False
        if load and not self.loaded:
            self.load(render_instance, screen_instance, gl_context, path, column, row, scale)
            loaded = True

        if not self.loaded:
            return loaded

        if not draw_tiles:
            return True

        render_instance.basic_rect_ltwh_to_quad(screen_instance, gl_context, f"{column}_{row}", ltwh)
        return loaded

    def _edit_image(self):
        pass
