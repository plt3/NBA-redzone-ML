from keras import applications, optimizers
from keras.layers import Dense, Dropout, Flatten
from keras.models import Sequential
from keras.saving import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator

"""
This also gets 92% on food/not food (but also took forever to train). Probably doing something wrong
when combining the models
"""

# path to the model weights files.
top_model_weights_path = "fc_model.h5"
# dimensions of our images.
img_width, img_height = 200, 200

train_data_dir = "../data/training"
validation_data_dir = "../data/validation"
nb_train_samples = 2984
nb_validation_samples = 1000
# epochs = 50
epochs = 25
batch_size = 16

# build the VGG16 network
vgg16model = applications.VGG16(weights="imagenet", include_top=False)
print("Model loaded.")

# # note that it is necessary to start with a fully-trained
# # classifier, including the top classifier,
# # in order to successfully do fine-tuning
# top_model.load_weights(top_model_weights_path)

# add the model on top of the convolutional base
custom_model = load_model("bottleneck_fc_model.keras")
# this is probably super wrong
final_model = Sequential()
for layer in vgg16model.layers:
    final_model.add(layer)
for layer in custom_model.layers:
    final_model.add(layer)
# model.add(top_model)
# model.layers.extend(top_model.layers)

# set the first 25 layers (up to the last conv block)
# to non-trainable (weights will not be updated)
for layer in final_model.layers[:-4]:
    layer.trainable = False

# compile the model with a SGD/momentum optimizer
# and a very slow learning rate.
final_model.compile(
    loss="binary_crossentropy",
    optimizer=optimizers.SGD(learning_rate=1e-4, momentum=0.9),
    metrics=["accuracy"],
)

# ???
final_model.build()

# prepare data augmentation configuration
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255, shear_range=0.2, zoom_range=0.2, horizontal_flip=True
)

test_datagen = ImageDataGenerator(rescale=1.0 / 255)

train_generator = train_datagen.flow_from_directory(
    train_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode="binary",
)

validation_generator = test_datagen.flow_from_directory(
    validation_data_dir,
    target_size=(img_height, img_width),
    batch_size=batch_size,
    class_mode="binary",
)

# fine-tune the model
final_model.fit(
    train_generator,
    epochs=epochs,
    validation_data=validation_generator,
)

final_model.save("model_part3.keras")
