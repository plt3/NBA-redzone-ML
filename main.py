import os
import subprocess
import time

import numpy as np
from tensorflow import keras
from tensorflow.keras.preprocessing.image import img_to_array

from manage_windows import fullscreen_window
from ml_models.crop_screenshots import ImageCropper

# TODO: deal with this
# from ml_models.setup_datasets import IMAGE_DIMS
from utils import get_windows, notify, run_shell, take_screenshot, toggle_mute

IMAGE_DIMS = (200, 320)


class StreamManager:
    start_delay = 5
    screenshot_tempfile = "nbaredzone_screenshot.jpg"
    model_file_name = "ml_models/part3_cropped.keras"

    def __init__(self):
        # run skhd_process in background for hotkeys to work
        self.skhd_process = subprocess.Popen(["skhd", "-c", "./skhdrc"])
        print("skhd process started.")

        self.placeholder_file = "placeholder.jpg"
        self.placeholder_uri = "file:///" + os.path.join(
            os.getcwd(), self.placeholder_file
        )
        self.placeholder_ids = []
        self.during_commercial = False

        self.conv_base = keras.applications.vgg16.VGG16(
            weights="imagenet",
            include_top=False,
            input_shape=(IMAGE_DIMS[0], IMAGE_DIMS[1], 3),
        )
        self.top_model = keras.models.load_model(self.model_file_name)

        print(
            f"Starting in {self.start_delay} seconds. Focus window with main stream,"
            " and make sure to mute all other windows with ctrl + m."
        )
        time.sleep(self.start_delay)

        for win in get_windows(title=True):
            if win["focus"]:
                self.main_id = win["id"]
                print(f"Found main window with title {win['title']}")
                break

        self.add_placeholder_windows()

    def __del__(self):
        self.skhd_process.terminate()
        print("skhd process terminated.")
        try:
            os.remove(self.screenshot_tempfile)
        except FileNotFoundError:
            pass

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

        run_shell(f"yabai -m window {self.main_id} --focus")

    def run_classifier_on_screenshot(self, win_id, double_check_commercials=True):
        start = time.time()
        take_screenshot(win_id, self.screenshot_tempfile)
        before_classify = time.time()
        cropper = ImageCropper(self.screenshot_tempfile)
        try:
            img = cropper.crop_image(resize_dims=(IMAGE_DIMS[1], IMAGE_DIMS[0]))
        except Exception as e:
            print(e)
            # use uncropped image as input if error cropping
            img = cropper.img.resize((IMAGE_DIMS[1], IMAGE_DIMS[0]))
        img_arr = img_to_array(img)
        img_arr = np.array([img_arr])
        input = keras.applications.vgg16.preprocess_input(img_arr)
        features = self.conv_base.predict(input, verbose=0)
        prediction = self.top_model.predict(features, verbose=0)
        done = time.time()
        res_str = f"{round(before_classify - start, 2)}s to take sc, {round(done - before_classify, 2)} to classify"

        if prediction[0][0] <= 0.5:
            print(f"looks like commercial. {res_str}")
            if double_check_commercials:
                print("Double checking:")
                time.sleep(3)
                return self.run_classifier_on_screenshot(win_id, False)
            return True
        else:
            print(f"looks like NBA. {res_str}")
            return False

    def win_is_commercial(self, win_id=None, double_check=True, force=None):
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

        if force is not None:
            is_commercial = force  # for testing
        else:
            is_commercial = self.run_classifier_on_screenshot(win_id, double_check)

        return win_id, is_commercial, is_fullscreen

    def switch_away_from_main(self):
        print("switching away from main stream")
        # find non-main, non placeholder window that isn't showing a commercial
        new_id = None
        windows = get_windows()
        # windows are either all fullscreen or all tiled, so can just check first one
        fullscreen = windows[0]["fullscreen"]
        for win in windows:
            if win["id"] != self.main_id and win["id"] not in self.placeholder_ids:
                _, is_com, _ = self.win_is_commercial(win["id"], False)
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
                # switch to stream showing game
                print("switching to other frame")
                run_shell(f"yabai -m window {new_id} --focus")
                toggle_mute()

    def return_to_main(self):
        print("returning to main stream")
        windows = get_windows()
        focused_id = None
        for win in windows:
            if win["focus"]:
                focused_id = win["id"]
                break
        fullscreen = windows[0]["fullscreen"]
        from_placeholder = focused_id in self.placeholder_ids

        if fullscreen:
            fullscreen_window(
                windows, window_id=self.main_id, from_placeholder=from_placeholder
            )
        else:
            toggle_mute()
            if focused_id != self.main_id:
                run_shell(f"yabai -m window {self.main_id} --focus")
                toggle_mute()

    def avoid_main_commercial(self):
        """Switch to other stream/placeholder for the duration of commercial in main
        stream, then switch back to main stream.
        """
        self.switch_away_from_main()

        is_com = True
        while is_com:
            time.sleep(5)  # TOOD: in practice this might be shorter than normal?
            # don't double check when already on commercial
            _, is_com, _ = self.win_is_commercial(self.main_id, False)

        self.return_to_main()

    def handle_if_commercial(self):
        _, commercial, _ = self.win_is_commercial()
        if commercial:
            self.avoid_main_commercial()

    def mainloop(self):
        try:
            while True:
                time.sleep(5)
                self.handle_if_commercial()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")


def main():
    manager = StreamManager()
    manager.mainloop()


if __name__ == "__main__":
    main()
