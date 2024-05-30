import os
import time

print("Importing Python machine learning libraries, this may take a few seconds...")

import numpy as np
from tensorflow import keras
from tensorflow.keras.preprocessing.image import img_to_array

from ml_models.crop_screenshots import ImageCropper
from utils import take_screenshot

# TODO: deal with this being in multiple places
IMAGE_DIMS = (200, 320)


class Classifier:
    def __init__(
        self,
        model_file_path: str,
        screenshot_tempfile: str = "nbaredzone_screenshot.jpg",
    ) -> None:
        self.screenshot_tempfile = screenshot_tempfile
        self.model_file_path = model_file_path
        self.model = keras.models.load_model(self.model_file_path)

    def __del__(self) -> None:
        try:
            os.remove(self.screenshot_tempfile)
            print("Screenshot temp image file removed.")
        except FileNotFoundError:
            pass

    def classify(self, win_id: int, double_check_commercials: bool = True) -> bool:
        """Return whether window with given ID is displaying a commercial"""
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
        prediction = self.model.predict(img_arr, verbose=0)
        done = time.time()
        res_str = f"{round(before_classify - start, 2)}s to take sc, {round(done - before_classify, 2)} to classify"

        if prediction[0][0] <= 0.5:
            print(f"looks like commercial. {res_str}")
            if double_check_commercials:
                print("Double checking:")
                time.sleep(3)
                return self.classify(win_id, False)
            return True
        else:
            print(f"looks like NBA. {res_str}")
            return False
