import matplotlib.pyplot as plt
from setup_datasets import IMAGE_DIMS, get_datasets
from tensorflow import keras
from tensorflow.keras import layers

model_file_name = "part4_cropped.keras"
train_dataset, validation_dataset, test_dataset = get_datasets()

conv_base = keras.applications.vgg16.VGG16(
    weights="imagenet", include_top=False, input_shape=(IMAGE_DIMS[0], IMAGE_DIMS[1], 3)
)
conv_base.trainable = False

data_augmentation = keras.Sequential(
    [
        layers.RandomFlip("horizontal"),
        layers.RandomRotation(0.1),
        layers.RandomZoom(0.2),
    ]
)
inputs = keras.Input(shape=(IMAGE_DIMS[0], IMAGE_DIMS[1], 3))
x = data_augmentation(inputs)
x = keras.applications.vgg16.preprocess_input(x)
x = conv_base(x)
x = layers.Flatten()(x)
x = layers.Dense(256)(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(loss="binary_crossentropy", optimizer="rmsprop", metrics=["accuracy"])

callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=model_file_name, save_best_only=True, monitor="val_loss"
    )
]

history = model.fit(
    train_dataset, epochs=50, validation_data=validation_dataset, callbacks=callbacks
)

acc = history.history["accuracy"]
val_acc = history.history["val_accuracy"]
loss = history.history["loss"]
val_loss = history.history["val_loss"]
epochs = range(1, len(acc) + 1)
plt.plot(epochs, acc, "bo", label="Training accuracy")
plt.plot(epochs, val_acc, "b", label="Validation accuracy")
plt.title("Training and validation accuracy")
plt.legend()
plt.figure()
plt.plot(epochs, loss, "bo", label="Training loss")
plt.plot(epochs, val_loss, "b", label="Validation loss")
plt.title("Training and validation loss")
plt.legend()
plt.show()

# # this gets 96.4% accuracy on the test data, so augmentation added 0.4%
# # (but also 5 hours of training)
# test_model = keras.models.load_model(model_file_name)
# test_loss, test_acc = test_model.evaluate(test_dataset)
# print(f"Test accuracy: {test_acc:.3f}")
