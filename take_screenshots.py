import os
import sys
import time
from datetime import datetime

from constants import DATA_DIRECTORY, FILE_EXTENSION, SCREENSHOT_INTERVAL
from utils import get_windows, strip_win_title, take_screenshot

"""
Take screenshots of windows in given space that are displaying streams at regular interval
in order to get data for ML model.

Press ctrl + c to stop
"""


class ScreenshotTaker:
    def __init__(
        self,
        space: int,
        interval: int = SCREENSHOT_INTERVAL,
        print_windows: bool = False,
        ignore_ids: list[int] = [],
    ) -> None:
        self.space = space
        self.interval = interval
        self.windows: list[dict] = []
        for win in get_windows(self.space, title=True):
            if win["id"] not in ignore_ids:
                self.windows.append(win)

        if print_windows:
            plural = ""
            if len(self.windows) > 1:
                plural = "s"
            print(f"Taking screenshots of the following window{plural}:")
            for win in self.windows:
                print(strip_win_title(win["title"]))
        os.makedirs(DATA_DIRECTORY, exist_ok=True)

    def take_screenshots(self) -> None:
        print(
            f"Collecting screenshots of all windows in space {self.space} to train classifier."
        )

        try:
            while True:
                time.sleep(self.interval)
                for win in self.windows:
                    win_id = win["id"]
                    filename = f'{datetime.now().strftime("%y-%m-%d_%H-%M-%S")}_{win_id}.{FILE_EXTENSION}'
                    file_path = os.path.join(DATA_DIRECTORY, filename)

                    take_screenshot(win_id, file_path)
                    print(f"Took screenshot {file_path} for classifier training.")
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"USAGE: python3 {sys.argv[0]} SPACE_NUMBER")
    else:
        sc_taker = ScreenshotTaker(int(sys.argv[1]), print_windows=True)
        sc_taker.take_screenshots()
