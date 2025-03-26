# import pygame



# def create_text_file_and_add_data(path: str, data: list[bytearray | str]):
#     with open(path, "wb") as file:
#         for line in data:
#             if isinstance(line, bytearray):
#                 file.write(line)
#             elif isinstance(line, str):
#                 file.write(line.encode(CollisionMode.UTF_8))


# def get_bytearray(path: str):
#     with open(path, mode='rb') as file:
#         return bytearray(file.read())


# class CollisionMode:
#     UTF_8 = 'utf-8'
#     NEW_LINE = '\n'

#     NO_COLLISION = 0
#     COLLISION = 1
#     GRAPPLEABLE = 2
#     PLATFORM = 3
#     WATER = 4

#     NO_COLLISION_BINARY = b'\x00'
#     COLLISION_BINARY = b'\x01'
#     GRAPPLEABLE_BINARY = b'\x02'
#     PLATFORM_BINARY = b'\x03'
#     WATER_BINARY = b'\x04'

#     NO_COLLISION_BYTEARRAY = bytearray(b'\x00')
#     COLLISION_BYTEARRAY = bytearray(b'\x01')
#     GRAPPLEABLE_BYTEARRAY = bytearray(b'\x02')
#     PLATFORM_BYTEARRAY = bytearray(b'\x03')
#     WATER_BYTEARRAY = bytearray(b'\x04')


#     path = "C:\\Users\\Kayle\\Desktop\\Blight\\Hamster_Ball_Blight\\Projects\\Project1\\Level2\\"
#     data_path = path + "text_file"
#     png_path = path + 't0_0.png'
#     image = bytearray(pygame.image.tobytes(pygame.image.load(png_path), "RGBA"))
#     create_text_file_and_add_data(data_path, [CollisionMode.NO_COLLISION_BYTEARRAY+CollisionMode.COLLISION_BYTEARRAY, CollisionMode.NEW_LINE, image])
#     final_file = get_bytearray(data_path)
#     print('s1', final_file)
#     raise Exception



if __name__ == '__main__':
    #
    # pathing
    import os
    PATH = os.getcwd()
    #
    # initialize time and keys
    from Code.application_setup import application_setup
    Time, Keys, Cursor = application_setup()
    Cursor.set_cursor_visibility(False)
    #
    # initialize visuals
    from Code.drawing_functions import initialize_display
    Screen, Render, gl_context = initialize_display()
    #
    # load permanently loaded images
    from Code.utilities import IMAGE_PATHS, loading_and_unloading_images_manager, ALWAYS_LOADED
    loading_and_unloading_images_manager(Screen, Render, gl_context, IMAGE_PATHS, [ALWAYS_LOADED], [])
    #
    # initialize Api
    from Code.application_setup import ApiObject
    Api = ApiObject(Render)
    #
    # game loop
    from Code.application_loop import application_loop
    application_loop(Api, PATH, Screen, gl_context, Render, Time, Keys, Cursor)