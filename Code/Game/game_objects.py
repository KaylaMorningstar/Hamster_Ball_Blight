import pygame
import math
from copy import deepcopy
from Code.utilities import atan2, move_number_to_desired_range, difference_between_angles, angle_in_range
from Code.Game.game_utilities import Map, get_vector_magnitude_in_direction, get_xy_vector_components
from bresenham import bresenham


# slopes
# friction
# low speeds seem to not move the player
# screen movement should be revised
# certain player movement should disallow on_a_slope and bouncing_low
# ball twitches when player pushes against walls
# tools
# force the player to stay inside the map
# slopes with low speeds don't work


class Player():
    # collision vs no collision
    NO_COLLISION = 0
    COLLISION = 1

    # states
    BALLISTIC = 0

    # ball size
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

    # attrbiutes dictating how velocity should behave
    MAX_VELOCITY_X = 900
    MAX_VELOCITY_Y = 900
    ANGLE_FOR_IMPULSE = 20
    STOP_BOUNCING_SPEED = 150
    FLAT_GROUND = 10
    MINIMUM_SLOPE_ANGLE = 1.5
    MAX_PIXEL_OFFSET_FROM_SLOPES = 10
    MIN_PIXEL_OFFSET_FROM_SLOPES = 2
    MOTION_RELATIVE_TO_NORMAL_ANGLE = 80

    # force applied from movement
    FORCE_MOVEMENT_X = 600
    FORCE_MOVEMENT_Y = 600
    AIRBORNE_FORCE_MOVEMENT_X = 500
    MIN_FORCE_MOVEMENT_X = 300
    MAX_MOVEMENT_ANGLE = 90

    # elasticity for the normal force
    MAX_ELASTICITY = 1.0
    MIN_ELASTICITY = 0.35

    # forces are reset to these values each frame
    DEFAULT_FORCE_GRAVITY_X = 0.0
    DEFAULT_FORCE_GRAVITY_Y = 400.0
    DEFAULT_FORCE_MOVEMENT_X = 0.0
    DEFAULT_FORCE_MOVEMENT_Y = 0.0
    DEFAULT_FORCE_TOOL_X = 0.0
    DEFAULT_FORCE_TOOL_Y = 0.0
    DEFAULT_FORCE_NORMAL_X = 0.0
    DEFAULT_FORCE_NORMAL_Y = 0.0
    DEFAULT_FORCE_WATER_X = 0.0
    DEFAULT_FORCE_WATER_Y = 0.0

    def set_gravity(self, gravity_x: float | None = None, gravity_y: float | None = None):
        if gravity_x is not None:
            Player.DEFAULT_FORCE_GRAVITY_X = gravity_x
            self.force_gravity_x = gravity_x
        if gravity_x is not None:
            Player.DEFAULT_FORCE_GRAVITY_Y = gravity_y
            self.force_gravity_y = gravity_y
        self.gravity_angle = math.degrees(math.atan2(-self.force_gravity_y, self.force_gravity_x)) % 360
        self.normal_force_lower_angle = (((self.gravity_angle - 180) % 360) - 90) % 360
        self.normal_force_upper_angle = (((self.gravity_angle - 180) % 360) + 90) % 360
    #
    def __init__(self, PATH: str):
        #
        # state
        self.last_state: int = Player.BALLISTIC
        self.state: int = Player.BALLISTIC
        self.collision_status: int = Player.NO_COLLISION
        self.on_a_slope: bool = False
        self.exit_slope: bool = False
        self.bouncing_low: bool = False
        #
        # pathing
        self.player_image_folder_path: str = f'{PATH}\\Images\\not_always_loaded\\game\\player\\'
        self.inner_ball_collision_path: str = 'inner_ball_collision.png'
        self.outer_ball_collision_path: str = 'outer_ball_collision.png'
        #
        # force adjacent
        self.normal_force_lower_angle: float
        self.normal_force_upper_angle: float
        self.gravity_angle: float
        self.normal_force_angle: float | None = None
        self.angle_of_motion: float | None = None
        #
        # forces
        self.set_gravity(gravity_x=Player.DEFAULT_FORCE_GRAVITY_X, gravity_y=Player.DEFAULT_FORCE_GRAVITY_Y)
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
        self.force_x: float = 0.0
        self.force_y: float = 0.0
        #
        # acceleration, velocity, position
        self.acceleration_x: float = 0.0
        self.acceleration_y: float = 0.0
        self.velocity_x: float = 0.0
        self.velocity_y: float = 0.0
        self.velocity: float = 0.0
        self.last_position_x: float = 0.0
        self.last_position_y: float = 0.0
        self.position_x: float = 1700.0
        self.position_y: float = 900.0
        self.ball_center_x: float = 0.0
        self.ball_center_y: float = 0.0
        #
        # screen position
        self.screen_position_x: float = 0.0
        self.screen_position_y: float = 0.0
        self.player_box_left: float = 0.0
        self.player_box_top: float = 0.0
        self.player_box_right: float = 0.0
        self.player_box_bottom: float = 0.0
        #
        # inner collision
        self.inner_ball_collision_image: pygame.Surface | None = None
        self.inner_ball_collision_data: dict[tuple[int, int], tuple[float, float, float]] = {}
        self.inner_ball_collisions: dict[tuple[int, int], bool] = {}
        self.inner_ball_collisions_default: dict[tuple[int, int], bool] = self.inner_ball_collisions
        # outer collision
        self.outer_ball_collision_image: pygame.Surface | None = None
        self.outer_ball_collision_data: dict[tuple[int, int], tuple[float, float, float]] = {}
        self.outer_ball_collisions: dict[tuple[int, int], bool] = {}
        self.outer_ball_collisions_default: dict[tuple[int, int], bool] = self.outer_ball_collisions
        #
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
        self.last_state = self.state
        self.last_position_x = self.position_x
        self.last_position_y = self.position_y
        self._get_normal_force_angle(Singleton.map)
        self._update_player_controls(Keys)
        self._get_normal_force(Time)
        self._reset_ball_collisions()
        self._calculate_force()
        self._calculate_position(Singleton, Render, Screen, gl_context, Keys, Cursor, Time)
        self._update_screen_position(Singleton.map, Screen, Time)
        self._readout(Time)
        self._reset_forces()
        self._draw(Singleton.stored_draws, Render, Screen, gl_context)
    #
    def _update_player_controls(self, Keys):
        if self.on_a_slope and self.normal_force_angle is not None:
            if Keys.left.pressed:
                angle_of_movement = self.normal_force_angle + 180 - Player.MOTION_RELATIVE_TO_NORMAL_ANGLE
                normal_gravity_angle_difference = min(abs(difference_between_angles(self.normal_force_angle + 180, self.gravity_angle)), Player.MAX_MOVEMENT_ANGLE)
                force_movement = max(Player.FORCE_MOVEMENT_X * math.cos(math.radians(normal_gravity_angle_difference)), Player.MIN_FORCE_MOVEMENT_X)
                self.force_movement_x = force_movement * math.cos(math.radians(angle_of_movement))
                self.force_movement_y = -force_movement * math.sin(math.radians(angle_of_movement))
            if Keys.right.pressed:
                angle_of_movement = self.normal_force_angle + 180 + Player.MOTION_RELATIVE_TO_NORMAL_ANGLE
                normal_gravity_angle_difference = min(abs(difference_between_angles(self.normal_force_angle + 180, self.gravity_angle)), Player.MAX_MOVEMENT_ANGLE)
                force_movement = max(Player.FORCE_MOVEMENT_X * math.cos(math.radians(normal_gravity_angle_difference)), Player.MIN_FORCE_MOVEMENT_X)
                self.force_movement_x = force_movement * math.cos(math.radians(angle_of_movement))
                self.force_movement_y = -force_movement * math.sin(math.radians(angle_of_movement))
            if Keys.float_up.pressed:
                self.force_movement_y = -Player.FORCE_MOVEMENT_Y
            if Keys.sink_down.pressed:
                self.force_movement_y = Player.FORCE_MOVEMENT_Y
        else:
            if Keys.left.pressed:
                self.force_movement_x = -Player.AIRBORNE_FORCE_MOVEMENT_X
            if Keys.right.pressed:
                self.force_movement_x = Player.AIRBORNE_FORCE_MOVEMENT_X
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
        for (offset_x, offset_y), (_, cos_angle, sin_angle) in self.outer_ball_collision_data.items():
            # collision may have already been recorded from an object
            if self.outer_ball_collisions[(offset_x, offset_y)]:
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
            self.collision_status = Player.NO_COLLISION
            return
        # get the normal force angle
        self.collision_status = Player.COLLISION
        self.normal_force_angle = round((math.degrees(math.atan2(cumulative_y / number_of_collisions, cumulative_x / number_of_collisions)) - 180) % 360, 2)
    #
    def _get_normal_force(self, Time):
        # no normal force if the ball is undergoing ballistic motion
        if self.normal_force_angle is None:
            return
        # on a slope, bouncing low, and final angle of motion
        if self.angle_of_motion is not None:
            # Fdt = mdv
            # check whether the ball is on a sloped

            self.on_a_slope = (((abs(90 - (difference_between_angles(self.angle_of_motion, self.normal_force_angle) % 180)) <= Player.ANGLE_FOR_IMPULSE) or  # direction of movement roughly matches the angle of the slope
                               (self.velocity * math.cos(math.radians(abs(difference_between_angles(self.angle_of_motion, self.gravity_angle)))) < Player.STOP_BOUNCING_SPEED)) and  # ball isn't moving with the slope, but it is moving slowly
                               not self.exit_slope)
            self.bouncing_low = ((self.velocity * math.cos(math.radians(abs(difference_between_angles(self.angle_of_motion, self.gravity_angle)))) < Player.STOP_BOUNCING_SPEED) and  # velocity is low in the direction of gravity
                                 abs(difference_between_angles(self.gravity_angle + 180, self.normal_force_angle)) < Player.FLAT_GROUND and  # ground is roughly flat in relation to gravity
                                 not self.exit_slope)
            # get the angle the ball will be moving after collision
            # if the ball is roughly on a slope, then snap the ball to the slope
            if self.on_a_slope:
                slope_angle1 = (self.normal_force_angle + 90) % 360
                slope_angle2 = (self.normal_force_angle - 90) % 360
                if abs(difference_between_angles(self.angle_of_motion, slope_angle1)) <= 90:
                    resulting_angle = slope_angle1
                elif abs(difference_between_angles(self.angle_of_motion, slope_angle2)) <= 90:
                    resulting_angle = slope_angle2
            # if the ball is bouncing without much speed, then snap the ball to the ground
            elif self.bouncing_low:
                slope_angle1 = (self.normal_force_angle + 90) % 360
                slope_angle2 = (self.normal_force_angle - 90) % 360
                if abs(difference_between_angles(self.angle_of_motion, slope_angle1)) <= 90:
                    resulting_angle = slope_angle1
                elif abs(difference_between_angles(self.angle_of_motion, slope_angle2)) <= 90:
                    resulting_angle = slope_angle2
            # normal impulse collision
            else:
                resulting_angle = self._reflect_angle(self.normal_force_angle, (self.angle_of_motion + 180) % 360)
        # normal force from gravity
        if angle_in_range(self.normal_force_lower_angle, self.normal_force_angle, self.normal_force_upper_angle):
            magnitude_of_gravity = math.sqrt((self.force_gravity_x ** 2) + (self.force_gravity_y ** 2))
            self.force_normal_x += magnitude_of_gravity * round(math.cos(math.radians(self.normal_force_angle)), 2)
            self.force_normal_y += magnitude_of_gravity * -round(math.sin(math.radians(self.normal_force_angle)), 2)
        # normal force from player movement
        if ((self.force_movement_x != 0) or (self.force_movement_y != 0)):
            force_of_movement_angle = math.degrees(math.atan2(-self.force_movement_y, self.force_movement_x)) % 360
            # force of movement must oppose the normal force angle to contribute to the normal force
            if abs(difference_between_angles(force_of_movement_angle, self.normal_force_angle + 180)) <= 90:
                magnitude_of_movement = math.sqrt((self.force_movement_x ** 2) + (self.force_movement_y ** 2))
                movement_force_multiplier = math.cos(math.radians(difference_between_angles(force_of_movement_angle, self.normal_force_angle)))
                magnitude_normal_force_from_movement = abs(magnitude_of_movement * movement_force_multiplier)
                self.force_normal_x += magnitude_normal_force_from_movement * round(math.cos(math.radians(self.normal_force_angle)), 2)
                self.force_normal_y += magnitude_normal_force_from_movement * -round(math.sin(math.radians(self.normal_force_angle)), 2)
        # force from impulse
        if self.angle_of_motion is not None:
            if abs(difference_between_angles(self.angle_of_motion, self.normal_force_angle + 180)) <= 90:
                # calculate elasticity
                elasticity = self._calculate_elasticity(self.angle_of_motion, resulting_angle)
                # calculate the final velocity in x and y directions
                if self.on_a_slope or self.bouncing_low:
                    # calculate a multiplier to only get the velocity in the direction of the slope
                    speed_multiplier_angle = abs(difference_between_angles(self.angle_of_motion, resulting_angle))
                    speed_multiplier_angle = speed_multiplier_angle if speed_multiplier_angle > Player.MINIMUM_SLOPE_ANGLE else 0.0
                    final_speed_multiplier = math.cos(math.radians(speed_multiplier_angle))
                    # calculate x-y velocity
                    final_velocity = self.velocity * final_speed_multiplier * elasticity
                    final_velocity_x = final_velocity * math.cos(math.radians(resulting_angle))
                    final_velocity_y = -final_velocity * math.sin(math.radians(resulting_angle))
                else:
                    # calculate x-y velocity
                    final_velocity = self.velocity * elasticity
                    final_velocity_x = final_velocity * math.cos(math.radians(resulting_angle))
                    final_velocity_y = -final_velocity * math.sin(math.radians(resulting_angle))
                # add the impulse to the normal force
                self.force_normal_x += Player.MASS * (final_velocity_x - self.velocity_x) / Time.delta_time
                self.force_normal_y += Player.MASS * (final_velocity_y - self.velocity_y) / Time.delta_time
    #
    def _reset_ball_collisions(self):
        self.inner_ball_collisions = deepcopy(self.inner_ball_collisions_default)
        self.outer_ball_collisions = deepcopy(self.outer_ball_collisions_default)
    #
    def _calculate_force(self):
        self.force_x = self.force_gravity_x + self.force_movement_x + self.force_tool_x + self.force_normal_x + self.force_water_x
        self.force_y = self.force_gravity_y + self.force_movement_y + self.force_tool_y + self.force_normal_y + self.force_water_y
    #
    def _calculate_position(self, Singleton, Render, Screen, gl_context, Keys, Cursor, Time):
        # get where the ball would be if it were unimpeded by walls or objects
        self.exit_slope = False
        self.acceleration_x = self.force_x / Player.MASS
        self.acceleration_y = self.force_y / Player.MASS
        initial_velocity_x = self.velocity_x
        initial_velocity_y = self.velocity_y
        self.velocity_x = move_number_to_desired_range(-Player.MAX_VELOCITY_X, self.velocity_x + (self.acceleration_x * Time.delta_time), Player.MAX_VELOCITY_X)
        self.velocity_y = move_number_to_desired_range(-Player.MAX_VELOCITY_Y, self.velocity_y + (self.acceleration_y * Time.delta_time), Player.MAX_VELOCITY_Y)
        self.velocity = math.sqrt((self.velocity_x ** 2) + (self.velocity_y ** 2))
        self.angle_of_motion = None if self.velocity == 0.0 else math.degrees(math.atan2(-self.velocity_y, self.velocity_x)) % 360
        unimpeded_position_x = ((1 / 2) * (self.velocity_x + initial_velocity_x) * Time.delta_time) + self.position_x
        unimpeded_position_y = ((1 / 2) * (self.velocity_y + initial_velocity_y) * Time.delta_time) + self.position_y

        # condition if no collision was detected last frame
        if self.collision_status == Player.NO_COLLISION:
            unimpeded_position_x = ((1 / 2) * (self.velocity_x + initial_velocity_x) * Time.delta_time) + self.position_x
            unimpeded_position_y = ((1 / 2) * (self.velocity_y + initial_velocity_y) * Time.delta_time) + self.position_y
            previous_offset_x = round(self.position_x)
            previous_offset_y = round(self.position_y)
            collision_encountered = False
            for (offset_x, offset_y) in bresenham(round(self.position_x), round(self.position_y), round(unimpeded_position_x), round(unimpeded_position_y)):
                _, number_of_collisions = self._get_ball_collisions(Singleton.map, offset_x, offset_y, inner=True)
                if number_of_collisions > 0:
                    self.position_x = previous_offset_x
                    self.position_y = previous_offset_y
                    collision_encountered = True
                    break
                previous_offset_x = offset_x
                previous_offset_y = offset_y
            if not collision_encountered:
                # check if the outer ball has collisions
                _, number_of_collisions = self._get_ball_collisions(Singleton.map, offset_x, offset_y, inner=False)
                # if no outer ball collisions, then put the ball at its unimpeded position
                if number_of_collisions == 0:
                    self.position_x = unimpeded_position_x
                    self.position_y = unimpeded_position_y
                # if outer ball collisions, then snap ball to collisions
                else:
                    collision_encountered = True
                    self.position_x = round(unimpeded_position_x)
                    self.position_y = round(unimpeded_position_y)

        # condition if a collision was detected last frame
        if self.collision_status == Player.COLLISION:
            unimpeded_position_x = (self.velocity_x * Time.delta_time) + self.position_x
            unimpeded_position_y = (self.velocity_y * Time.delta_time) + self.position_y

            # position calculation when not on a slope
            if not self.on_a_slope:
                previous_offset_x = round(self.position_x)
                previous_offset_y = round(self.position_y)
                collision_encountered = False
                for (offset_x, offset_y) in bresenham(round(self.position_x), round(self.position_y), round(unimpeded_position_x), round(unimpeded_position_y)):
                    _, number_of_collisions = self._get_ball_collisions(Singleton.map, offset_x, offset_y, inner=True)
                    if number_of_collisions > 0:
                        self.position_x = previous_offset_x
                        self.position_y = previous_offset_y
                        collision_encountered = True
                        break
                    previous_offset_x = offset_x
                    previous_offset_y = offset_y
                if not collision_encountered:
                    # check if the outer ball has collisions
                    _, number_of_collisions = self._get_ball_collisions(Singleton.map, offset_x, offset_y, inner=False)
                    # if no outer ball collisions, then put the ball at its unimpeded position
                    if number_of_collisions == 0:
                        self.position_x = unimpeded_position_x
                        self.position_y = unimpeded_position_y
                    # if outer ball collisions, then snap ball to collisions
                    else:
                        collision_encountered = True
                        self.position_x = round(unimpeded_position_x)
                        self.position_y = round(unimpeded_position_y)
            
            if self.on_a_slope:
                exit_slope = False
                new_position_x = self.position_x
                new_position_y = self.position_y
                normal_angle_cos = math.cos(math.radians(self.normal_force_angle))
                normal_angle_sin = math.sin(math.radians(self.normal_force_angle))
                max_slope_offset_x = Player.MAX_PIXEL_OFFSET_FROM_SLOPES * normal_angle_cos
                max_slope_offset_y = - Player.MAX_PIXEL_OFFSET_FROM_SLOPES * normal_angle_sin
                min_slope_offset_x = - Player.MIN_PIXEL_OFFSET_FROM_SLOPES * normal_angle_cos
                min_slope_offset_y = Player.MIN_PIXEL_OFFSET_FROM_SLOPES * normal_angle_sin
                # check points from the current position to the next unimpeded position
                for (unimpeded_x_pos, unimpeded_y_pos) in bresenham(round(self.position_x), round(self.position_y), round(unimpeded_position_x), round(unimpeded_position_y)):
                    # allow for slight offsets in the direction of the normal force to allow for the ball to stay on the slope
                    for (x_pos, y_pos) in bresenham(round(unimpeded_x_pos + min_slope_offset_x), round(unimpeded_y_pos + min_slope_offset_y), round(unimpeded_x_pos + max_slope_offset_x), round(unimpeded_y_pos + max_slope_offset_y)):
                        valid, on_a_slope, normal_angle = self._validate_offset_position_on_slope(Singleton.map, x_pos, y_pos)
                        # ball has been impeded by a collision
                        if not valid:
                            print('s1', (x_pos, y_pos), (round(unimpeded_x_pos + min_slope_offset_x), round(unimpeded_y_pos + min_slope_offset_y)), (round(unimpeded_x_pos + max_slope_offset_x), round(unimpeded_y_pos + max_slope_offset_y)))
                            continue
                        # exit slope if there's no collision with the ball's final valid position
                        if not on_a_slope:
                            print('s2', (x_pos, y_pos), (round(unimpeded_x_pos + min_slope_offset_x), round(unimpeded_y_pos + min_slope_offset_y)), (round(unimpeded_x_pos + max_slope_offset_x), round(unimpeded_y_pos + max_slope_offset_y)))
                            exit_slope = True
                            new_position_x = x_pos
                            new_position_y = y_pos - 1
                            break
                        # exit slope if there is a collision on the ball's final valid position, but the angle between motion and the slope is too different
                        if abs(abs(difference_between_angles(self.angle_of_motion, normal_angle)) - 90) >= Player.ANGLE_FOR_IMPULSE:
                            print('s3', (x_pos, y_pos), (round(unimpeded_x_pos + min_slope_offset_x), round(unimpeded_y_pos + min_slope_offset_y)), (round(unimpeded_x_pos + max_slope_offset_x), round(unimpeded_y_pos + max_slope_offset_y)))
                            exit_slope = True
                            new_position_x = x_pos
                            new_position_y = y_pos
                            break
                        # ball position is valid and ball is still attached to the slope
                        print('s4', (x_pos, y_pos), (round(unimpeded_x_pos + min_slope_offset_x), round(unimpeded_y_pos + min_slope_offset_y)), (round(unimpeded_x_pos + max_slope_offset_x), round(unimpeded_y_pos + max_slope_offset_y)))
                        exit_slope = False
                        new_position_x = x_pos
                        new_position_y = y_pos
                        break
                print('frame', exit_slope)
                self.exit_slope = exit_slope
                self.position_x = new_position_x
                self.position_y = new_position_y

        # recalculate where the center of the ball is
        self.ball_center_x = self.position_x + self.ball_radius
        self.ball_center_y = self.position_y + self.ball_radius
    #
    def _update_screen_position(self, Map, Screen, Time):
        # left-right movement
        self.player_box_left = (Screen.width // 2) - Player.MAX_LEFT - math.floor(self.ball_radius)
        self.player_box_right = (Screen.width // 2) + Player.MAX_RIGHT - math.floor(self.ball_radius)
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
            if abs(self.velocity_x) > 50:
                if self.velocity_x < 0:
                    self.screen_position_x += Player.BALL_POSITION_ON_SCREEN_SPEED_X * Time.delta_time
                else:
                    self.screen_position_x -= Player.BALL_POSITION_ON_SCREEN_SPEED_X * Time.delta_time
            self.screen_position_x = move_number_to_desired_range(self.player_box_left, self.screen_position_x, self.player_box_right)
            Map.offset_x = round(self.screen_position_x - self.position_x)
        # up-down movement
        self.player_box_up = (Screen.height // 2) - Player.MAX_UP - math.floor(self.ball_radius)
        self.player_box_down = (Screen.height // 2) + Player.MAX_DOWN - math.floor(self.ball_radius)
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
            if abs(self.velocity_y) > 50:
                if self.velocity_y < 0:
                    self.screen_position_y += Player.BALL_POSITION_ON_SCREEN_SPEED_Y * Time.delta_time
                else:
                    self.screen_position_y -= Player.BALL_POSITION_ON_SCREEN_SPEED_Y * Time.delta_time
            self.screen_position_y = move_number_to_desired_range(self.player_box_up, self.screen_position_y, self.player_box_down)
            Map.offset_y = round(self.screen_position_y - self.position_y)
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
        Render.store_draw(Player.PRETTY_BALL_FRONT_REFERENCE, Render.basic_rect_ltwh_to_quad, {'object_name': Player.PRETTY_BALL_FRONT_REFERENCE, 'ltwh': [round(self.screen_position_x), round(self.screen_position_y), self.ball_width, self.ball_height]})
        stored_draws.add_draw(Player.PRETTY_BALL_FRONT_REFERENCE, Player.PRETTY_BALL_ORDER)
    #
    def _initialize_ball_collision(self):
        # load the images
        self.inner_ball_collision_image = pygame.image.load(f'{self.player_image_folder_path}{self.inner_ball_collision_path}')
        self.outer_ball_collision_image = pygame.image.load(f'{self.player_image_folder_path}{self.outer_ball_collision_path}')
        # get width, height, and center
        self.ball_width = self.inner_ball_collision_image.get_width()
        self.ball_width_index = self.ball_width - 1
        self.ball_height = self.inner_ball_collision_image.get_height()
        self.ball_height_index = self.ball_height - 1
        self.ball_radius = self.ball_width / 2
        self.ball_center_index = self.ball_width // 2
        # iterate through all pixels to find where ball collision exists
        # inner
        for index_x in range(self.ball_width):
            for index_y in range(self.ball_height):
                if self.inner_ball_collision_image.get_at((index_x, index_y)) == (0, 0, 0, 255):
                    angle_from_center = atan2((index_x + 0.5 - self.ball_radius), -(index_y + 0.5 - self.ball_radius))
                    self.inner_ball_collision_data[(index_x, index_y)] = (angle_from_center, math.cos(math.radians(angle_from_center)), math.sin(math.radians(angle_from_center)))
                    self.inner_ball_collisions[(index_x, index_y)] = False
        # outer
        for index_x in range(self.outer_ball_collision_image.get_width()):
            for index_y in range(self.outer_ball_collision_image.get_height()):
                if self.outer_ball_collision_image.get_at((index_x, index_y)) == (0, 0, 0, 255):
                    angle_from_center = atan2((index_x + 0.5 - self.ball_radius - 1), -(index_y + 0.5 - self.ball_radius - 1))
                    self.outer_ball_collision_data[(index_x - 1, index_y - 1)] = (angle_from_center, math.cos(math.radians(angle_from_center)), math.sin(math.radians(angle_from_center)))
                    self.outer_ball_collisions[(index_x - 1, index_y - 1)] = False
        # define a default collision to revert active collisions each frame
        self.inner_ball_collisions_default = deepcopy(self.inner_ball_collisions)
        self.outer_ball_collisions_default = deepcopy(self.outer_ball_collisions)
        # get keys to ball collision pixels representing certain directions
        self.ball_left_key = (0, self.ball_center_index)
        self.ball_up_key = (self.ball_center_index, 0)
        self.ball_right_key = (self.ball_width_index, self.ball_center_index)
        self.ball_down_key = (self.ball_center_index, self.ball_height_index)
    #
    @staticmethod
    def _reflect_angle(angle_of_reflection, angle_being_reflected):
        difference_between_angles = abs(angle_being_reflected - angle_of_reflection)
        if difference_between_angles == 0.0:
            return angle_of_reflection
        elif angle_being_reflected > angle_of_reflection:
            return (angle_being_reflected - (2 * difference_between_angles)) % 360
        else:
            return (angle_being_reflected + (2 * difference_between_angles)) % 360
    #
    def _calculate_elasticity(self, angle1, angle2):
        angle_difference = abs(difference_between_angles(angle1, angle2))
        elasticity_scale = abs((angle_difference / 180) - 1)
        elasticity = (elasticity_scale * Player.MAX_ELASTICITY) + ((1 - elasticity_scale) * Player.MIN_ELASTICITY)
        return elasticity
    #
    def _get_ball_collisions(self, Map, x_pos: int, y_pos: int, inner: bool):
        # checking inner vs. outer ball collisions
        if inner:
            ball_collisions = deepcopy(self.inner_ball_collisions_default)
        else:
            ball_collisions = deepcopy(self.outer_ball_collisions_default)
        number_of_collisions = 0
        for (offset_x, offset_y) in ball_collisions.keys():
            # get map collision pixel data
            tile_x, pixel_x = divmod(x_pos+offset_x, Map.TILE_WH)
            tile_y, pixel_y = divmod(y_pos+offset_y, Map.TILE_WH)
            pixel_collision = Map.tiles[tile_x][tile_y].collision_bytearray[(pixel_y * Map.TILE_WH) + pixel_x]
            # record collisions from the map
            if (pixel_collision == Map.COLLISION) or (pixel_collision == Map.GRAPPLEABLE):
                number_of_collisions += 1
                ball_collisions[(offset_x, offset_y)] = True
                continue
        return ball_collisions, number_of_collisions
    #
    def _validate_offset_position_on_slope(self, collision_map, x_pos, y_pos):
        valid = True
        on_a_slope = True
        normal_angle = 0.0

        # inner ball
        for (offset_x, offset_y), (_, cos_angle, sin_angle) in self.inner_ball_collision_data.items():
            # collision may have already been recorded from an object
            if self.inner_ball_collisions[(offset_x, offset_y)]:
                valid = False
                return valid, on_a_slope, normal_angle
            # get map collision pixel data
            tile_x, pixel_x = divmod(x_pos+offset_x, Map.TILE_WH)
            tile_y, pixel_y = divmod(y_pos+offset_y, Map.TILE_WH)
            pixel_collision = collision_map.tiles[tile_x][tile_y].collision_bytearray[(pixel_y * Map.TILE_WH) + pixel_x]
            # record collisions from the map
            if (pixel_collision == Map.COLLISION) or (pixel_collision == Map.GRAPPLEABLE):
                valid = False
                return valid, on_a_slope, normal_angle

        # outer ball
        number_of_collisions = 0
        cumulative_x = 0
        cumulative_y = 0
        for (offset_x, offset_y), (_, cos_angle, sin_angle) in self.outer_ball_collision_data.items():
            # collision may have already been recorded from an object
            if self.outer_ball_collisions[(offset_x, offset_y)]:
                cumulative_x += cos_angle
                cumulative_y += sin_angle
                number_of_collisions += 1
                continue
            # get map collision pixel data
            tile_x, pixel_x = divmod(x_pos+offset_x, Map.TILE_WH)
            tile_y, pixel_y = divmod(y_pos+offset_y, Map.TILE_WH)
            pixel_collision = collision_map.tiles[tile_x][tile_y].collision_bytearray[(pixel_y * Map.TILE_WH) + pixel_x]
            # record collisions from the map
            if (pixel_collision == Map.COLLISION) or (pixel_collision == Map.GRAPPLEABLE):
                cumulative_x += cos_angle
                cumulative_y += sin_angle
                number_of_collisions += 1
                continue
        # end the function if there was no collision
        if number_of_collisions == 0:
            on_a_slope = False
            return valid, on_a_slope, normal_angle
        # get the normal force angle
        normal_angle = round((math.degrees(math.atan2(cumulative_y / number_of_collisions, cumulative_x / number_of_collisions)) - 180) % 360, 2)
        return valid, on_a_slope, normal_angle
    #
    def _readout(self, Time):
        return
        print(f"{(self.force_x, self.force_y)=}")
        print(f"{(self.force_gravity_x, self.force_gravity_y)=}")
        print(f"{(self.force_movement_x, self.force_movement_y)=}")
        print(f"{(self.force_normal_x, self.force_normal_y)=}")
        print(f"{(self.velocity_x, self.velocity_y)=}")
        print(f"{(self.position_x, self.position_y)=}")
        print(200 * '-')