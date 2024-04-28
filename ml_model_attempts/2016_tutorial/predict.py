import random

import numpy as np
from keras import applications
from keras.preprocessing import image
from keras.saving import load_model

# from trainmodel.py
# classifier = load_model("model_part1.keras")

# from part2
# classifier = load_model("model_part2.keras")
# model1 = applications.VGG16(include_top=False, weights="imagenet")

classifier = load_model("model_part3.keras")

total = 1000
corrects = 0
fps = 0
fns = 0

eval_files = [
    f"../data/evaluation/{label_type}/{label_type}_{num}.jpg"
    for label_type in range(2)
    for num in range(500)
]
random.shuffle(eval_files)

for i in range(total):
    file_name = eval_files[i]
    if file_name.startswith("../data/evaluation/1/1_"):
        is_food = True
    elif file_name.startswith("../data/evaluation/0/0_"):
        is_food = False
    else:
        print(f"{file_name}: uh ohhhhh")
        break

    test_image = image.load_img(file_name, target_size=(200, 200))
    test_image = image.img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)

    # FOR PREDICTING MODEL FROM trainmodel.py or part3.py
    # is this bc classifier.predict expects to do multiple predictions? So it makes an
    # array of arrays
    result = classifier.predict(test_image, verbose=0)

    # FOR PREDICTING MODEL FROM part2.py
    # features = model1.predict(test_image, verbose=0)
    # result = classifier.predict(features, verbose=0)

    # training_set.class_indices
    # if result[0][0] == 1:
    if result[0][0] > 0.98:
        if is_food:
            corrects += 1
        else:
            fps += 1
            print(f"FP: {file_name}")
    else:
        if not is_food:
            corrects += 1
        else:
            fns += 1
            print(f"FN: {file_name}")
    if i % 100 == 0:
        print(i)

print(f"{corrects}/{total} correct, {round(corrects/total * 100, 2)}%")
print(
    f"{fps}/{total - corrects} false positives/errors, {round(fps/(total-corrects) * 100, 2)}%"
)
print(
    f"{fns}/{total - corrects} false negatives/errors, {round(fns/(total-corrects) * 100, 2)}%"
)
