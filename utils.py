import json
import os
import subprocess
import time

from simple_term_menu import TerminalMenu

NOTIFICATION_TITLE = "NBARedZone"


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


def control_stream_audio(chrome_cli_id, mute=True):
    if mute:
        mute_str = "true"
    else:
        mute_str = "false"
    # TODO: support other browsers chrome-cli supports
    command = (
        'brave-cli execute \'Array.from(document.querySelectorAll("video"))'
        f".forEach(e => e.muted = {mute_str});' -t {chrome_cli_id}"
    )
    run_shell(command)


def get_window_video_elements(chrome_cli_id):
    """Return JSON object containing whether given tab has any HTML video elements, and
    list of HTML iframe elements if not. This is because it is only possible to mute
    video elements, not iframes via JavaScript. So it's important to have a stream
    be displayed in a video and not an iframe in order to programmatically mute/unmute it.
    """
    command = (
        "brave-cli execute '(function(){const e={iframes:[]};"
        'return e.has_video=document.querySelectorAll("video").length>0,'
        'e.has_video||(e.iframes=Array.from(document.querySelectorAll("iframe")).map((e=>e.src))),'
        f"JSON.stringify(e)}}());' -t {chrome_cli_id}"
    )
    return json.loads(run_shell(command))


def notify(text, title=NOTIFICATION_TITLE):
    run_shell(f'osascript -e \'display notification "{text}" with title "{title}"\'')


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
                f"[{i + 1}] {win['title'].removesuffix(' - Audio playing')}"
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

    title = windows[choice_index]["title"].removesuffix(" - Audio playing")
    return windows[choice_index]["id"], title


def get_windows(space, title=False):
    command = f"yabai -m query --windows --space {space}"

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


def get_chrome_cli_ids(windows):
    """Return dictionary mapping yabai window IDs to chrome-cli tab IDs (assuming 1 tab
    per window since windows are using minimal theme)"""
    tabs = json.loads(run_shell("OUTPUT_FORMAT=json brave-cli list tabs", shell=True))
    id_dict = {}

    for win in windows:
        stripped_win_title = win["title"].removesuffix(" - Audio playing")
        for tab in tabs["tabs"]:
            # Unsure if this check is robust enough
            if tab["title"] == stripped_win_title:
                id_dict[win["id"]] = int(tab["id"])
                break
        else:
            raise Exception(
                f"No chrome-cli tab ID found for window with title {win['title']}"
            )

    return id_dict
