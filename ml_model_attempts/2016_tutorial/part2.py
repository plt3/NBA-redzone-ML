import numpy as np
from keras import applications
from keras.layers import Dense, Dropout, Flatten
from keras.models import Sequential
from tensorflow.keras.preprocessing.image import ImageDataGenerator

"""
This hits 92% on food/not food lets gooooo
"""

# dimensions of our images.
img_width, img_height = 200, 200

top_model_weights_path = "model_part2.keras"
train_data_dir = "../data/training"
validation_data_dir = "../data/validation"
nb_train_samples = 2984
nb_validation_samples = 1000
epochs = 50
batch_size = 16


def save_bottlebeck_features():
    datagen = ImageDataGenerator(rescale=1.0 / 255)

    # build the VGG16 network
    model = applications.VGG16(include_top=False, weights="imagenet")

    generator = datagen.flow_from_directory(
        train_data_dir,
        target_size=(img_width, img_height),
        batch_size=batch_size,
        class_mode=None,
        shuffle=False,
    )
    print(
        f"DEBUGPRINT[4]: part2.py:70 (before bottleneck_features_train = model.predic…)"
    )
    bottleneck_features_train = model.predict(
        generator,
    )
    print(
        f"DEBUGPRINT[1]: part2.py:74 (before np.save(open(bottleneck_features_train.n…)"
    )
    np.save("bottleneck_features_train.npy", bottleneck_features_train)

    generator = datagen.flow_from_directory(
        validation_data_dir,
        target_size=(img_width, img_height),
        batch_size=batch_size,
        class_mode=None,
        shuffle=False,
    )
    print(
        f"DEBUGPRINT[3]: part2.py:84 (before bottleneck_features_validation = model.p…)"
    )
    bottleneck_features_validation = model.predict(
        generator,
    )
    print(f"DEBUGPRINT[2]: part2.py:88 (before np.save()")
    np.save("bottleneck_features_validation.npy", bottleneck_features_validation)


def train_top_model():
    train_data = np.load("bottleneck_features_train.npy")
    train_labels = np.array(
        [0] * (nb_train_samples // 2) + [1] * (nb_train_samples // 2)
    )

    validation_data = np.load("bottleneck_features_validation.npy")
    validation_labels = np.array(
        [0] * (nb_validation_samples // 2) + [1] * (nb_validation_samples // 2)
    )

    model = Sequential()
    model.add(Flatten(input_shape=train_data.shape[1:]))
    model.add(Dense(256, activation="relu"))
    model.add(Dropout(0.5))
    model.add(Dense(1, activation="sigmoid"))

    model.compile(optimizer="rmsprop", loss="binary_crossentropy", metrics=["accuracy"])

    model.fit(
        train_data,
        train_labels,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(validation_data, validation_labels),
    )
    model.save(top_model_weights_path)


save_bottlebeck_features()
train_top_model()
