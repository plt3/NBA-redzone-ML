import numpy as np
from setup_datasets import IMAGE_DIMS, get_datasets
from tensorflow import keras
from tensorflow.keras.preprocessing.image import img_to_array, load_img
from tqdm import tqdm

# model_file_name = "part5_cropped_5-29-24.keras"
model_file_name = "part3_cropped_5-29-24.keras"

_, _, test_dataset = get_datasets()
test_model = keras.models.load_model(model_file_name)


conv_base = keras.applications.vgg16.VGG16(
    weights="imagenet", include_top=False, input_shape=(IMAGE_DIMS[0], IMAGE_DIMS[1], 3)
)

corrects = 0
fps = 0
fns = 0
total = len(test_dataset.file_paths)
for image_path in tqdm(test_dataset.file_paths):
    img = load_img(image_path, target_size=IMAGE_DIMS)
    img_arr = img_to_array(img)
    img_arr = np.array([img_arr])

    # pred = test_model.predict(img_arr, verbose=0)

    inp = keras.applications.vgg16.preprocess_input(img_arr)
    features = conv_base.predict(inp, verbose=0)
    pred = test_model.predict(features, verbose=0)

    if "_game" in image_path:
        if pred[0][0] >= 0.5:
            corrects += 1
        else:
            fns += 1
            print(f"FN: {image_path}")
    elif "_com" in image_path:
        if pred[0][0] < 0.5:
            corrects += 1
        else:
            fps += 1
            print(f"FP: {image_path}")

print(f"{corrects}/{total} correct: {round(corrects/total * 100, 2)}%")
print(
    f"{fps}/{total - corrects} false positives/errors, {round(fps/(total-corrects) * 100, 2)}%"
)
print(
    f"{fns}/{total - corrects} false negatives/errors, {round(fns/(total-corrects) * 100, 2)}%"
)
