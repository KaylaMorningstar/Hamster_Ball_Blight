import math
import random
import pygame
from copy import deepcopy
from Code.utilities import rgba_to_glsl, percent_to_rgba, COLORS, get_text_height, get_text_width, point_is_in_ltwh, IMAGE_PATHS, loading_and_unloading_images_manager, get_rect_minus_borders, round_scaled, ceil_scaled, floor_scaled, LOADED_IN_EDITOR, LOADED_IN_GAME, LOADED_IN_MENU, OFF_SCREEN, move_number_to_desired_range, get_time, switch_to_base10, base10_to_hex, add_characters_to_front_of_string
from Code.Editor.editor_update import update_palette, update_header, update_footer, update_tools, update_add_color, update_tool_attributes, update_collision_selector
from Code.Editor.editor_utilities import TextInput, CurrentlySelectedColor, HeaderManager, ScrollBar, EditorMap, get_tf_circle
from Code.Editor.editor_utilities import EditorTool, MarqueeRectangleTool, LassoTool, PencilTool, SprayTool, HandTool, BucketTool, LineTool, CurvyLineTool, RectangleEllipseTool, BlurTool, JumbleTool, EyedropTool
from Code.Editor.editor_utilities import MapModes, EditorModes, CollisionSelector, CollisionMode
import random



