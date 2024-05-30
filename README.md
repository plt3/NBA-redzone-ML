# NBA-redzone-ML

> switch to a different NBA game during commercial breaks using a machine learning image classifier

## What does this do?

I love watching the NBA, but I hate watching commercials. NBA-redzone-ML solves this problem by taking screenshots of the
browser window(s) showing NBA stream(s) every 3 seconds and passing the screenshots to an image classifier. When the classifier
detects that the stream is displaying a commercial, NBA-redzone-ML mutes the stream and optionally covers it with a slightly
opaque window to avoid having to watch or hear the commercial. If other windows are simultaneously streaming games, it will
also unmute and focus a game that is not showing a commercial.

## Features:

- automatic commercial detection (around 98% accurate in testing)
- mutes stream during commercial and switches to another stream if possible
- optionally covers commercial with an opaque window and removes it when returning to game
- supports watching up to 4 streams in the same desktop space and switching between them
- use any device connected to same network as a remote to override whether stream is displaying commercial or game, as well as forcing
  commercial for 15 minutes during halftime
- watch multiple games tiled in desktop space or with one window fullscreened and others behind it, switching focus during commercials

## Installation and Usage:

### Requirements:

- macOS
- Brave Browser (could be easily modified to work with other Chromium-based browsers)
- iTerm2 (optional)
- Python
- [yabai](https://github.com/koekeishiya/yabai) (no need to disable SIP)
- [chrome-cli](https://github.com/prasmussen/chrome-cli) 

### Installation:

- clone this repository
- in Brave Browser, make sure View > Developer > Allow JavaScript from Apple Events is checked (see [chrome-cli documentation](https://github.com/prasmussen/chrome-cli?tab=readme-ov-file#javascript-execution-and-viewing-source))
- optional: setup an opaque iTerm2 profile to use to cover commercials
  - when ML-RedZone determines that the stream is showing a commercial, it can optionally cover the stream with an iTerm2 window to
    avoid having to look at the commercial. I chose to use an iTerm2 window as this cover because you can make them transparent, so you
    can keep an eye on the stream in case there is an error with the automatic commercial detection
  - when creating the profile, setting transparency to 7 in the Window tab is a good value
  - I recommend using some relaxing or interesting background image, so that you can look at it during commercials
  - make sure to call the profile "ML-RedZone Placeholder"
- download image classifier weights TODO

### Launching the Program:

- see usage information with `python3 main.py --help`
- you can either specify stream URLs as positional arguments on the command line, or can simply open the stream(s) you would like to
  watch in browser windows in an empty desktop space
- specify `-t/--take-screenshots` to have program save screenshots every minute to `screenshots` directory for future classifier training
- once program is running, it will prompt you to select a desktop space if not already specified, and then to choose a main window if
  there are multiple streams in the space. The main stream is the only one that will constantly be checked for commercials, and all
  other streams will only be switched to if the main stream is showing a commercial.
- the program may also tell you that the stream page is not scriptable, in which case it will let you choose links found on the page that
  may work. Select one that works and then select "continue".

### While the Program is Running:

Once the program is running, it will automatically switch away/back to the main stream when detecting commercials. However, there are some
actions you can perform to override/change its behavior.

#### Keybinds:

- although no keybinds are provided with NBA-redzone-ML, it makes use of yabai window signals to automate behavior.
- if you would like to assign keybinds, I would recommend using [skhd](https://github.com/koekeishiya/skhd) 
- here are keybinds you could set:
  - switching main window: simply focus a different stream to switch the main window. This can be done by clicking on the window, or with
    some sort of command like `yabai -m window --focus north`. This will unmute the selected window, and mute all others.
  - toggling fullscreen/tile view: use a command like `yabai -m window --toggle zoom-fullscreen` to fullscreen/tile a window, and
    NBA-redzone-ML will make sure to change all the other windows accordingly. Use the fullscreen view if you would only like to watch one
    stream most of the time and only switch during a commercial, and the tile view if you would like to keep an eye on multiple streams at once.

#### Remote Control:

- once the program is running, it starts an HTTP server providing a remote control interface
- open the link on any device connected to the same network (especially designed to be used on mobile), and you will see a remote control page
- available remote control buttons:
  - `Start halftime`: press to force a commercial for 15 minutes (i.e. the duration of an NBA halftime). This way, you can watch other streams
    during halftime and switch back once the main game resumes
  - `Force commercial`: press to force classification as a commercial in the main stream. This can be useful if NBA-redzone-ML is not
    recognizing a commercial automatically. Press it again to stop forcing commercials.
  - `Force NBA`: press to force classification as an NBA game in the main stream. This can be useful if NBA-redzone-ML thinks the main stream
    is displaying a commercial, but it is actually a game. Press it again to stop forcing an NBA game.

## Scripts:

### Gathering data for ML classifier:

- `take_screenshots.py`: run while watching up to 4 streams (in the same desktop space) to take screenshots of each stream every 60 seconds
- `label_screenshots.py`: GUI utility to easily label each screenshot taken by `take_screenshots.py` as representing an NBA game or a commercial

### Training/evaluating the ML classifier:

- `predict.py`: run the classifier on evaluation data, and print out false positives/negatives
- `wrongs.py`: display images the classifier wrongly classified. Copy and paste output from `predict.py` into wrongs.txt, then run `wrongs.py` to see all mistakes it made
