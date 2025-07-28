if __name__ == '__main__':
    #
    # pathing
    import os
    PATH = os.getcwd()
    #
    # initialize visuals
    from Code.drawing_functions import initialize_display
    Screen, Render, gl_context = initialize_display()
    #
    # initialize time and keys
    from Code.application_setup import application_setup
    Time, Keys, Cursor = application_setup(Render)
    Cursor.set_cursor_visibility(False)
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