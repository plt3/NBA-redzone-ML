import os
import subprocess
import time

from manage_windows import fullscreen_window
from utils import get_windows, notify, run_shell, toggle_mute


class StreamManager:
    start_delay = 5

    def __init__(self):
        # run skhd_process in background for hotkeys to work
        self.skhd_process = subprocess.Popen(["skhd", "-c", "./skhdrc"])
        print("skhd process started.")

        self.placeholder_file = "placeholder.jpg"
        self.placeholder_uri = "file:///" + os.path.join(
            os.getcwd(), self.placeholder_file
        )
        self.placeholder_ids = []

    def __del__(self):
        self.skhd_process.terminate()
        print("skhd process terminated.")

    def add_placeholder_windows(self):
        """Open extra windows to always have 1 or 4 windows open in space"""
        win_cmd = f"open -a 'Brave Browser.app' -n --args --new-window --app={self.placeholder_uri}"
        windows = get_windows(title=True)

        if len(windows) in [2, 3]:
            notify(
                "Adding placeholder windows to have 4 windows in space. Adjust if necessary."
            )

        while len(windows) in [2, 3]:
            run_shell(win_cmd)

            if len(windows) == 2:
                not_focused_id = None
                for win in windows:
                    if not win["focus"]:
                        not_focused_id = win["id"]
                        break

                time.sleep(0.5)
                run_shell(f"yabai -m window {not_focused_id} --focus")
                time.sleep(0.5)
                run_shell(win_cmd)

            time.sleep(0.5)
            windows = get_windows(title=True)

        for win in windows:
            if self.placeholder_file in win["title"]:
                self.placeholder_ids.append(win["id"])

    def win_is_commercial(self, win_id=None, force=True):
        is_fullscreen = None

        # use focused window if no win_id specified
        if win_id is None:
            for win in get_windows():
                if win["focus"]:
                    win_id = win["id"]
                    is_fullscreen = win["fullscreen"]
                    break
            if win_id is None:
                raise Exception("No focused window found.")

        # placeholder for now, always returns force. In future, should put image
        # classifying code here
        is_commercial = force

        return win_id, is_commercial, is_fullscreen

    def avoid_commercial(self, win_id, fullscreen):
        # find different, non placeholder window that isn't showing a commercial
        new_id = None
        windows = get_windows(title=True)
        for win in windows:
            if win["id"] != win_id and self.placeholder_file not in win["title"]:
                _, is_com, _ = self.win_is_commercial(win["id"])
                if not is_com:
                    new_id = win["id"]
                    break

        if fullscreen:
            if new_id is not None:
                print("fs other stream")
                # fullscreen stream showing game
                fullscreen_window(windows, new_id)
            else:
                # fullscreen placeholder if no streams showing games
                if len(self.placeholder_ids) > 0:
                    print("fs placeholder")
                    fullscreen_window(windows, self.placeholder_ids[0])
                else:
                    toggle_mute()
        else:
            print("changing mute")
            toggle_mute()
            if new_id is not None:
                print("switching to other frame")
                run_shell(f"yabai -m window {new_id} --focus")
                toggle_mute()

    def handle_if_commercial(self):
        win_id, commercial, fullscreen = self.win_is_commercial()
        if commercial:
            self.avoid_commercial(win_id, fullscreen)

    def mainloop(self):
        try:
            print(
                f"Starting in {self.start_delay} seconds. Switch to space with streams now."
            )
            time.sleep(self.start_delay)
            self.add_placeholder_windows()
            while True:
                time.sleep(5)
                print("handling")
                self.handle_if_commercial()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")


def main():
    manager = StreamManager()
    manager.mainloop()


if __name__ == "__main__":
    main()
