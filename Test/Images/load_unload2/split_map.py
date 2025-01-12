from PIL import Image


FILE_LOCATION = "C:\\Users\\Kayle\\Desktop\\Hamster_Ball_Blight\\Test\\Images\\load_unload2\\Forest.png"
TILE_WIDTH = 256
TILE_HEIGHT = 256

IMAGE = Image.open(FILE_LOCATION)
IMAGE_WIDTH, IMAGE_HEIGHT = IMAGE.size

ROWS = (IMAGE_WIDTH // TILE_WIDTH)
COLUMNS = (IMAGE_HEIGHT // TILE_HEIGHT)


for row_index in range(ROWS):
    for column_index in range(COLUMNS):
        
        left = row_index * TILE_WIDTH
        top = column_index * TILE_HEIGHT
        right = min((row_index + 1) * TILE_WIDTH, IMAGE_WIDTH)
        bottom = min((column_index + 1) * TILE_HEIGHT, IMAGE_HEIGHT)

        tile = IMAGE.crop((left, top, right, bottom))
        tile.save(f"t{row_index}_{column_index}.png")
