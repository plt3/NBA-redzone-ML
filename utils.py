import json
import subprocess

NOTIFICATION_TITLE = "NBARedZone"


def run_shell(command, check=True):
    # split command into list with each element containing a word, except if command
    # contains quotes, in which case quoted part must be in one element of list
    if "'" in command:
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

    result = subprocess.run(command_list, capture_output=True, text=True, check=check)

    return result.stdout


def toggle_mute():
    # mute/unmute focused window using Brave keyboard shortcut
    run_shell(
        'osascript -e \'tell application "System Events" to keystroke "m" using control down\''
    )


def notify(text, title=NOTIFICATION_TITLE):
    run_shell(f'osascript -e \'display notification "{text}" with title "{title}"\'')


def get_windows(space=None, title=False):
    command = "yabai -m query --windows --space"
    if space is not None:
        command += f" {space}"

    windows = json.loads(run_shell(command))
    windows_info = [
        {
            "id": win["id"],
            "focus": win["has-focus"],
            "fullscreen": win["has-fullscreen-zoom"],
        }
        for win in windows
    ]

    # add titles for debugging purposes
    if title:
        for index, win in enumerate(windows):
            windows_info[index]["title"] = win["title"]

    return windows_info