class EditorSingleton():
    def __init__(self, Render, Screen, gl_context, PATH):
        self.editor_enabled = True
        self.border_color = COLORS['BLACK']
        self.map_mode = MapModes.PRETTY
        self.editor_mode = EditorModes.DRAW
        #
        # header
        self.header_text_pixel_color = COLORS['BLACK']
        self.header_background_color = COLORS['PINK']
        self.header_highlight_color = (COLORS['YELLOW'][0], COLORS['YELLOW'][1], COLORS['YELLOW'][2], COLORS['YELLOW'][3] * 0.5)
        self.header_selected_color = COLORS['YELLOW']
        self.header_border_color = COLORS['WHITE']
        self.header_border_thickness = 25
        self.header_strings = ['FILE', 'EDIT', 'OPTIONS']
        self.header_string_selected = ''
        self.header_index_selected = -1
        self.header_indexes = [index for index in range(len(self.header_strings))]
        self.header_which_selected = [False for string in self.header_strings]
        self.header_selected = False
        self.header_padding = 10
        self.header_text_pixel_size = 3
        self.header_string_text_width = [get_text_width(Render, header_option, self.header_text_pixel_size) for header_option in self.header_strings]
        self.distance_between_header_options = 2 * self.header_padding
        current_left_position = self.distance_between_header_options
        self.header_strings_lefts = []
        self.header_strings_top = 0.5 * self.header_padding
        self.header_hover_ltwh = []
        self.header_height = self.header_padding + get_text_height(self.header_text_pixel_size) - (2 * self.header_text_pixel_size)
        for width in self.header_string_text_width:
            self.header_strings_lefts.append(current_left_position)
            hover_width = (self.distance_between_header_options * 2) + width
            self.header_hover_ltwh.append([current_left_position - self.distance_between_header_options, 0, hover_width, self.header_height])
            current_left_position += hover_width
        #
        self.header_manager_padding = 10
        self.header_manager_padding_between_items = 20
        self.header_manager_border_thickness = 3
        self.header_options = {
            'FILE': HeaderManager(Render,
                                  option_names_and_responses={'New project': lambda: print('a'),
                                                              'New level': lambda: print('a'),
                                                              'Save level': lambda: print('b'),
                                                              'Main menu': lambda: print('c'),
                                                              'Exit game': lambda: print('d'),},
                                  text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[0][0], top = self.header_height),

            'EDIT': HeaderManager(Render,
                                  option_names_and_responses={'Undo': lambda: print('e'),
                                                              'Paste': lambda: print('f'),
                                                              'Rotate': lambda: print('g'),
                                                              'Replace color': lambda: print('h'),
                                                              'Flip': lambda: print('i'),},
                                  text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[1][0], top = self.header_height),

            'OPTIONS': HeaderManager(Render,
                                     option_names_and_responses={'Play level': lambda: print('j'),
                                                                 'Toggle map': lambda: print('k'),
                                                                 'Show grid': lambda: print('l'),},
                                     text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[2][0], top = self.header_height),
            }
        self.header_bottom = self.header_height + self.header_border_thickness
        #
        # play button
        self.play_text_color = self.header_text_pixel_color
        self.play_highlight_color = self.header_highlight_color
        self.play_selected_color = self.header_selected_color
        self.play_text = 'PLAY'
        self.play_text_pixel_size = self.header_text_pixel_size
        self.play_text_width = get_text_width(Render, self.play_text, self.play_text_pixel_size)
        self.play_button_box_ltwh = [0, 0, (2 * self.distance_between_header_options) + self.play_text_width, self.header_border_thickness]
        self.play_button_text_lt = [0, self.header_strings_top]
        #
        # palette
        self.palette_border_color = COLORS['PINK']
        self.palette_background_color = COLORS['GREY']
        self.palette_colors_border_color = COLORS['BLACK']
        self.palette_colors = [rgba_to_glsl((random.randint(0,255), random.randint(0,255), random.randint(0,255), random.randint(0,255))) for _ in range(1000)]
        self.palette_color_wh = [35, 35]
        self.palette_colors_before_move = []
        self.last_palette_index_during_move = -1
        self.last_highlight_palette_ltwh_during_move = [0, 0, self.palette_color_wh[0], self.palette_color_wh[1]]
        self.palette_colors_per_row = 5
        self.palette_padding = 7
        self.palette_space_between_colors_and_scroll = 8
        self.palette_scroll_width = 20
        self.palette_scroll_height = 50
        self.palette_color_border_thickness = 2
        self.palette_ltwh = [0, self.header_bottom, (2 * self.palette_padding) + (self.palette_colors_per_row * self.palette_color_wh[0]) + self.palette_space_between_colors_and_scroll + self.palette_scroll_width - (self.palette_color_border_thickness * (self.palette_colors_per_row) - 1), 0]
        self.currently_selected_color = CurrentlySelectedColor(self.palette_colors[0], 0, self.palette_color_wh[0])
        self.palette_pressed_add_or_remove_button_this_frame = False
        self.palette_moving_a_color_color = COLORS['RED']
        self.palette_moving_a_color = False
        self.palette_just_clicked_new_color = False
        self.palette_moving_color_cursor_distance_from_top_or_bottom = 30
        self.time_between_palette_moves_while_holding_color = 0.05
        self.time_since_moving_palette_while_holding_color = get_time()
        # palette scroll bar
        self.palette_scroll_background_color = COLORS['WHITE']
        self.palette_scroll_border_color = COLORS['BLUE']
        self.palette_scroll_inside_unhighlighted = rgba_to_glsl((255, 255, 255, 255))
        self.palette_scroll_inside_hightlighted = rgba_to_glsl((200, 200, 200, 255))
        self.palette_scroll_inside_grabbed = rgba_to_glsl((150, 150, 150, 255))
        self.palette_scroll_border_thickness = 4
        self.palette_scroll_is_grabbed = False
        self.palette_scroll_cursor_was_above = False
        self.palette_scroll_cursor_was_below = False
        self.palette_scroll_ltwh = [self.palette_ltwh[2] - self.palette_padding - self.palette_scroll_width, 0, self.palette_scroll_width, self.palette_scroll_height]
        self.palette_scroll_percentage = 0.0
        self.palette_pixels_down = 0
        #
        # separate palette and add color
        self.separate_palette_and_add_color_ltwh = [0, 0, self.palette_ltwh[2], 0]
        #
        # footer
        self.footer_color = COLORS['BLUE']
        self.footer_ltwh = [0, 0, 0, self.header_height]
        self.footer_text_pixel_size = 3
        self.active_color_circle_padding = 3
        self.footer_active_color_outline_thickness = 1
        self.footer_active_color_circle_wh = self.footer_ltwh[3] - (2 * self.active_color_circle_padding)
        self.footer_active_color_circle_inside_wh = self.footer_active_color_circle_wh - (2 * self.footer_active_color_outline_thickness)
        pygame_circle_image = pygame.Surface((self.footer_active_color_circle_inside_wh, self.footer_active_color_circle_inside_wh), pygame.SRCALPHA)
        for left, row in enumerate(get_tf_circle(self.footer_active_color_circle_inside_wh)):
            for top, draw in enumerate(row):
                if draw:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 255))
                else:
                    pygame_circle_image.set_at((left, top), (0, 0, 0, 0))
        self.footer_active_color_circle_reference = 'footer_active_color_circle_reference'
        Render.add_moderngl_texture_with_surface(Screen, gl_context, pygame_circle_image, self.footer_active_color_circle_reference)
        #
        # add color
        # add/remove color
        self.add_color_words_border_color = COLORS['BLACK']
        self.add_color_words_text_pixel_size = 3
        self.add_color_words_border_thickness = 5
        self.add_color_words_padding = 4
        self.add_color_words = "ADD COLOR"
        self.remove_color_words = "REMOVE COLOR"
        self.add_color_words_length = get_text_width(Render, self.add_color_words, self.add_color_words_text_pixel_size)
        self.remove_color_words_length = get_text_width(Render, self.remove_color_words, self.add_color_words_text_pixel_size)
        self.add_color_words_background_ltwh = [self.palette_padding, self.separate_palette_and_add_color_ltwh[1] + self.separate_palette_and_add_color_ltwh[3] + self.palette_padding, self.palette_ltwh[2] - (2 * self.palette_padding), get_text_height(self.add_color_words_text_pixel_size) - (2 * self.add_color_words_text_pixel_size) + (2 * self.add_color_words_border_thickness) + (2 * self.add_color_words_padding)]
        self.add_color_words_lt = [math.floor(self.add_color_words_background_ltwh[0] + (self.add_color_words_background_ltwh[2] / 2) - (self.add_color_words_length / 2)), self.add_color_words_background_ltwh[1] + self.add_color_words_border_thickness + self.add_color_words_padding]
        self.remove_color_words_lt = [math.floor(self.add_color_words_background_ltwh[0] + (self.add_color_words_background_ltwh[2] / 2) - (self.remove_color_words_length / 2)), self.add_color_words_background_ltwh[1] + self.add_color_words_border_thickness + self.add_color_words_padding]
        self.gap_between_add_or_remove_color_and_spectrum = 4
        self.add_or_remove_checkerboard_ltwh = [self.add_color_words_background_ltwh[0] + self.add_color_words_border_thickness, self.add_color_words_background_ltwh[1] + self.add_color_words_border_thickness, self.add_color_words_background_ltwh[2] - (2 * self.add_color_words_border_thickness), self.add_color_words_background_ltwh[3] - (2 * self.add_color_words_border_thickness)]
        self.add_or_remove_checkerboard_repeat = 32
        # spectrum
        self.add_color_background_color = COLORS['PINK']
        self.add_color_spectrum_border_color = COLORS['BLACK']
        self.add_color_spectrum_height = 150
        self.add_color_spectrum_border_thickness = self.add_color_words_border_thickness
        self.add_color_spectrum_ltwh = [self.palette_padding + self.add_color_spectrum_border_thickness, self.separate_palette_and_add_color_ltwh[1] + self.separate_palette_and_add_color_ltwh[3] + self.palette_padding + self.add_color_spectrum_border_thickness, self.palette_ltwh[2] - (2 * self.palette_padding) - (2 * self.add_color_spectrum_border_thickness), self.add_color_spectrum_height - (2 * self.add_color_spectrum_border_thickness)]
        self.add_color_circle_center_relative_xy = [0, 0]
        self.add_color_spectrum_x_percentage = 0.0
        self.add_color_spectrum_y_percentage = 0.0
        self.add_color_circle_ltwh = [self.add_color_spectrum_ltwh[0], OFF_SCREEN, Render.renderable_objects['editor_circle'].ORIGINAL_WIDTH, Render.renderable_objects['editor_circle'].ORIGINAL_HEIGHT]
        self.add_color_circle_is_held = False
        self.add_color_current_circle_color = COLORS['BLACK'] # changes with left-click on spectrum
        self.add_color_saturation_ltwh = [self.add_color_spectrum_ltwh[0], self.add_color_spectrum_ltwh[1] + self.add_color_spectrum_ltwh[3], self.add_color_spectrum_ltwh[2], 13]
        self.add_color_saturation_circle_ltwh = [self.add_color_spectrum_ltwh[0], OFF_SCREEN, Render.renderable_objects['editor_circle'].ORIGINAL_WIDTH, Render.renderable_objects['editor_circle'].ORIGINAL_HEIGHT]
        self.add_color_saturation_circle_is_held = False
        self.add_color_saturation_circle_relative_x = self.add_color_spectrum_ltwh[2]
        self.add_color_saturation_percentage = 1.0
        self.add_color_alpha_ltwh = [self.add_color_spectrum_ltwh[0], self.add_color_spectrum_ltwh[1] + self.add_color_spectrum_ltwh[3], self.add_color_spectrum_ltwh[2], 13]
        self.add_color_alpha_circle_ltwh = [self.add_color_spectrum_ltwh[0], OFF_SCREEN, Render.renderable_objects['editor_circle'].ORIGINAL_WIDTH, Render.renderable_objects['editor_circle'].ORIGINAL_HEIGHT]
        self.add_color_alpha_circle_is_held = False
        self.add_color_alpha_circle_relative_x = self.add_color_spectrum_ltwh[2]
        self.add_color_alpha_percentage = 1.0
        self.add_color_alpha_checker_x = 7
        self.add_color_alpha_checker_y = 7
        self.add_color_alpha_checker_color1 = COLORS['GREY']
        self.add_color_alpha_checker_color2 = COLORS['WHITE']
        # rgba input
        self.add_color_input_inputs_and_equals_color = COLORS['BLACK']
        self.add_color_input_background_color = COLORS['LIGHT_GREY']
        self.add_color_input_highlighted_text_color = COLORS['WHITE']
        self.add_color_input_highlighted_background_color = COLORS['RED']
        self.add_color_input_space_between_inputs = 12
        self.add_color_input_text_pixel_size = 3
        self.add_color_input_single_input_height = self.add_color_input_space_between_inputs + get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size)
        self.add_color_inputs = ['R', 'G', 'B', 'A', 'HEX #']
        self.add_color_input_equals_symbol = '='
        self.add_color_input_max_length = 0
        self.add_color_input_max_length = max([get_text_width(Render, character, self.add_color_input_text_pixel_size) for character in self.add_color_inputs if len(character) == 1])
        self.add_color_input_top = self.add_color_spectrum_ltwh[1] + self.add_color_spectrum_ltwh[3]
        self.add_color_input_color_equals_input_left = [self.palette_padding, self.palette_padding + self.add_color_input_max_length + get_text_width(Render, ' ', self.add_color_input_text_pixel_size), self.palette_padding + self.add_color_input_max_length + get_text_width(Render, ' = ', self.add_color_input_text_pixel_size) - self.add_color_input_text_pixel_size]
        self.add_color_input_height = (self.add_color_input_space_between_inputs * 6) + (5 * (get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size)))
        self.add_color_dynamic_inputs = [TextInput([self.add_color_input_color_equals_input_left[2], 0, self.palette_ltwh[2] - (2 * self.palette_padding) - self.add_color_input_max_length - get_text_width(Render, ' = ', self.add_color_input_text_pixel_size) + self.add_color_input_text_pixel_size, get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size) + (self.add_color_input_space_between_inputs / 2)], self.add_color_input_background_color, self.add_color_input_inputs_and_equals_color, self.add_color_input_highlighted_text_color, self.add_color_input_highlighted_background_color, self.add_color_input_text_pixel_size, (self.add_color_input_space_between_inputs / 4), allowable_range=[0, 255], is_an_int=True, must_fit=True, default_value='255'),
                                         TextInput([self.add_color_input_color_equals_input_left[2], 0, self.palette_ltwh[2] - (2 * self.palette_padding) - self.add_color_input_max_length - get_text_width(Render, ' = ', self.add_color_input_text_pixel_size) + self.add_color_input_text_pixel_size, get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size) + (self.add_color_input_space_between_inputs / 2)], self.add_color_input_background_color, self.add_color_input_inputs_and_equals_color, self.add_color_input_highlighted_text_color, self.add_color_input_highlighted_background_color, self.add_color_input_text_pixel_size, (self.add_color_input_space_between_inputs / 4), allowable_range=[0, 255], is_an_int=True, must_fit=True, default_value='255'),
                                         TextInput([self.add_color_input_color_equals_input_left[2], 0, self.palette_ltwh[2] - (2 * self.palette_padding) - self.add_color_input_max_length - get_text_width(Render, ' = ', self.add_color_input_text_pixel_size) + self.add_color_input_text_pixel_size, get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size) + (self.add_color_input_space_between_inputs / 2)], self.add_color_input_background_color, self.add_color_input_inputs_and_equals_color, self.add_color_input_highlighted_text_color, self.add_color_input_highlighted_background_color, self.add_color_input_text_pixel_size, (self.add_color_input_space_between_inputs / 4), allowable_range=[0, 255], is_an_int=True, must_fit=True, default_value='255'),
                                         TextInput([self.add_color_input_color_equals_input_left[2], 0, self.palette_ltwh[2] - (2 * self.palette_padding) - self.add_color_input_max_length - get_text_width(Render, ' = ', self.add_color_input_text_pixel_size) + self.add_color_input_text_pixel_size, get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size) + (self.add_color_input_space_between_inputs / 2)], self.add_color_input_background_color, self.add_color_input_inputs_and_equals_color, self.add_color_input_highlighted_text_color, self.add_color_input_highlighted_background_color, self.add_color_input_text_pixel_size, (self.add_color_input_space_between_inputs / 4), allowable_range=[0, 255], is_an_int=True, must_fit=True, default_value='255'),
                                         TextInput([self.palette_padding + get_text_width(Render, self.add_color_inputs[4], self.add_color_input_text_pixel_size) + self.add_color_input_text_pixel_size, 0, self.palette_ltwh[2] - (2 * self.palette_padding) - get_text_width(Render, self.add_color_inputs[4], self.add_color_input_text_pixel_size) - self.add_color_input_text_pixel_size, get_text_height(self.add_color_input_text_pixel_size) - (2 * self.add_color_input_text_pixel_size) + (self.add_color_input_space_between_inputs / 2)], self.add_color_input_background_color, self.add_color_input_inputs_and_equals_color, self.add_color_input_highlighted_text_color, self.add_color_input_highlighted_background_color, self.add_color_input_text_pixel_size, (self.add_color_input_space_between_inputs / 4), allowable_range=[switch_to_base10('00000000', 16), switch_to_base10('ffffffff', 16)], is_a_hex=True, show_front_zeros=True, number_of_digits=8, must_fit=True, default_value='ffffffff'),]
        self.add_color_input_moving_down = False
        self.add_color_input_last_move_time = get_time()
        self.add_color_input_initial_fast_move = get_time()
        self.add_color_input_time_before_fast_move = 0.50
        self.add_color_input_time_between_moves = 0.05
        self.add_color_ltwh = [0, 0, self.palette_ltwh[2], (2 * self.palette_padding) + self.add_color_words_background_ltwh[3] + self.gap_between_add_or_remove_color_and_spectrum + self.add_color_spectrum_height + self.add_color_saturation_ltwh[3] + self.add_color_alpha_ltwh[3] + self.add_color_input_height - self.palette_padding]
        #
        # tool bar
        self.tool_bar_color = COLORS['RED']
        self.tool_bar_glow_color = COLORS['WHITE']
        self.tool_bar_padding = 5
        self.tool_bar_outline_pixels = 3
        self.tool_bar_tool_width = Render.renderable_objects['Marquee rectangle'].ORIGINAL_WIDTH
        self.tool_bar_ltwh = [0, self.header_bottom, Render.renderable_objects['Marquee rectangle'].ORIGINAL_WIDTH + (2 * self.tool_bar_padding), 0]
        tool_bar_tool_names_and_indexes = [(deepcopy(MarqueeRectangleTool.NAME), deepcopy(MarqueeRectangleTool.INDEX)),
                                           (deepcopy(LassoTool.NAME), deepcopy(LassoTool.INDEX)),
                                           (deepcopy(PencilTool.NAME), deepcopy(PencilTool.INDEX)),
                                           (deepcopy(SprayTool.NAME), deepcopy(SprayTool.INDEX)),
                                           (deepcopy(HandTool.NAME), deepcopy(HandTool.INDEX)),
                                           (deepcopy(BucketTool.NAME), deepcopy(BucketTool.INDEX)),
                                           (deepcopy(LineTool.NAME), deepcopy(LineTool.INDEX)),
                                           (deepcopy(CurvyLineTool.NAME), deepcopy(CurvyLineTool.INDEX)),
                                           (deepcopy(RectangleEllipseTool.NAME), deepcopy(RectangleEllipseTool.INDEX)),
                                           (deepcopy(BlurTool.NAME), deepcopy(BlurTool.INDEX)),
                                           (deepcopy(JumbleTool.NAME), deepcopy(JumbleTool.INDEX)),
                                           (deepcopy(EyedropTool.NAME), deepcopy(EyedropTool.INDEX))]
        self.tool_bar_tools = []
        self.tool_active = tool_bar_tool_names_and_indexes[EditorTool.STARTING_TOOL_INDEX]
        for tool_name, tool_index in tool_bar_tool_names_and_indexes:
            self.tool_bar_tools.append([[0, self.header_bottom + (Render.renderable_objects[tool_name].ORIGINAL_HEIGHT * tool_index) + (self.tool_bar_padding * (tool_index + 1)), Render.renderable_objects[tool_name].ORIGINAL_WIDTH, Render.renderable_objects[tool_name].ORIGINAL_HEIGHT], # ltwh
                                         True if tool_name == self.tool_active[0] else False, # selected
                                         tool_name # name
                                         ])
        #
        # image area
        self.image_large_border_color = COLORS['PINK']
        self.image_large_inside_color = COLORS['GREY']
        self.image_large_border_thickness = self.palette_padding
        self.image_large_border_ltwh = [self.palette_ltwh[0],
                                        self.header_height + self.header_border_thickness,
                                        self.tool_bar_ltwh[0] - self.palette_ltwh[0],
                                        self.footer_ltwh[1] - self.header_height - self.header_border_thickness]
        self.image_inside_border_ltwh = [0, 0, 0, 0]
        self.image_vertical_scroll = ScrollBar(scroll_area_lt=[0, 0], is_vertical=True, scroll_thickness=22, scroll_length=50, scroll_area_border_thickness=self.image_large_border_thickness, scroll_border_thickness=5, border_color=COLORS['PINK'], background_color=COLORS['WHITE'], scroll_border_color=COLORS['RED'], unhighlighted_color=COLORS['WHITE'], shaded_color=COLORS['LIGHT_GREY'], highlighted_color=COLORS['GREY'])
        self.image_horizontal_scroll = ScrollBar(scroll_area_lt=[0, 0], is_vertical=False, scroll_thickness=22, scroll_length=50, scroll_area_border_thickness=self.image_large_border_thickness, scroll_border_thickness=5, border_color=COLORS['PINK'], background_color=COLORS['WHITE'], scroll_border_color=COLORS['RED'], unhighlighted_color=COLORS['WHITE'], shaded_color=COLORS['LIGHT_GREY'], highlighted_color=COLORS['GREY'])
        self.image_area_ltwh = [0, 0, 0, 0]
        self.window_resize_last_frame = False
        self.map: EditorMap = EditorMap(PATH, Screen, gl_context, Render, PATH)
        #
        # tool attribute area
        self.tool_attribute_ltwh = [0, 0, 0, 0]
        #
        # collision selector area
        self.collision_selector_border_color = COLORS['PINK']
        self.collision_selector_inner_color = COLORS['WHITE']
        self.collision_selector_circle_color = COLORS['WHITE']
        self.collision_selector_text_color = COLORS['BLACK']
        self.collision_selector_color_indicator_border_color = COLORS['BLACK']
        self.collision_selector_text_pixel_size = 3
        self.collision_selector_space_between_text_and_circle = 2
        self.collision_selector_circle_thickness = 3
        self.collision_selector_additional_padding = 0
        self.collision_selector_space_between_options = (2 * self.collision_selector_space_between_text_and_circle) + self.collision_selector_circle_thickness
        self.collision_selector_square_color_indicator_thickness = 2
        self.collision_selector_square_color_indicator_padding = 1
        self.collision_selector_modes = {'no_collision': CollisionSelector(Render, text_color=self.collision_selector_text_color, color=CollisionMode.NO_COLLISION_COLOR, text='NO COLLISION', text_pixel_size=self.collision_selector_text_pixel_size, mode=CollisionMode.NO_COLLISION),
                                         'collision': CollisionSelector(Render, text_color=self.collision_selector_text_color, color=CollisionMode.COLLISION_COLOR, text='COLLISION', text_pixel_size=self.collision_selector_text_pixel_size, mode=CollisionMode.COLLISION, active=True),
                                         'grappleable': CollisionSelector(Render, text_color=self.collision_selector_text_color, color=CollisionMode.GRAPPLEABLE_COLOR, text='GRAPPLE', text_pixel_size=self.collision_selector_text_pixel_size, mode=CollisionMode.GRAPPLEABLE),
                                         'platform': CollisionSelector(Render, text_color=self.collision_selector_text_color, color=CollisionMode.PLATFORM_COLOR, text='PLATFORM', text_pixel_size=self.collision_selector_text_pixel_size, mode=CollisionMode.PLATFORM),
                                         'water': CollisionSelector(Render, text_color=self.collision_selector_text_color, color=CollisionMode.WATER_COLOR, text='WATER', text_pixel_size=self.collision_selector_text_pixel_size, mode=CollisionMode.WATER)}
        self.collision_selector_ltwh = [0, self.header_bottom, self.palette_ltwh[2], (len(self.collision_selector_modes) * get_text_height(self.collision_selector_text_pixel_size)) - (2 * self.collision_selector_text_pixel_size) + ((len(self.collision_selector_modes) + 1) * self.collision_selector_circle_thickness) + (len(self.collision_selector_modes) * self.collision_selector_space_between_text_and_circle) + (2 * self.collision_selector_additional_padding)]
        self.collision_selector_mode = CollisionMode.COLLISION
        #
        # other
        self.stored_draws = []
        self.xy = [0, 0]

    def get_color_spectrum_ltwh(self):
        return [self.palette_padding + self.add_color_spectrum_border_thickness, 
                self.separate_palette_and_add_color_ltwh[1] + self.add_color_words_background_ltwh[3] + self.gap_between_add_or_remove_color_and_spectrum + self.separate_palette_and_add_color_ltwh[3] + self.palette_padding + self.add_color_spectrum_border_thickness, 
                self.palette_ltwh[2] - (2 * self.palette_padding) - (2 * self.add_color_spectrum_border_thickness), 
                self.add_color_spectrum_height - (2 * self.add_color_spectrum_border_thickness)]


