from keras.layers import Activation, Conv2D, Dense, Dropout, Flatten, MaxPooling2D
from keras.models import Sequential
from tensorflow.keras.preprocessing.image import ImageDataGenerator

# literally all lifted from https://stackoverflow.com/questions/57309958/one-class-classification-using-keras-and-python
# gets 82% accuracy on evaluation data which I think is already pretty good. Could try
# changing model to one that is pre-built maybe? Idk. Also fix all 100000 warnings about
# batch size etc. lol
# also got 85% on 3000 training examples (1500 food, 1500 not food) and 25 epochs

# turns out this is all from https://blog.keras.io/building-powerful-image-classification-models-using-very-little-data.html
classifier = Sequential()

classifier.add(Conv2D(32, (3, 3), input_shape=(200, 200, 3), activation="relu"))
classifier.add(MaxPooling2D(pool_size=(2, 2)))

classifier.add(Conv2D(32, (3, 3), activation="relu"))
classifier.add(MaxPooling2D(pool_size=(2, 2)))

classifier.add(Conv2D(64, (3, 3), activation="relu"))
classifier.add(MaxPooling2D(pool_size=(2, 2)))

classifier.add(Flatten())

classifier.add(Dense(units=64, activation="relu"))

classifier.add(Dropout(0.5))

# output layer
classifier.add(Dense(1))
classifier.add(Activation("sigmoid"))


# TODO: SO poster changed to SGD instead of Adam? Probably won't make much difference
classifier.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])

train_datagen = ImageDataGenerator(
    rescale=1.0 / 255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1.0 / 255)

batch_size = 16

training_set = train_datagen.flow_from_directory(
    "training/",
    target_size=(200, 200),
    batch_size=batch_size,
    class_mode="binary",
    shuffle=True,
)

test_set = test_datagen.flow_from_directory(
    "validation/",
    target_size=(200, 200),
    batch_size=batch_size,
    class_mode="binary",
    shuffle=True,
)

# history = classifier.fit_generator(
classifier.fit(
    training_set,
    # steps_per_epoch=1000,
    steps_per_epoch=2000 // batch_size,
    epochs=50,
    validation_data=test_set,
    validation_steps=800 // batch_size,
)

classifier.save("model.keras")
