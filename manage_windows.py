import sys
import time

from utils import get_windows, run_shell, toggle_mute


def move_focus(windows, direction):
    # don't try to move if a window is fullscreened
    if any([win["fullscreen"] for win in windows]):
        return
    if direction in ["north", "south", "east", "west"]:
        toggle_mute()
        run_shell(f"yabai -m window --focus {direction}", False)
        toggle_mute()
    else:
        raise Exception('direction must be one of "north", "south", "east", or "west".')


def fullscreen_window(windows, window_id=None, from_placeholder=False):
    """If in tile view, call without specifying window_id to fullscreen focused window
    (and fullscreen all other windows behind it). If all windows are fullscreened, specify
    window_id of window to bring to front. This will also unmute it and mute previous
    front window. Specify from_placeholder=True if current fullscreened window is placeholder.
    """
    fullscreen = windows[0]["fullscreen"]
    # only mute focused window if it is maximized, not if in tile view
    if fullscreen and not from_placeholder:
        toggle_mute()
        time.sleep(0.5)

    for window in windows:
        if not window["fullscreen"]:
            run_shell(f"yabai -m window {window['id']} --toggle zoom-fullscreen")
        if window_id is not None and window["id"] == window_id:
            run_shell(f"yabai -m window {window['id']} --focus")
            if fullscreen:
                time.sleep(0.5)
                toggle_mute()
            break


def tile_view(windows):
    """Un-fullscreen window to go back to tile view where all streams are visible"""
    # TODO: switch to OOP to have windows be a member variable?
    for window in windows:
        if window["fullscreen"]:
            run_shell(f"yabai -m window {window['id']} --toggle zoom-fullscreen")


def toggle_fullscreen(windows):
    """Alternate between fullscreening focused window and returning to tile view"""
    for win in windows:
        if win["focus"]:
            if not win["fullscreen"]:
                fullscreen_window(windows)
            else:
                tile_view(windows)
            break


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "toggle_fullscreen":
            # toggle fullscreen of focused window
            toggle_fullscreen(get_windows())
        elif len(sys.argv) == 3 and sys.argv[1] == "fullscreen":
            # fullscreen a background window. Not meant to be bound to a
            # hotkey, only for use when switching away from commercials
            fullscreen_window(get_windows(), int(sys.argv[2]))
        elif sys.argv[1] in ["move_north", "move_south", "move_east", "move_west"]:
            # move between windows
            move_focus(get_windows(), sys.argv[1].removeprefix("move_"))
    else:
        print("TODO: help message")


if __name__ == "__main__":
    main()
