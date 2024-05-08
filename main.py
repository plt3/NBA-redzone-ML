import os
import subprocess
import time

print("Importing Python machine learning libraries, this may take a few seconds...")

import numpy as np
from tensorflow import keras
from tensorflow.keras.preprocessing.image import img_to_array

from ml_models.crop_screenshots import ImageCropper
# TODO: deal with this
# from ml_models.setup_datasets import IMAGE_DIMS
from utils import (choose_main_window_id, choose_space, control_stream_audio,
                   control_stream_overlay, get_chrome_cli_ids,
                   get_window_video_elements, get_windows,
                   let_user_choose_iframe, run_shell, take_screenshot)

IMAGE_DIMS = (200, 320)
FORCE_COMMERCIAL = None


class StreamManager:
    start_delay = 5
    screenshot_tempfile = "nbaredzone_screenshot.jpg"
    model_file_name = "ml_models/part3_cropped.keras"

    def __init__(self):
        # run skhd_process in background for hotkeys to work
        self.skhd_process = subprocess.Popen(["skhd", "-c", "./skhdrc"])
        print("skhd process started.")

        self.during_commercial = False

        self.conv_base = keras.applications.vgg16.VGG16(
            weights="imagenet",
            include_top=False,
            input_shape=IMAGE_DIMS + (3,),
        )
        self.top_model = keras.models.load_model(self.model_file_name)

        self.space = choose_space()
        windows = get_windows(self.space, title=True)
        self.id_dict = get_chrome_cli_ids(windows)

        self.main_id, title = choose_main_window_id(windows)
        print(f'Selected main window with title "{title}" in space {self.space}.')

        self.handle_iframes(windows)

        print(
            "\nSetup done. Make sure space with streams is visible,"
            " or software will not work.\n"
        )

        # TODO: update this with keybinds too (threading)
        self.focused_id = self.main_id

    def __del__(self):
        self.skhd_process.terminate()
        print("skhd process terminated.")
        try:
            os.remove(self.screenshot_tempfile)
            print("Screenshot temp image file removed.")
        except FileNotFoundError:
            pass

    def handle_iframes(self, windows):
        """Can't mute/unmute a page with JavaScript if its video elements are playing
        in iframes due to same-origin policy. Therefore, detect this and let user
        choose a stream that was in an iframe as whole page.
        """
        for win in windows:
            chrome_cli_id = self.id_dict[win["id"]]
            video_obj = get_window_video_elements(chrome_cli_id)

            if not video_obj["has_video"]:
                iframes = video_obj["iframes"]
                title = win["title"].removesuffix(" - Audio playing")

                if len(iframes) == 0:
                    raise Exception(f'No stream found in window with title "{title}"')

                let_user_choose_iframe(title, iframes, chrome_cli_id)

    def fullscreen_window(self, windows, window_id):
        """If in tile view, call without specifying window_id to fullscreen focused window
        (and fullscreen all other windows behind it). If all windows are fullscreened, specify
        window_id of window to bring to front. This will also unmute it and mute previous
        front window.
        """
        for window in windows:
            if not window["fullscreen"]:
                run_shell(f"yabai -m window {window['id']} --toggle zoom-fullscreen")
            if window["id"] == window_id:
                run_shell(f"yabai -m window {window['id']} --focus")
                self.focused_id = window_id
            control_stream_audio(
                self.id_dict[window["id"]], mute=(window["id"] != window_id)
            )

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

    def win_is_commercial(self, win_id, double_check=True, force=None):
        is_fullscreen = None

        if force is not None:
            is_commercial = force  # for testing
        else:
            is_commercial = self.run_classifier_on_screenshot(win_id, double_check)

        return win_id, is_commercial, is_fullscreen

    def switch_away_from_main(self):
        print("switching away from main stream")
        # find non-main window that isn't showing a commercial
        new_id = None
        windows = get_windows(self.space)
        # windows are either all fullscreen or all tiled, so can just check first one
        fullscreen = windows[0]["fullscreen"]
        for win in windows:
            if win["id"] != self.main_id:
                _, is_com, _ = self.win_is_commercial(
                    win["id"], False, force=FORCE_COMMERCIAL
                )
                if not is_com:
                    new_id = win["id"]
                    self.focused_id = new_id
                    break

        if fullscreen:
            if new_id is not None:
                print("fs other stream")
                # fullscreen stream showing game
                self.fullscreen_window(windows, new_id)
            else:
                control_stream_audio(self.id_dict[self.main_id], mute=True)
                control_stream_overlay(self.id_dict[self.main_id], show_overlay=True)
        else:
            print("muting")
            control_stream_audio(self.id_dict[self.main_id], mute=True)
            control_stream_overlay(self.id_dict[self.main_id], show_overlay=True)
            if new_id is not None:
                # switch to stream showing game
                print("switching to other frame")
                control_stream_audio(self.id_dict[new_id], mute=False)

    def return_to_main(self):
        print("returning to main stream")
        windows = get_windows(self.space)
        fullscreen = windows[0]["fullscreen"]

        if fullscreen:
            self.fullscreen_window(windows, self.main_id)
        else:
            control_stream_audio(self.id_dict[self.focused_id], mute=True)
            control_stream_audio(self.id_dict[self.main_id], mute=False)
            control_stream_overlay(self.id_dict[self.main_id], show_overlay=False)
            self.focused_id = self.main_id

    def avoid_main_commercial(self):
        """Switch to other stream for the duration of commercial in main
        stream, then switch back to main stream.
        """
        self.switch_away_from_main()

        is_com = True
        while is_com:
            time.sleep(5)
            _, is_com, _ = self.win_is_commercial(
                self.main_id, False, force=FORCE_COMMERCIAL
            )

        self.return_to_main()

    def handle_if_commercial(self):
        _, commercial, _ = self.win_is_commercial(self.main_id, force=FORCE_COMMERCIAL)
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
