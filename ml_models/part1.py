import matplotlib.pyplot as plt
from setup_datasets import IMAGE_DIMS, get_datasets
from tensorflow import keras
from tensorflow.keras import layers

MODEL_FILE_NAME = "part1_cropped.keras"

train_dataset, validation_dataset, test_dataset = get_datasets()

inputs = keras.Input(shape=IMAGE_DIMS + (3,))
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

# save model every epoch, overwriting file to only save best epoch each time
callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=MODEL_FILE_NAME, save_best_only=True, monitor="val_loss"
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

# # this gets 91.4% accuracy on the test data
# # and 91.5% accuracy with cropped images
# test_model = keras.models.load_model(MODEL_FILE_NAME)
# test_loss, test_acc = test_model.evaluate(test_dataset)
# print(f"Test accuracy: {test_acc:.3f}")
