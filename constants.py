# for manage_streams.py
MODEL_FILE_PATH = "ml_models/part5_cropped_5-29-24.keras"
DEFAULT_PORT = 80
DEFAULT_UPDATE_RATE = 3
# when making request to start halftime, stop classification for 15 minutes
HALFTIME_DURATION = 15 * 60

# for take_screenshots.py
FILE_EXTENSION = "jpg"
SCREENSHOT_INTERVAL = 60
DATA_DIRECTORY = "screenshots"

# for label_screenshots.py
GAME_CLASS = "game"
COMMERCIAL_CLASS = "com"
UNSORTED_DATA_DIRECTORY = "screenshots"
SORTED_DATA_DIRECTORY = "sorted_screenshots"
