import json
import os
import subprocess
import time

from simple_term_menu import TerminalMenu

NOTIFICATION_TITLE = "NBARedZone"
ITERM_PROFILE = "ML-RedZone Placeholder"


def run_shell(command, check=True, shell=False):
    # split command into list with each element containing a word, except if command
    # contains quotes, in which case quoted part must be in one element of list. Also
    # don't split if shell=True
    if shell:
        command_list = command
    elif "'" in command:
        command_list = []
        current_word = ""
        within_quotes = False

        for char in command:
            if not within_quotes:
                if char == " ":
                    if current_word != "":
                        command_list.append(current_word)
                        current_word = ""
                elif char == "'":
                    within_quotes = True
                else:
                    current_word += char
            else:
                if char == "'":
                    command_list.append(current_word)
                    current_word = ""
                    within_quotes = False
                else:
                    current_word += char

        if current_word != "":
            command_list.append(current_word)
    else:
        command_list = command.split()

    result = subprocess.run(
        command_list, capture_output=True, text=True, check=check, shell=shell
    )

    return result.stdout


def chrome_cli_execute(js_file, id, context_dict):
    # run JS code in given file on browser tab with given ID, passing variables to
    # replace in JS file via context_dict parameter
    with open(js_file) as f:
        js_code = "\n" + f.read()

    for var_name, value in context_dict.items():
        js_code = js_code.replace(var_name, value)

    return run_shell(f"brave-cli execute '{js_code}' -t {id}")


def control_stream_audio(chrome_cli_id, mute=True):
    if mute:
        var_dict = {"MUTE_STREAM": "true"}
    else:
        var_dict = {"MUTE_STREAM": "false"}

    chrome_cli_execute("javascript/mute.js", chrome_cli_id, var_dict)


def control_stream_overlay(chrome_cli_id, overlay_text, show_overlay=True):
    var_dict = {"OVERLAY_TEXT": overlay_text, "SHOW_OVERLAY": "true"}
    if not show_overlay:
        var_dict["SHOW_OVERLAY"] = "false"

    chrome_cli_execute("javascript/overlay.js", chrome_cli_id, var_dict)


def get_window_video_elements(chrome_cli_id):
    """Return JSON object containing whether given tab has any HTML video elements, and
    list of HTML iframe elements if not. This is because it is only possible to mute
    video elements, not iframes via JavaScript. So it's important to have a stream
    be displayed in a video and not an iframe in order to programmatically mute/unmute it.
    """
    result = chrome_cli_execute("javascript/video_elements.js", chrome_cli_id, {})
    return json.loads(result)


def notify(text, title=NOTIFICATION_TITLE):
    run_shell(f'osascript -e \'display notification "{text}" with title "{title}"\'')


def open_stream_windows(urls: list[str], space: int) -> None:
    """Open provided URLs in provided space in minimal Brave windows"""
    ids_before = [win["id"] for win in get_windows()]
    for url in urls:
        run_shell(f"open -a 'Brave Browser.app' -n --args --new-window --app='{url}'")

    ids_after = ids_before
    while len(ids_after) == len(ids_before):
        time.sleep(0.5)
        ids_after = [win["id"] for win in get_windows()]

    new_window_ids = [id for id in ids_after if id not in ids_before]

    for id in new_window_ids:
        run_shell(f"yabai -m window {id} --space {space}")


# TODO: split some of these into separate classes/files? Like chrome-cli or cover stuff
def open_commercial_cover(space, windows):
    res_text = run_shell(
        f'osascript -e \'tell application "iTerm" to create window with profile "{ITERM_PROFILE}"\''
    )
    win_id = int(res_text.split()[-1])
    # TODO: condense in one yabai command? Seems like you can chain them
    run_shell(f"yabai -m window {win_id} --toggle float")
    run_shell(f"yabai -m window {win_id} --space {space}")

    # focus all other windows in space to put cover behind them all
    for win in windows:
        run_shell(f"yabai -m window {win['id']} --focus")

    return win_id


def close_commercial_cover(win_id):
    run_shell(f"yabai -m window {win_id} --close")


def cover_window(win_id, cover_id):
    # TODO: probably pass this as an argument? Don't run query here
    win_info = json.loads(run_shell(f"yabai -m query --windows --window {win_id}"))
    coords = win_info["frame"]

    run_shell(f"yabai -m window {cover_id} --move abs:{coords['x']}:{coords['y']}")
    run_shell(f"yabai -m window {cover_id} --resize abs:{coords['w']}:{coords['h']}")
    run_shell(f"yabai -m window {cover_id} --focus")


def strip_win_title(title):
    # remove various suffixes at end of window title that make window title returned
    # by yabai differ from the one returned by chrome-cli
    try:
        end_index = title.index(" - High memory usage")
        title = title[:end_index]
    except ValueError:
        pass
    return title.replace(" - Audio playing", "").replace(" - Brave", "")


