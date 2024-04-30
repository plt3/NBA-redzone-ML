import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import image_dataset_from_directory

# 180x180px is pretty much arbitrary
inputs = keras.Input(shape=(180, 180, 3))
# get inputs to [0, 1] range instead of [0, 255] range
x = layers.Rescaling(1.0 / 255)(inputs)
x = layers.Conv2D(filters=32, kernel_size=3, activation="relu")(x)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=64, kernel_size=3, activation="relu")(x)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=128, kernel_size=3, activation="relu")(x)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=256, kernel_size=3, activation="relu")(x)
x = layers.MaxPooling2D(pool_size=2)(x)
x = layers.Conv2D(filters=256, kernel_size=3, activation="relu")(x)
x = layers.Flatten()(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs=inputs, outputs=outputs)

model.compile(loss="binary_crossentropy", optimizer="rmsprop", metrics=["accuracy"])

# 2000 images
train_dataset = image_dataset_from_directory(
    "../data/training", image_size=(180, 180), batch_size=32
)
# 1000 images
validation_dataset = image_dataset_from_directory(
    "../data/validation", image_size=(180, 180), batch_size=32
)
# 1984 images
test_dataset = image_dataset_from_directory(
    "../data/evaluation", image_size=(180, 180), batch_size=32
)

# save model every epoch, overwriting file to only save best epoch each time
callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath="convnet_from_scratch.keras", save_best_only=True, monitor="val_loss"
    )
]

# book did 50 epochs, I was impatient
history = model.fit(
    train_dataset, epochs=15, validation_data=validation_dataset, callbacks=callbacks
)

accuracy = history.history["accuracy"]
val_accuracy = history.history["val_accuracy"]
loss = history.history["loss"]
val_loss = history.history["val_loss"]
epochs = range(1, len(accuracy) + 1)
plt.plot(epochs, accuracy, "bo", label="Training accuracy")
plt.plot(epochs, val_accuracy, "b", label="Validation accuracy")
plt.title("Training and validation accuracy")
plt.legend()
plt.figure()
plt.plot(epochs, loss, "bo", label="Training loss")
plt.plot(epochs, val_loss, "b", label="Validation loss")
plt.title("Training and validation loss")
plt.legend()
plt.show()

# # this gets 84.4% accuracy on the test data, while it gets 69.5% on the dog/cat data
# # in the book. Wonder why
# test_model = keras.models.load_model("convnet_from_scratch.keras")
# test_loss, test_acc = test_model.evaluate(test_dataset)
# print(f"Test accuracy: {test_acc:.3f}")
