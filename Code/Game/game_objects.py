import pygame
import math
from copy import deepcopy
from Code.utilities import atan2, move_number_to_desired_range
from Code.Game.game_utilities import Map


class Player():
    BALL_WH = 69

    # used for drawing
    PRETTY_BALL_FRONT_REFERENCE = 'player_ball_front'
    PRETTY_BALL_ORDER = 5

    # used for force calculations
    MASS = 1

    # ball must stay in rectangle in center of screen
    MAX_LEFT = 200
    MAX_UP = 100
    MAX_RIGHT = 200
    MAX_DOWN = 100
    BALL_POSITION_ON_SCREEN_SPEED_X = 6 * 60
    BALL_POSITION_ON_SCREEN_SPEED_Y = 3 * 60

    # max velocity in x and y directions
    MAX_VELOCITY_X = 400
    MAX_VELOCITY_Y = 900

    # force applied from movement
    FORCE_MOVEMENT_X = 400
    FORCE_MOVEMENT_Y = 400

    # forces are reset to these values each frame
    DEFAULT_FORCE_GRAVITY_X = 0.0
    DEFAULT_FORCE_GRAVITY_Y = 0.0
    DEFAULT_FORCE_MOVEMENT_X = 0.0
    DEFAULT_FORCE_MOVEMENT_Y = 0.0
    DEFAULT_FORCE_TOOL_X = 0.0
    DEFAULT_FORCE_TOOL_Y = 0.0
    DEFAULT_FORCE_NORMAL_X = 0.0
    DEFAULT_FORCE_NORMAL_Y = 0.0
    DEFAULT_FORCE_WATER_X = 0.0
    DEFAULT_FORCE_WATER_Y = 0.0

    def __init__(self, PATH: str):
        #
        # pathing
        self.player_image_folder_path: str = f'{PATH}\\Images\\not_always_loaded\\game\\player\\'
        self.ball_collision_path: str = 'ball_collision.png'
        #
        # forces
        self.force_gravity_x: float = Player.DEFAULT_FORCE_GRAVITY_X
        self.force_gravity_y: float = Player.DEFAULT_FORCE_GRAVITY_Y
        self.force_movement_x: float = Player.DEFAULT_FORCE_MOVEMENT_X
        self.force_movement_y: float = Player.DEFAULT_FORCE_MOVEMENT_Y
        self.force_tool_x: float = Player.DEFAULT_FORCE_TOOL_X
        self.force_tool_y: float = Player.DEFAULT_FORCE_TOOL_Y
        self.force_normal_x: float = Player.DEFAULT_FORCE_NORMAL_X
        self.force_normal_y: float = Player.DEFAULT_FORCE_NORMAL_Y
        self.force_water_x: float = Player.DEFAULT_FORCE_WATER_X
        self.force_water_y: float = Player.DEFAULT_FORCE_WATER_Y
        self.force_x: float = 0
        self.force_y: float = 0
        #
        # force adjacent
        self.normal_force_angle: int | None = None
        #
        # acceleration, velocity, position
        self.acceleration_x: float = 0
        self.acceleration_y: float = 0
        self.velocity_x: float = 0
        self.velocity_y: float = 0
        self.position_x: float = 0
        self.position_y: float = 0
        self.ball_center_x: float = 0
        self.ball_center_y: float = 0
        #
        # screen position
        self.screen_position_x: float = 0
        self.screen_position_y: float = 0
        self.player_box_left: float = 0
        self.player_box_top: float = 0
        self.player_box_right: float = 0
        self.player_box_bottom: float = 0
        #
        # collision
        self.ball_collision_image: pygame.Surface = None
        self.ball_collision_data: dict[tuple[int, int], tuple[float, float, float]] = {}
        self.ball_collisions: dict[tuple[int, int], bool] = {}
        self.ball_collisions_default: dict[tuple[int, int], bool] = self.ball_collisions
        self.ball_width: int = None
        self.ball_width_index: int = None
        self.ball_height: int = None
        self.ball_height_index: int = None
        self.ball_radius: float = None
        self.ball_center_index: int = None
        self.ball_left_key: tuple
        self.ball_up_key: tuple
        self.ball_right_key: tuple
        self.ball_down_key: tuple
        self._initialize_ball_collision()
        #
        # tools (water jet, grapple, etc)
    #
    def update(self, Singleton, Render, Screen, gl_context, Keys, Cursor, Time):
        self._update_player_controls(Keys)
        self._get_normal_force_angle(Singleton.map)
        self._get_normal_force()
        self._reset_ball_collisions()
        self._calculate_force()
        self._calculate_position(Singleton, Render, Screen, gl_context, Keys, Cursor, Time)
        self._update_screen_position(Singleton.map, Screen, Time)
        self._reset_forces()
        self._draw(Singleton.stored_draws, Render, Screen, gl_context)
    #
    def _update_player_controls(self, Keys):
        if Keys.left.pressed:
            self.force_movement_x = -Player.FORCE_MOVEMENT_X
        if Keys.right.pressed:
            self.force_movement_x = Player.FORCE_MOVEMENT_X
        if Keys.float_up.pressed:
            self.force_movement_y = -Player.FORCE_MOVEMENT_Y
        if Keys.sink_down.pressed:
            self.force_movement_y = Player.FORCE_MOVEMENT_Y
    #
    def _get_normal_force_angle(self, map_object):
        number_of_collisions = 0
        cumulative_x = 0
        cumulative_y = 0
        x_pos, y_pos = round(self.position_x), round(self.position_y)
        for (offset_x, offset_y), (_, cos_angle, sin_angle) in self.ball_collision_data.items():
            # collision may have already been recorded from an object
            if self.ball_collisions[(offset_x, offset_y)]:
                cumulative_x += cos_angle
                cumulative_y += sin_angle
                number_of_collisions += 1
                continue
            # get map collision pixel data
            tile_x, pixel_x = divmod(x_pos+offset_x, Map.TILE_WH)
            tile_y, pixel_y = divmod(y_pos+offset_y, Map.TILE_WH)
            pixel_collision = map_object.tiles[tile_x][tile_y].collision_bytearray[(pixel_y * Map.TILE_WH) + pixel_x]
            # record collisions from the map
            if (pixel_collision == Map.COLLISION) or (pixel_collision == Map.GRAPPLEABLE):
                cumulative_x += cos_angle
                cumulative_y += sin_angle
                number_of_collisions += 1
                continue
        # end the function if there was no collision
        if number_of_collisions == 0:
            self.normal_force_angle = None
            return
        # get the normal force angle
        self.normal_force_angle = round((math.degrees(math.atan2(cumulative_y / number_of_collisions, cumulative_x / number_of_collisions)) - 180) % 360, 2)
    #
    def _get_normal_force(self):
        if self.normal_force_angle is None:
            return
        # normal force from gravity
        if 0.0 <= self.normal_force_angle <= 180.0:
            magnitude_of_gravity = math.sqrt((self.force_gravity_x ** 2) + (self.force_gravity_y ** 2))
            self.force_normal_x += round(math.cos(math.radians(self.normal_force_angle)), 2) * magnitude_of_gravity
            self.force_normal_y += round(math.sin(math.radians(self.normal_force_angle)), 2) * magnitude_of_gravity
        # normal force from impulse
    #
    def _reset_ball_collisions(self):
        self.ball_collisions = deepcopy(self.ball_collisions_default)
    #
    def _calculate_force(self):
        self.force_x = self.force_gravity_x + self.force_movement_x + self.force_tool_x + self.force_normal_x + self.force_water_x
        self.force_y = self.force_gravity_y + self.force_movement_y + self.force_tool_y + self.force_normal_y + self.force_water_y
    #
    def _calculate_position(self, Singleton, Render, Screen, gl_context, Keys, Cursor, Time):
        self.acceleration_x = self.force_x / Player.MASS
        self.acceleration_y = self.force_y / Player.MASS
        initial_velocity_x = self.velocity_x
        initial_velocity_y = self.velocity_y
        self.velocity_x = self.velocity_x + (self.acceleration_x * Time.delta_time)
        self.velocity_y = self.velocity_y + (self.acceleration_y * Time.delta_time)
        self.position_x = ((1 / 2) * (self.velocity_x + initial_velocity_x) * Time.delta_time) + self.position_x
        self.position_y = ((1 / 2) * (self.velocity_y + initial_velocity_y) * Time.delta_time) + self.position_y
        self.ball_center_x = self.position_x + self.ball_radius
        self.ball_center_y = self.position_y + self.ball_radius
    #
    def _update_screen_position(self, Map, Screen, Time):
        # left-right movement
        self.player_box_left = (Screen.width / 2) - Player.MAX_LEFT - self.ball_radius
        self.player_box_right = (Screen.width / 2) + Player.MAX_RIGHT - self.ball_radius
        if Map.reached_left_edge:
            self.screen_position_x = self.position_x
            if self.screen_position_x > self.player_box_left:
                Map.reached_left_edge = False
                Map.offset_x = 0
        elif Map.reached_right_edge:
            self.screen_position_x = Screen.width + self.position_x - Map.map_wh[0]
            if self.screen_position_x < self.player_box_right:
                Map.reached_right_edge = False
                Map.offset_x = Screen.width - Map.map_wh[0]
        if (not Map.reached_left_edge and not Map.reached_right_edge):
            if self.velocity_x < 0:
                self.screen_position_x += Player.BALL_POSITION_ON_SCREEN_SPEED_X * Time.delta_time
            else:
                self.screen_position_x -= Player.BALL_POSITION_ON_SCREEN_SPEED_X * Time.delta_time
            self.screen_position_x = move_number_to_desired_range(self.player_box_left, self.screen_position_x, self.player_box_right)
            Map.offset_x = int(self.screen_position_x - self.position_x)
        # up-down movement
        self.player_box_up = (Screen.height / 2) - Player.MAX_UP - self.ball_radius
        self.player_box_down = (Screen.height / 2) + Player.MAX_DOWN - self.ball_radius
        if Map.reached_top_edge:
            self.screen_position_y = self.position_y
            if self.screen_position_y > self.player_box_up:
                Map.reached_top_edge = False
                Map.offset_y = 0
        elif Map.reached_bottom_edge:
            self.screen_position_y = Screen.height + self.position_y - Map.map_wh[1]
            if self.screen_position_y < self.player_box_down:
                Map.reached_bottom_edge = False
                Map.offset_y = Screen.height - Map.map_wh[1]
        if (not Map.reached_top_edge and not Map.reached_bottom_edge):
            if self.velocity_y < 0:
                self.screen_position_y += Player.BALL_POSITION_ON_SCREEN_SPEED_Y * Time.delta_time
            else:
                self.screen_position_y -= Player.BALL_POSITION_ON_SCREEN_SPEED_Y * Time.delta_time
            self.screen_position_y = move_number_to_desired_range(self.player_box_up, self.screen_position_y, self.player_box_down)
            Map.offset_y = int(self.screen_position_y - self.position_y)
    #
    def _reset_forces(self):
        self.force_gravity_x = Player.DEFAULT_FORCE_GRAVITY_X
        self.force_gravity_y = Player.DEFAULT_FORCE_GRAVITY_Y
        self.force_movement_x = Player.DEFAULT_FORCE_MOVEMENT_X
        self.force_movement_y = Player.DEFAULT_FORCE_MOVEMENT_Y
        self.force_tool_x = Player.DEFAULT_FORCE_TOOL_X
        self.force_tool_y = Player.DEFAULT_FORCE_TOOL_Y
        self.force_normal_x = Player.DEFAULT_FORCE_NORMAL_X
        self.force_normal_y = Player.DEFAULT_FORCE_NORMAL_Y
        self.force_water_x = Player.DEFAULT_FORCE_WATER_X
        self.force_water_y = Player.DEFAULT_FORCE_WATER_Y
    #
    def _draw(self, stored_draws, Render, Screen, gl_context):
        # draw the front of the ball
        Render.store_draw(Player.PRETTY_BALL_FRONT_REFERENCE, Render.basic_rect_ltwh_to_quad, {'object_name': Player.PRETTY_BALL_FRONT_REFERENCE, 'ltwh': [self.screen_position_x, self.screen_position_y, self.ball_width, self.ball_height]})
        stored_draws.add_draw(Player.PRETTY_BALL_FRONT_REFERENCE, Player.PRETTY_BALL_ORDER)
    #
    def _initialize_ball_collision(self):
        # load the image
        self.ball_collision_image = pygame.image.load(f'{self.player_image_folder_path}{self.ball_collision_path}')
        # get width, height, and center
        self.ball_width = self.ball_collision_image.get_width()
        self.ball_width_index = self.ball_width - 1
        self.ball_height = self.ball_collision_image.get_height()
        self.ball_height_index = self.ball_height - 1
        self.ball_radius = self.ball_width / 2
        self.ball_center_index = self.ball_width // 2
        # iterate through all pixels to find where ball collision exists
        for index_x in range(self.ball_width):
            for index_y in range(self.ball_height):
                if self.ball_collision_image.get_at((index_x, index_y)) == (0, 0, 0, 255):
                    angle_from_center = atan2((index_x + 0.5 - self.ball_radius), -(index_y + 0.5 - self.ball_radius))
                    self.ball_collision_data[(index_x, index_y)] = (angle_from_center, math.cos(math.radians(angle_from_center)), math.sin(math.radians(angle_from_center)))
                    self.ball_collisions[(index_x, index_y)] = False
        # define a default collision to revert active collisions each frame
        self.ball_collisions_default = deepcopy(self.ball_collisions)
        # get keys to ball collision pixels representing certain directions
        self.ball_left_key = (0, self.ball_center_index)
        self.ball_up_key = (self.ball_center_index, 0)
        self.ball_right_key = (self.ball_width_index, self.ball_center_index)
        self.ball_down_key = (self.ball_center_index, self.ball_height_index)
