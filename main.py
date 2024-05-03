import os
import subprocess
import time

from utils import get_windows, run_shell


class StreamManager:
    start_delay = 5

    def __init__(self):
        # run skhd_process in background for hotkeys to work
        self.skhd_process = subprocess.Popen(["skhd", "-c", "./skhdrc"])
        print("skhd process started.")

        self.placeholder_uri = "file:///" + os.path.join(os.getcwd(), "README.md")

    def __del__(self):
        self.skhd_process.terminate()
        print("skhd process terminated.")

    def add_placeholder_windows(self, windows):
        """Open extra windows to always have 1 or 4 windows open in space"""
        win_cmd = f"open -a 'Brave Browser.app' -n --args --new-window --app={self.placeholder_uri}"

        if len(windows) in [2, 3]:
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

    def mainloop(self):
        try:
            print(
                f"Starting in {self.start_delay} seconds. Switch to space with streams now."
            )
            time.sleep(self.start_delay)
            windows = get_windows()
            self.add_placeholder_windows(windows)
            while True:
                pass
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")


def main():
    manager = StreamManager()
    manager.mainloop()


if __name__ == "__main__":
    main()
