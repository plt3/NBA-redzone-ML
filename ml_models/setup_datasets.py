import os

import matplotlib.pyplot as plt
import splitfolders
from crop_screenshots import ImageCropper
from keras.api.utils import image_dataset_from_directory
from tqdm import tqdm

INPUT_DIR = "../sorted_screenshots"
OUTPUT_DIR = "model_data"
IMAGE_DIMS = (200, 320)


def create_model_data(crop: bool = False) -> None:
    if not os.path.exists(OUTPUT_DIR):
        splitfolders.ratio(
            INPUT_DIR,
            output=OUTPUT_DIR,
            ratio=(0.64, 0.16, 0.2),
            group_prefix=None,
            move=False,
        )
    if crop:
        for path, _, files in os.walk(OUTPUT_DIR):
            for file in tqdm(files):
                if file.endswith(".jpg"):
                    img_path = os.path.join(path, file)
                    cropper = ImageCropper(img_path)
                    try:
                        cropper.save_cropped_image(
                            True, True, (IMAGE_DIMS[1], IMAGE_DIMS[0]), img_path
                        )
                    except Exception as e:
                        if file not in str(e):
                            print(e, file)
                        else:
                            print(e)


def get_datasets() -> tuple:
    # returns tuple of training, validation, and testing datasets
    return_list = []
    for ds_type in ["train", "val", "test"]:
        return_list.append(
            image_dataset_from_directory(
                os.path.join(OUTPUT_DIR, ds_type),
                image_size=IMAGE_DIMS,
                color_mode="rgb",
                batch_size=32,
                shuffle=True,
            )
        )
    return tuple(return_list)


def view_dataset(dataset) -> None:
    plt.figure(figsize=(10, 10))
    for images, _ in dataset.take(1):
        for i in range(9):
            plt.subplot(3, 3, i + 1)
            plt.imshow(images[i].numpy().astype("uint8"))
            plt.axis("off")
    plt.show()


def main() -> None:
    create_model_data(True)


if __name__ == "__main__":
    main()
