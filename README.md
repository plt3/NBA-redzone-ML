# NBA-redzone-ML

> switch to a different NBA game during commercial breaks using a machine learning image classifier

## Scripts:

### Gathering data for ML classifier:

- `take_screenshots.py`: run while watching up to 4 streams (in the same desktop space) to take screenshots of each stream every 60 seconds
- `label_screenshots.py`: GUI utility to easily label each screenshot taken by `take_screenshots.py` as representing an NBA game or a commercial

### Training/evaluating the ML classifier:

- `predict.py`: run the classifier on evaluation data, and print out false positives/negatives
- `wrongs.py`: display images the classifier wrongly classified. Copy and paste output from `predict.py` into wrongs.txt, then run `wrongs.py` to see all mistakes it made

## TODO:

- stop using overlay at all?
  - or at least don't try to collect training screenshots when overlay is on
  - use iTerm transparency instead? or some other way to have transparency
