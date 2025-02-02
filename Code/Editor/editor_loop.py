import math
import random
from copy import deepcopy
from Code.utilities import rgba_to_glsl, percent_to_rgba, COLORS, get_text_height, get_text_width, point_is_in_ltwh, IMAGE_PATHS, loading_and_unloading_images_manager, get_rect_minus_borders, round_scaled, LOADED_IN_EDITOR, OFF_SCREEN, move_number_to_desired_range, get_time, switch_to_base10, base10_to_hex, add_characters_to_front_of_string
from Code.Editor.editor_update import update_palette, update_header, update_footer, update_tools, update_add_color, update_tool_attributes
from Code.Editor.editor_utilities import TextInput, CurrentlySelectedColor, HeaderManager, ScrollBar, EditorMap
from Code.Editor.editor_utilities import EditorTool, MarqueeRectangleTool, LassoTool, PencilTool, EraserTool, SprayTool, HandTool, BucketTool, LineTool, CurvyLineTool, EmptyRectangleTool, FilledRectangleTool, EmptyEllipseTool, FilledEllipseTool, BlurTool, JumbleTool, EyedropTool


class EditorSingleton():
    def __init__(self, Render, Screen, gl_context, PATH):
        self.editor_enabled = True
        self.border_color = COLORS['BLACK']
        #
        # header
        self.header_text_pixel_color = COLORS['BLACK']
        self.header_background_color = COLORS['PINK']
        self.header_highlight_color = (COLORS['YELLOW'][0], COLORS['YELLOW'][1], COLORS['YELLOW'][2], COLORS['YELLOW'][3] * 0.5)
        self.header_selected_color = COLORS['YELLOW']
        self.header_border_color = COLORS['WHITE']
        self.header_border_thickness = 25
        self.header_strings = ['File', 'Edit', 'Options', 'Objects', 'Blocks']
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
            'File': HeaderManager(Render,
                                  option_names_and_responses={'New project': lambda: print('a'),
                                                              'New level': lambda: print('a'),
                                                              'Save level': lambda: print('b'),
                                                              'Main menu': lambda: print('c'),
                                                              'Exit game': lambda: print('d'),},
                                  text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[0][0], top = self.header_height),

            'Edit': HeaderManager(Render,
                                  option_names_and_responses={'Undo': lambda: print('e'),
                                                              'Paste': lambda: print('f'),
                                                              'Rotate': lambda: print('g'),
                                                              'Replace color': lambda: print('h'),
                                                              'Flip': lambda: print('i'),},
                                  text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[1][0], top = self.header_height),

            'Options': HeaderManager(Render,
                                     option_names_and_responses={'Play level': lambda: print('j'),
                                                                 'Toggle map': lambda: print('k'),
                                                                 'Show grid': lambda: print('l'),},
                                     text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[2][0], top = self.header_height),

            'Objects': HeaderManager(Render,
                                     option_names_and_responses={'Object': lambda: print('m'),},
                                     text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[3][0], top = self.header_height),

            'Blocks': HeaderManager(Render,
                                    option_names_and_responses={'Block': lambda: print('n'),},
                                    text_pixel_size = 3, padding = self.header_manager_padding, padding_between_items = self.header_manager_padding_between_items, border_thickness = self.header_manager_border_thickness, text_color = COLORS['BLACK'], background_color = COLORS['GREEN'], highlighted_background_color = COLORS['YELLOW'], edge_color = COLORS['BLUE'], left = self.header_hover_ltwh[4][0], top = self.header_height),
            }
        self.header_bottom = self.header_height + self.header_border_thickness
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
                                           (deepcopy(EraserTool.NAME), deepcopy(EraserTool.INDEX)),
                                           (deepcopy(SprayTool.NAME), deepcopy(SprayTool.INDEX)),
                                           (deepcopy(HandTool.NAME), deepcopy(HandTool.INDEX)),
                                           (deepcopy(BucketTool.NAME), deepcopy(BucketTool.INDEX)),
                                           (deepcopy(LineTool.NAME), deepcopy(LineTool.INDEX)),
                                           (deepcopy(CurvyLineTool.NAME), deepcopy(CurvyLineTool.INDEX)),
                                           (deepcopy(EmptyRectangleTool.NAME), deepcopy(EmptyRectangleTool.INDEX)),
                                           (deepcopy(FilledRectangleTool.NAME), deepcopy(FilledRectangleTool.INDEX)),
                                           (deepcopy(EmptyEllipseTool.NAME), deepcopy(EmptyEllipseTool.INDEX)),
                                           (deepcopy(FilledEllipseTool.NAME), deepcopy(FilledEllipseTool.INDEX)),
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
        Singleton.map.update(Api, Screen, gl_context, Keys, Render, Cursor, Singleton.image_area_ltwh, Singleton.window_resize_last_frame, Singleton.image_horizontal_scroll, Singleton.image_vertical_scroll, Singleton.tool_active, Singleton.currently_selected_color.color)
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
        loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [LOADED_IN_EDITOR], [])
        Api.api_initiated_singletons['Editor'] = Api.api_singletons['Editor'](Render, Screen, gl_context, PATH)
        Api.setup_required = False
    #
    Singleton = Api.api_initiated_singletons[Api.current_api]
    update_image(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_palette(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_header(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_footer(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_add_color(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_tools(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    update_tool_attributes(Singleton, Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)
    