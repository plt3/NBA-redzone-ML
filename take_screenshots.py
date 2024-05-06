import json
import os
import subprocess
import sys
import time
from datetime import datetime

from utils import take_screenshot

"""
Take screenshots of windows in given space that are displaying streams at regular interval
in order to get data for ML model.

Press ctrl + c to stop
"""

FILE_EXTENSION = "jpg"
SCREENSHOT_INTERVAL = 60
DATA_DIRECTORY = 'screenshots'


def get_window_ids(space):
    command = f"yabai -m query --windows --space {space}"
    result = subprocess.run(command.split(), capture_output=True, text=True, check=True)
    windows = json.loads(result.stdout)

    if len(windows) not in [1, 4]:
        raise Exception(
            "Must have 1 or 4 windows open in space. If not 4 streams, open up blank windows to take up space."
        )
    else:
        stream_window_ids = []

        for window in windows:
            if 'NBA' in window['title']:
                print(f'Assuming stream in window with title "{window['title']}".')
                stream_window_ids.append(window['id'])
            else:
                stream_response = input(f'Does window "{window['title']}" contain a stream? y/[n]: ')
                if stream_response == 'y':
                    print(f'Adding window with title "{window['title']}" to streams list.')
                    stream_window_ids.append(window['id'])

        return stream_window_ids


def main():
    if len(sys.argv) < 2:
        print(f"USAGE: python3 {sys.argv[0]} SPACE_NUMBER")
    else:
        ids = get_window_ids(sys.argv[1])
        os.makedirs(DATA_DIRECTORY, exist_ok=True)
        print(f'Starting to take screenshots in {SCREENSHOT_INTERVAL} seconds. Switch to space {sys.argv[1]} now.')

        while True:
            time.sleep(SCREENSHOT_INTERVAL)
            for id in ids:
                filename = f'{datetime.now().strftime("%y-%m-%d_%H-%M-%S")}_{id}.{FILE_EXTENSION}'
                file_path = os.path.join(DATA_DIRECTORY, filename)
                take_screenshot(id, DATA_DIRECTORY)
                print(f"Took screenshot {file_path}")


if __name__ == "__main__":
    main()
