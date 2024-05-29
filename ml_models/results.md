# ML Classifier Results:

## part3.py (VGG-16 without data augmentation):

- part3_cropped.keras: 98.3% on test data on 5/6/24 (<3000 images total), with 200x320 images
  - ok also running it on test data from 4239 total images (so more test data than when it was trained)
    gives 99.2% accuracy which is crazy and better than the others that were trained on more data (i.e. part3_cropped_5-13-24.keras)
    - on second thought this is probably due to that test data containing some of the images it was
      trained on (since it was generated with two different calls to split-folders), so the better
      accuracy probably just shows it can correctly classify the images it was trained on (and might
      be more of a result of overfitting than anything)
- part3_cropped_5-13-24.keras: 98.0% on test data on 5/13/24 (4239 images total), with 200x320 images
- part3_cropped_5-13-24_2.keras: 98.2% on test data on 5/13/24 (4239 images total), but with 300x480 images
  - running the classifier also takes ~2.25x longer on each image (proportional to how many times more pixels images have)
- part5_cropped.keras: 98.6% on test data, 98.47% on predict.py (4239 images total), with 200x320 images
  - seems like the best result then
- part5_cropped_5-29-24.keras: 97.8% on test data, 98.01% on predict.py on 5/29/24 (5513 images total), with 200x320 images
  - this is also after reclassifying some images (see reclassified_images.txt)
- part3_cropped_5-29-24.keras: 98.2% on test data, 98.28% on predict.py on 5/29/24 (5513 images total), with 200x320 images
