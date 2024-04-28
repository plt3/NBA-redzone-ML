import random

import numpy as np
from keras.preprocessing import image
from keras.saving import load_model

classifier = load_model("model.keras")

total = 1000
corrects = 0
fps = 0
fns = 0


for i in range(total):
    one_or_zero = random.choice([0, 1])
    num = random.randint(0, 499)
    test_image = image.load_img(
        f"evaluation/{one_or_zero}/{one_or_zero}_{num}.jpg", target_size=(200, 200)
    )
    test_image = image.img_to_array(test_image)
    test_image = np.expand_dims(test_image, axis=0)
    result = classifier.predict(test_image, verbose=0)
    # training_set.class_indices
    if result[0][0] == 1:
        if one_or_zero == 1:
            corrects += 1
        else:
            fps += 1
    else:
        if one_or_zero == 0:
            corrects += 1
        else:
            fns += 1
    if i % 100 == 0:
        print(i)

print(f"{corrects}/{total} correct, {round(corrects/total * 100, 2)}%")
print(
    f"{fps}/{total - corrects} false positives/errors, {round(fps/(total-corrects) * 100, 2)}%"
)
print(
    f"{fns}/{total - corrects} false negatives/errors, {round(fns/(total-corrects) * 100, 2)}%"
)
