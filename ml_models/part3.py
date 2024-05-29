import matplotlib.pyplot as plt
import numpy as np
from setup_datasets import IMAGE_DIMS, get_datasets
from tensorflow import keras
from tensorflow.keras import layers
from tqdm import tqdm

# "So if your new dataset differs a lot from the dataset on which the original model was
# trained, you may be bet- ter off using only the first few layers of the model to do
# feature extraction, rather than using the entire convolutional base." (page 226)
#
# book also lists other image-classification models (other than VGG16) to try

model_file_name = "part3_cropped_5-29-24.keras"
train_dataset, validation_dataset, test_dataset = get_datasets()

conv_base = keras.applications.vgg16.VGG16(
    weights="imagenet", include_top=False, input_shape=IMAGE_DIMS + (3,)
)


def get_features_and_labels(dataset):
    all_features = []
    all_labels = []
    for images, labels in tqdm(dataset):
        preprocessed_images = keras.applications.vgg16.preprocess_input(images)
        features = conv_base.predict(preprocessed_images, verbose=0)
        all_features.append(features)
        all_labels.append(labels)
    return np.concatenate(all_features), np.concatenate(all_labels)


train_features, train_labels = get_features_and_labels(train_dataset)
val_features, val_labels = get_features_and_labels(validation_dataset)
# test_features, test_labels = get_features_and_labels(test_dataset)

# NOTE!!!!!!!! shape must match the output shape of the conv_base layer. This
# changes based on input_shape passed to VGG16!!! Was (5, 5, 512) when input shape
# was (180, 180, 3), but I changed it. Would probably be better to set this shape
# dynamically anyways
# inputs = keras.Input(shape=(6, 10, 512))
inputs = keras.Input(shape=conv_base.layers[-1].output.shape[1:])
x = layers.Flatten()(inputs)
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
    train_features,
    train_labels,
    epochs=20,
    validation_data=(val_features, val_labels),
    callbacks=callbacks,
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

# # also gets 98.3% accuracy with cropped data!!
# test_model = keras.models.load_model(model_file_name)
# test_loss, test_acc = test_model.evaluate(test_features, test_labels)
# print(f"Test accuracy: {test_acc:.3f}")