def update_image(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor):
    #
    # update larger image border ltwh
    Singleton.image_large_border_ltwh = [Singleton.palette_ltwh[2] - Singleton.image_large_border_thickness,
                                         Singleton.header_height + Singleton.header_border_thickness,
                                         Singleton.tool_bar_ltwh[0] - Singleton.palette_ltwh[2] + Singleton.image_large_border_thickness,
                                         Singleton.footer_ltwh[1] - Singleton.header_height - Singleton.header_border_thickness]
    Singleton.image_inside_border_ltwh = get_rect_minus_borders(Singleton.image_large_border_ltwh, Singleton.image_large_border_thickness)
    #
    # update image area ltwh
    Singleton.image_area_ltwh[0] = Singleton.image_inside_border_ltwh[0]
    Singleton.image_area_ltwh[1] = Singleton.image_inside_border_ltwh[1]
    Singleton.image_area_ltwh[2] = Singleton.image_inside_border_ltwh[2] - Singleton.image_vertical_scroll.scroll_area_ltwh[2] + Singleton.image_large_border_thickness
    Singleton.image_area_ltwh[3] = Singleton.image_inside_border_ltwh[3] - Singleton.image_horizontal_scroll.scroll_area_ltwh[3] + Singleton.image_large_border_thickness
    #
    # update image
    Singleton.tool_attribute_ltwh = [Singleton.image_area_ltwh[0], Singleton.header_height, Singleton.image_area_ltwh[2], Singleton.header_border_thickness]
    if Screen.window_resize:
        Singleton.window_resize_last_frame = True
    else:
        Singleton.map.update(Api, Screen, gl_context, Keys, Render, Cursor, Singleton.image_area_ltwh, Singleton.window_resize_last_frame, Singleton.image_horizontal_scroll, Singleton.image_vertical_scroll, Singleton.tool_active, Singleton)
        Singleton.window_resize_last_frame = False
    Render.draw_rectangle(Screen, gl_context, Singleton.image_large_border_ltwh, Singleton.image_large_border_thickness, Singleton.image_large_border_color, True, Singleton.image_large_inside_color, False)
    #
    # update scroll bars
    # vertical scroll
    Singleton.image_vertical_scroll.scroll_area_ltwh[0] = Singleton.image_inside_border_ltwh[0] + Singleton.image_inside_border_ltwh[2] - Singleton.image_vertical_scroll.scroll_area_ltwh[2] + Singleton.image_large_border_thickness
    Singleton.image_vertical_scroll.scroll_area_ltwh[1] = Singleton.image_inside_border_ltwh[1] - Singleton.image_large_border_thickness
    Singleton.image_vertical_scroll.scroll_area_ltwh[3] = Singleton.image_inside_border_ltwh[3] - Singleton.image_horizontal_scroll.scroll_area_ltwh[3] + (3 * Singleton.image_large_border_thickness)
    Singleton.image_vertical_scroll.update(Screen, gl_context, Keys, Render, Cursor)
    # horizontal scroll
    Singleton.image_horizontal_scroll.scroll_area_ltwh[0] = Singleton.image_inside_border_ltwh[0] - Singleton.image_large_border_thickness
    Singleton.image_horizontal_scroll.scroll_area_ltwh[1] = Singleton.image_inside_border_ltwh[1] + Singleton.image_inside_border_ltwh[3] - Singleton.image_horizontal_scroll.scroll_area_ltwh[3] + Singleton.image_large_border_thickness
    Singleton.image_horizontal_scroll.scroll_area_ltwh[2] = Singleton.image_inside_border_ltwh[2] - Singleton.image_vertical_scroll.scroll_area_ltwh[2] + (3 * Singleton.image_large_border_thickness)
    Singleton.image_horizontal_scroll.update(Screen, gl_context, Keys, Render, Cursor)
    # square in image area corner between scroll bars
    Render.basic_rect_ltwh_with_color_to_quad(Screen, gl_context, 'blank_pixel', [Singleton.image_horizontal_scroll.scroll_area_ltwh[0] + Singleton.image_horizontal_scroll.scroll_area_ltwh[2], Singleton.image_horizontal_scroll.scroll_area_ltwh[1], Singleton.image_horizontal_scroll.scroll_area_ltwh[3] - Singleton.image_large_border_thickness, Singleton.image_horizontal_scroll.scroll_area_ltwh[3]], Singleton.image_vertical_scroll.border_color)


def editor_loop(Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor):
    Cursor.add_cursor_this_frame('cursor_arrow')
    if Api.setup_required:
        loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [LOADED_IN_EDITOR], [LOADED_IN_MENU, LOADED_IN_GAME])
        Api.api_initiated_singletons['Editor'] = Api.api_singletons['Editor'](Render, Screen, gl_context, PATH)
        Api.setup_required = False
    #
    Singleton = Api.api_initiated_singletons[Api.current_api]
    update_image(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_palette(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_header(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_footer(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_add_color(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_collision_selector(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_tools(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_tool_attributes(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
