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
from utils import (
    control_stream_audio,
    get_chrome_cli_ids,
    get_focused_space,
    get_window_video_elements,
    get_windows,
    run_shell,
    take_screenshot,
)

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
            input_shape=IMAGE_DIMS + (3,),
        )
        self.top_model = keras.models.load_model(self.model_file_name)

        print(f"Starting in {self.start_delay} seconds. Focus window with main stream.")
        time.sleep(self.start_delay)

        self.space = get_focused_space()
        windows = get_windows(self.space, title=True)
        self.id_dict = get_chrome_cli_ids(windows)

        for win in windows:
            if win["focus"]:
                # TODO: self.main_id won't update with any keybinds now. Need to handle
                self.main_id = win["id"]
                title = win["title"].removesuffix(" - Audio playing")
                print(
                    f'Found main window with title "{title}" in space'
                    f" {self.space}. You may now switch away if desired."
                )
                break
        else:
            raise Exception(
                "No window with focus found, so unable to determine main stream."
            )

        self.handle_iframes(windows)

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
        for win in windows:
            video_obj = get_window_video_elements(self.id_dict[win["id"]])
            if not video_obj["has_video"]:
                title = win["title"].removesuffix(" - Audio playing")
                if len(video_obj["iframes"]) == 0:
                    raise Exception(f'No stream found in window with title "{title}"')
                print(
                    "No HTML video elements found in window with title"
                    f' "{title}". Try one of these iframes found on the page:\n'
                )
                for index, iframe in enumerate(video_obj["iframes"]):
                    print(f"{index + 1}. {iframe}")
                # TODO: handle input and make nicer UI?
                iframe_choice = int(input("\nEnter a number: "))
                run_shell(
                    f'brave-cli open {video_obj["iframes"][iframe_choice-1]}'
                    f' -t {self.id_dict[win["id"]]}'
                )

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
        # find non-main, non placeholder window that isn't showing a commercial
        new_id = None
        windows = get_windows(self.space)
        # windows are either all fullscreen or all tiled, so can just check first one
        fullscreen = windows[0]["fullscreen"]
        for win in windows:
            if win["id"] != self.main_id and win["id"] not in self.placeholder_ids:
                _, is_com, _ = self.win_is_commercial(win["id"], False, force=False)
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
        else:
            print("muting")
            control_stream_audio(self.id_dict[self.main_id], mute=True)
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
            self.focused_id = self.main_id

    def avoid_main_commercial(self):
        """Switch to other stream/placeholder for the duration of commercial in main
        stream, then switch back to main stream.
        """
        self.switch_away_from_main()

        is_com = True
        while is_com:
            time.sleep(5)  # TOOD: in practice this might be shorter than normal?
            # don't double check when already on commercial
            _, is_com, _ = self.win_is_commercial(self.main_id, False, force=False)

        self.return_to_main()

    def handle_if_commercial(self):
        _, commercial, _ = self.win_is_commercial(self.main_id, force=True)
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
