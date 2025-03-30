import pygame
import math
from copy import deepcopy
from Code.utilities import atan2


class Player():
    def __init__(self, PATH: str):
        # collision
        self.ball_collision_image_path: str = f'{PATH}\\Images\\not_always_loaded\\game\\player\\ball_collision.png'
        self.ball_collision_image: pygame.Surface = None
        self.ball_collision_data: dict[tuple[int, int], list[float]] = {}
        self.ball_collisions: dict[tuple[int, int], bool] = {}
        self.ball_collisions_default: dict[tuple[int, int], bool] = self.ball_collisions
        self.ball_width: int = None
        self.ball_width_index: int = None
        self.ball_height: int = None
        self.ball_height_index: int = None
        self.ball_center: float = None
        self.ball_center_index: int = None
        self.ball_left_key: tuple
        self.ball_up_key: tuple
        self.ball_right_key: tuple
        self.ball_down_key: tuple
        self._get_ball_collision()
    #
    def _get_ball_collision(self):
        # load the image
        self.ball_collision_image = pygame.image.load(self.ball_collision_image_path)
        # get width, height, and center
        self.ball_width = self.ball_collision_image.get_width()
        self.ball_width_index = self.ball_width - 1
        self.ball_height = self.ball_collision_image.get_height()
        self.ball_height_index = self.ball_height - 1
        self.ball_center = self.ball_width / 2
        self.ball_center_index = self.ball_width // 2
        # iterate through all pixels to find where ball collision exists
        for index_x in range(self.ball_width):
            for index_y in range(self.ball_height):
                if self.ball_collision_image.get_at((index_x, index_y)) == (0, 0, 0, 255):
                    angle_from_center = atan2((index_x + 0.5 - self.ball_center), -(index_y + 0.5 - self.ball_center))
                    self.ball_collision_data[(index_x, index_y)] = angle_from_center
                    self.ball_collisions[(index_x, index_y)] = False
        # define a default collision to revert active collisions each frame
        self.ball_collisions_default = deepcopy(self.ball_collisions)
        # get keys to ball collision pixels representing certain directions
        self.ball_left_key = (0, self.ball_center_index)
        self.ball_up_key = (self.ball_center_index, 0)
        self.ball_right_key = (self.ball_width_index, self.ball_center_index)
        self.ball_down_key = (self.ball_center_index, self.ball_height_index)
        print(self.ball_left_key, self.ball_up_key, self.ball_right_key, self.ball_down_key)
        print(self.ball_collision_data)