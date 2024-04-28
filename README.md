# NBA-redzone-ML

> switch to a different NBA game during commercial breaks using a machine learning image classifier

## Scripts:

### Gathering data for ML classifier:

- `take_screenshots.py`: run while watching up to 4 streams (in the same desktop space) to take screenshots of each stream every 60 seconds
- `label_screenshots.py`: GUI utility to easily label each screenshot taken by `take_screenshots.py` as representing an NBA game or a commercial
