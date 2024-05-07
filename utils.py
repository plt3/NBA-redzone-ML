import json
import os
import subprocess

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


def get_focused_space():
    command = "yabai -m query --spaces"
    spaces = json.loads(run_shell(command))

    for space in spaces:
        if space["has-focus"]:
            return space["index"]

    raise Exception("No focused space found.")


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