def take_screenshot(window_id, file_path):
    extension = os.path.splitext(file_path)[1].removeprefix(".")
    command = f"screencapture -oxl {window_id} -t {extension} {file_path}"
    run_shell(command)


def wait_for_load(chrome_cli_id):
    command = f"OUTPUT_FORMAT=json brave-cli info -t {chrome_cli_id}"
    while json.loads(run_shell(command, shell=True))["loading"]:
        time.sleep(0.5)


def let_user_choose_iframe(win_title, iframes, chrome_cli_id):
    menu_title = (
        f'\nPage with title "{win_title}" is not scriptable. '
        "Try one of these streams embedded in the page:\n"
    )
    iframe_choices = [f"[{i + 1}] {frame}" for i, frame in enumerate(iframes)]
    continue_added = False
    choice_index = 0
    while choice_index != len(iframes):
        terminal_menu = TerminalMenu(
            iframe_choices,
            title=menu_title,
            cursor_index=choice_index,
            raise_error_on_interrupt=True,
            shortcut_key_highlight_style=("fg_green",),
            menu_highlight_style=("underline",),
        )
        choice_index = terminal_menu.show()
        if choice_index != len(iframes):
            run_shell(f"brave-cli open {iframes[choice_index]}" f" -t {chrome_cli_id}")
            wait_for_load(chrome_cli_id)
            has_video = get_window_video_elements(chrome_cli_id)["has_video"]
            if has_video:
                menu_title = (
                    "\nSelected page is scriptable. Press c to continue,"
                    " or choose a different one:\n"
                )
                if not continue_added:
                    iframe_choices.append(f"[c] continue")
                    continue_added = True
            else:
                menu_title = (
                    "\nSelected page is still not scriptable. Try a different one:\n"
                )
                if continue_added:
                    iframe_choices.pop()
                    continue_added = False


def choose_space():
    spaces = json.loads(run_shell("yabai -m query --spaces"))
    spaces.sort(key=lambda space: space["index"])
    space_indices = [space["index"] for space in spaces]
    probable_index = 0
    for i, space in enumerate(spaces):
        if space["is-visible"] and not space["has-focus"]:
            probable_index = i
            break

    terminal_menu = TerminalMenu(
        [f"[{index}] space {index}" for index in space_indices],
        title="\nSelect space containing stream(s):\n",
        cursor_index=probable_index,
        raise_error_on_interrupt=True,
        shortcut_key_highlight_style=("fg_green",),
        menu_highlight_style=("underline",),
    )

    choice_index = terminal_menu.show()
    if choice_index is None:
        raise Exception("No space selected.")

    return space_indices[choice_index]


def choose_main_window_id(windows):
    if len(windows) == 0:
        raise Exception(f"No windows found in given space.")
    elif len(windows) == 1:
        choice_index = 0
    else:
        terminal_menu = TerminalMenu(
            [
                f"[{i + 1}] {strip_win_title(win['title'])}"
                for i, win in enumerate(windows)
            ],
            title="\nSelect main stream:\n",
            raise_error_on_interrupt=True,
            shortcut_key_highlight_style=("fg_green",),
            menu_highlight_style=("underline",),
        )

        choice_index = terminal_menu.show()
        if choice_index is None:
            raise Exception("No main window selected.")

    title = strip_win_title(windows[choice_index]["title"])
    return windows[choice_index]["id"], title


def get_windows(space: int | None = None, title: bool = False) -> list[dict]:
    command = "yabai -m query --windows"
    if space is not None:
        command += f" --space {space}"

    windows = json.loads(run_shell(command))
    windows_info = [
        {
            "id": win["id"],
            "focus": win["has-focus"],
            "fullscreen": win["has-fullscreen-zoom"],
        }
        for win in windows
    ]

    if title:
        for index, win in enumerate(windows):
            windows_info[index]["title"] = win["title"]

    return windows_info


def get_chrome_cli_ids(windows, debug=False):
    """Return dictionary mapping yabai window IDs to chrome-cli tab IDs (assuming 1 tab
    per window since windows are using minimal theme)"""
    tabs = json.loads(run_shell("OUTPUT_FORMAT=json brave-cli list tabs", shell=True))
    id_dict = {}

    for win in windows:
        for tab in tabs["tabs"]:
            # Unsure if this check is robust enough
            if tab["title"] == strip_win_title(win["title"]) or (
                debug == True
                and tab["title"] == ""
                and strip_win_title(win["title"]).endswith("mp4")
            ):
                id_dict[win["id"]] = int(tab["id"])
                break
        else:
            raise Exception(
                f"No chrome-cli tab ID found for window with title {win['title']}"
            )

    return id_dict


if __name__ == "__main__":
    open_stream_windows(
        [
            "https://github.com/kkoomen/vim-doge",
            "https://github.com/JoosepAlviste/nvim-ts-context-commentstring",
        ],
        6,
    )
