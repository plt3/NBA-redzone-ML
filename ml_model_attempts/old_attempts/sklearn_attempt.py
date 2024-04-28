# from https://www.youtube.com/watch?v=il8dMDlXrIE

import os

import numpy as np
from joblib import dump, load
from skimage.io import imread
from skimage.transform import resize
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.svm import SVC

# prepare data
input_dir = "../data/training"
categories = ["0", "1"]

data = []
labels = []
for category_idx, category in enumerate(categories):
    for index, file in enumerate(os.listdir(os.path.join(input_dir, category))):
        img_path = os.path.join(input_dir, category, file)
        img = imread(img_path)
        # img = resize(img, (200, 200))
        img = resize(img, (100, 100))
        # img = resize(img, (50, 50))
        # if img.flatten().shape != (120000,):
        #     os.remove(img_path)
        # else:
        data.append(img.flatten())
        labels.append(category_idx)
        if index % 100 == 0:
            print(f"{category}: {index}")

# __import__("pprint").pprint(data)
# for i, d in enumerate(data):
#     if d.shape != (120000,):
#         print(i, d.shape)
data = np.asarray(data)
labels = np.asarray(labels)
# print(len(data))
# print(labels)
# exit()

# train / test split
x_train, x_test, y_train, y_test = train_test_split(
    data, labels, test_size=0.2, shuffle=True, stratify=labels
)

# train classifier
print("before svc")
classifier = SVC()

# TODO: best params are C = 10 and gamma = 0.001 from 50x50. Try with 200x200?
# parameters = [{"gamma": [0.01, 0.001, 0.0001], "C": [1, 10, 100, 1000]}]
parameters = [{"gamma": [0.001], "C": [10]}]

print("starting grid search")
grid_search = GridSearchCV(classifier, parameters, verbose=10)

print(f"DEBUGPRINT[3]: main.py:40 (before grid_search.fit(x_train, y_train))")
grid_search.fit(x_train, y_train)

# test performance
best_estimator = grid_search.best_estimator_

print(f"DEBUGPRINT[1]: main.py:45 (before y_prediction = best_estimator.predict(x_…)")
y_prediction = best_estimator.predict(x_test)

score = accuracy_score(y_prediction, y_test)

resultstr = "{}% of samples were correctly classified".format(str(score * 100))
print(resultstr)
import os

os.system(
    f'osascript -e \'tell application "Messages" to send "{resultstr}" to buddy "9784734599"\''
)

# pickle.dump(best_estimator, open("./model.p", "wb"))
dump(best_estimator, "model.p")
