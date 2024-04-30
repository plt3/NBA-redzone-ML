import matplotlib.pyplot as plt
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.utils import image_dataset_from_directory

# "So if your new dataset differs a lot from the dataset on which the original model was
# trained, you may be bet- ter off using only the first few layers of the model to do
# feature extraction, rather than using the entire convolutional base." (page 226)
#
# book also lists other image-classification models (other than VGG16) to try

conv_base = keras.applications.vgg16.VGG16(
    weights="imagenet", include_top=False, input_shape=(180, 180, 3)
)


def get_features_and_labels(dataset):
    all_features = []
    all_labels = []
    print(f"DEBUGPRINT[1]: part3.py:21 (before for images, labels in dataset:)")
    for images, labels in dataset:
        preprocessed_images = keras.applications.vgg16.preprocess_input(images)
        features = conv_base.predict(preprocessed_images)
        all_features.append(features)
        all_labels.append(labels)
    print(f"DEBUGPRINT[2]: part3.py:26 (after all_labels.append(labels))")
    return np.concatenate(all_features), np.concatenate(all_labels)


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

train_features, train_labels = get_features_and_labels(train_dataset)
val_features, val_labels = get_features_and_labels(validation_dataset)
test_features, test_labels = get_features_and_labels(test_dataset)

inputs = keras.Input(shape=(5, 5, 512))
x = layers.Flatten()(inputs)
x = layers.Dense(256)(x)
x = layers.Dropout(0.5)(x)
outputs = layers.Dense(1, activation="sigmoid")(x)
model = keras.Model(inputs, outputs)
model.compile(loss="binary_crossentropy", optimizer="rmsprop", metrics=["accuracy"])

model_file_name = "feature_extraction.keras"
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

# # this gets 96.0% accuracy on the test data, very nice
# test_model = keras.models.load_model(model_file_name)
# test_loss, test_acc = test_model.evaluate(test_features, test_labels)
# print(f"Test accuracy: {test_acc:.3f}")
