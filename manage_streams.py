import logging
import os
import subprocess
import time
from threading import Lock, Thread

import flask.cli
from flask import Flask, render_template

from classifier import Classifier
from constants import (
    DEFAULT_PORT,
    DEFAULT_UPDATE_RATE,
    HALFTIME_DURATION,
    MODEL_FILE_PATH,
)
from take_screenshots import ScreenshotTaker
from utils import (
    choose_main_window_id,
    chrome_cli_execute,
    close_window,
    control_stream_audio,
    convert_open_windows_to_minimal,
    cover_window,
    get_chrome_cli_ids,
    get_window_video_elements,
    get_windows,
    let_user_choose_iframe,
    open_commercial_cover,
    open_stream_windows,
    run_shell,
    strip_win_title,
)


class StreamManager:
    yabai_focus_signal_label = "MLRedZoneFocus"
    yabai_fullscreen_signal_label = "MLRedZoneFullscreen"

    def __init__(
        self,
        space: int,
        urls: list[str] = [],
        classifier_path: str = MODEL_FILE_PATH,
        server_port: int = DEFAULT_PORT,
        gather_data: bool = False,
        cover_commercials: bool = True,
        update_rate: int = DEFAULT_UPDATE_RATE,
    ) -> None:
        self.classifier = Classifier(classifier_path)
        # keys: window IDs, values: True to force that window as showing a commercial,
        # False to force it as showing NBA
        self.force_windows: dict[int, bool] = {}
        self.lock = Lock()
        self.update_rate = update_rate
        self.during_halftime = False
        self.windows_are_fullscreen = False
        self.last_focus_called = time.time()
        self.last_fullscreen_called = time.time()

        self.space = space

        if len(urls) == 0:
            input(
                "\nSince no stream URLs were provided on the command line, assuming that"
                f" all tabs in all windows in space {self.space} contain streams,"
                " and will close all of them to reopen them with minimal browser theme."
                " Press Enter to acknowledge this, or ctrl + c to cancel."
            )
            windows = convert_open_windows_to_minimal(self.space)
        else:
            windows = open_stream_windows(urls, self.space)

        self.id_dict = get_chrome_cli_ids(windows)

        self.main_id, title = choose_main_window_id(windows)
        print(f'Selected main window with title "{title}" in space {self.space}.')

        # check if can execute js using chrome-cli
        test_val = "testing_string"
        if (
            chrome_cli_execute(
                "javascript/test.js",
                self.id_dict[self.main_id],
                {"TEST_VALUE": test_val},
            ).strip()
            != test_val
        ):
            raise Exception(
                "Unable to inject JavaScript into browser pages. Did you"
                " check View > Developer > Allow JavaScript from Apple Events in the"
                " browser options?"
            )

        self.was_commercial: dict[int, bool] = {}
        # initialize all windows as not showing commercials
        for win_id, chrome_cli_id in self.id_dict.items():
            self.was_commercial[win_id] = False
            # mute all non-main windows
            if win_id != self.main_id:
                control_stream_audio(chrome_cli_id, mute=True)

        self.handle_iframes(windows)

        # turn off yabai mouse_follows_focus so that focusing cover window doesn't move
        # mouse
        self.mouse_follows_focus = run_shell("yabai -m config mouse_follows_focus")
        if self.mouse_follows_focus != "off":
            run_shell("yabai -m config mouse_follows_focus off")
            print("Switched mouse_follows_focus off.")

        if cover_commercials:
            self.cover_id = open_commercial_cover(self.space, windows)
        else:
            self.cover_id = None

        self._start_flask_server(server_port)

        # send window focus request when window is focused
        uri = "http://localhost"
        if server_port != 80:
            uri += f":{server_port}"
        os.system(
            f"yabai -m signal --add event=window_focused label={self.yabai_focus_signal_label}"
            ' app="^Brave Browser$" action="curl -X POST'
            f' {uri}/focus/\\$YABAI_WINDOW_ID"'
        )
        os.system(
            f"yabai -m signal --add event=window_resized label={self.yabai_fullscreen_signal_label}"
            ' app="^Brave Browser$" action="curl -X POST'
            f' {uri}/toggle-fullscreen/\\$YABAI_WINDOW_ID"'
        )

        # save screenshots for training classifier later
        if gather_data:
            if self.cover_id is None:
                ignore_ids = []
            else:
                ignore_ids = [self.cover_id]
            self.sc_taker = ScreenshotTaker(self.space, ignore_ids=ignore_ids)
            Thread(target=self.sc_taker.take_screenshots, daemon=True).start()

        print(
            "\nSetup done. Make sure space with streams is visible,"
            " or software will not work.\n"
        )

        # TODO: update this with keybinds too (threading)
        self.focused_id = self.main_id

    def __del__(self) -> None:
        if hasattr(self, "classifier"):
            self.classifier.__del__()

        if hasattr(self, "cover_id") and self.cover_id is not None:
            close_window(self.cover_id)
            print("Commercial cover window closed.")

        if hasattr(self, "mouse_follows_focus"):
            if self.mouse_follows_focus != "off":
                run_shell(
                    f"yabai -m config mouse_follows_focus {self.mouse_follows_focus}"
                )
                print("Switched mouse_follows_focus back on.")

        try:
            run_shell(f"yabai -m signal --remove {self.yabai_focus_signal_label}")
            print(f"Yabai window focus signal removed.")
            run_shell(f"yabai -m signal --remove {self.yabai_fullscreen_signal_label}")
            print(f"Yabai window fullscreen signal removed.")
        except subprocess.CalledProcessError:
            pass

    def _start_flask_server(self, port: int) -> None:
        # suppress Flask output
        flask.cli.show_server_banner = lambda *_: None
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        self.app = Flask(__name__)

        # add routes
        self.app.route("/")(self.flask_main_route)
        self.app.route("/force-halftime", methods=["POST"])(
            self.handle_halftime_request
        )
        self.app.route("/force-commercial", methods=["POST"])(
            self.handle_force_commercial_request
        )
        self.app.route("/force-nba", methods=["POST"])(self.handle_force_nba_request)
        self.app.route("/focus/<int:win_id>", methods=["POST"])(
            self.handle_focus_window_request
        )
        self.app.route("/toggle-fullscreen/<int:win_id>", methods=["POST"])(
            self.handle_toggle_fullscreen_request
        )

        # run Flask app in background thread
        host = "0.0.0.0"
        Thread(target=lambda: self.app.run(host=host, port=port), daemon=True).start()

        ip = run_shell(
            "ifconfig -l | xargs -n1 ipconfig getifaddr", shell=True, check=False
        ).strip()
        port_str = ""
        if port != 80:
            port_str = f":{port}"
        # copy IP address to clipboard to easily paste on iPhone with clibpoard sync
        run_shell(f'printf "http://{ip}{port_str}" | pbcopy', shell=True)

        message = f"HTTP server listening at http://{host}{port_str} for this device,"
        message += f" or http://{ip}{port_str} for other devices on this network.\n"
        message += f"http://{ip}{port_str} has been copied to clipboard."
        print(message)

    def flask_main_route(self) -> str:
        return render_template("index.html")

    def handle_focus_window_request(
        self, win_id: int
    ) -> tuple[dict[str, str], int] | dict[str, str]:
        """Focus window with given ID and make that window the new main window"""
        # debounce calls due to yabai signals
        if time.time() - self.last_focus_called < 1:
            return {"message": "Must wait >= 1 second between calls"}, 400
        self.last_focus_called = time.time()

        if win_id not in [win["id"] for win in get_windows(self.space)]:
            return {"message": f"{win_id} is not a stream window"}, 400
        elif win_id == self.focused_id:
            return {"message": f"{win_id} is already focused"}, 400
        elif win_id == self.main_id:
            return {"message": f"{win_id} is already main window"}, 400

        with self.lock:
            self.was_commercial[self.main_id] = False
            self.main_id = win_id

        print(f"Switched main ID to {win_id}")
        self.return_to_main()

        return {}

    def handle_toggle_fullscreen_request(
        self, win_id: int
    ) -> tuple[dict[str, str], int] | dict[str, str]:
        # yabai calls this too often bc of resizing windows, so debounce
        if time.time() - self.last_fullscreen_called < 1:
            return {"message": "Must wait >= 1 second between calls"}, 400
        self.last_fullscreen_called = time.time()
        if win_id != self.focused_id:
            return {"message": "Can only fullscreen focused window"}, 400

        windows = get_windows(self.space)

        if not self.windows_are_fullscreen:
            print("Fullscreening windows")
            self.fullscreen_window(windows, self.focused_id)
        else:
            print("Switching back to tile view")
            for win in windows:
                if win["id"] != self.cover_id and win["fullscreen"]:
                    run_shell(f"yabai -m window {win['id']} --toggle zoom-fullscreen")

        with self.lock:
            self.windows_are_fullscreen = not self.windows_are_fullscreen

        return {}

    def handle_halftime_request(
        self,
    ) -> tuple[dict[str, int | str], int] | dict[str, int]:
        """Start/stop halftime break in main window"""
        with self.lock:
            if self.during_halftime:
                return {"message": "already during halftime"}, 400

        Thread(target=self.force_halftime, daemon=True).start()

        return {"timeout": HALFTIME_DURATION}

    def handle_force_commercial_request(
        self,
    ) -> tuple[dict[str, str], int] | dict[str, str]:
        """Start/stop untimed commercial break in main window"""
        with self.lock:
            if self.during_halftime:
                return {"message": "cannot force commercial during halftime"}, 400
            # force commercial if no previous force or if previous force was NBA
            if not self.force_windows.get(self.main_id, False):
                force_commercial = True
                self.force_windows[self.main_id] = True

                if self.was_commercial[self.main_id]:
                    # set was_commercial to False, so that when checks resume, they will
                    # swich away from main if commercial again
                    self.was_commercial[self.main_id] = False
                    skip_switch_away = True
                else:
                    skip_switch_away = False
            else:
                force_commercial = False
                del self.force_windows[self.main_id]
                skip_switch_away = False

        if force_commercial:
            if not skip_switch_away:
                self.switch_away_from_main()
            return {"next_action": "Stop forcing commercial"}
        else:
            self.return_to_main()
            return {"next_action": "Force commercial"}

    def handle_force_nba_request(self) -> dict[str, str]:
        """Force/stop forcing showing game in main window"""
        with self.lock:
            # force NBA if no previous force or if previous force was commercial
            if self.force_windows.get(self.main_id, True):
                if self.force_windows.get(self.main_id, None) is None:
                    return_to_main = self.was_commercial[self.main_id]
                else:
                    # return_to_main = True if previous force was commercial, bc
                    # handle_force_commercial_request sets was_commercial to False
                    return_to_main = True
                self.force_windows[self.main_id] = False
                self.was_commercial[self.main_id] = False
                force_nba = True
                switch_back_to_halftime = False
            else:
                # go back to forced commercial if stopping NBA force while halftime is
                # still ongoing
                if self.during_halftime:
                    self.force_windows[self.main_id] = True
                    switch_back_to_halftime = True
                else:
                    # delete force if previous force was NBA (i.e. toggle)
                    del self.force_windows[self.main_id]
                    switch_back_to_halftime = False
                return_to_main = False
                force_nba = False

        if force_nba:
            if return_to_main:
                self.return_to_main()
            return {"next_action": "Stop forcing NBA"}
        else:
            if switch_back_to_halftime:
                self.switch_away_from_main()
            return {"next_action": "Force NBA"}

    def force_halftime(self) -> None:
        """Switch to other stream for the duration of halftime in main
        stream, then switch back to main stream.
        """
        with self.lock:
            self.during_halftime = True

            if self.was_commercial[self.main_id]:
                self.was_commercial[self.main_id] = False
                skip_switch_away = True
            else:
                skip_switch_away = False

            # skip switching away if commercial already forced by
            # handle_force_commercial_request
            if self.force_windows.get(self.main_id, False):
                skip_switch_away = True
            else:
                self.force_windows[self.main_id] = True

        if not skip_switch_away:
            self.switch_away_from_main()

        time.sleep(HALFTIME_DURATION)

        with self.lock:
            return_to_main = self.force_windows.get(self.main_id, True)
            # don't delete force_window if force got changed to NBA during halftime
            if return_to_main:
                del self.force_windows[self.main_id]
            self.during_halftime = False

        if return_to_main:
            self.return_to_main()

    def handle_iframes(self, windows: list[dict]) -> None:
        """Can't mute/unmute a page with JavaScript if its video elements are playing
        in iframes due to same-origin policy. Therefore, detect this and let user
        choose a stream that was in an iframe as whole page.
        """
        for win in windows:
            chrome_cli_id = self.id_dict[win["id"]]
            video_obj = get_window_video_elements(chrome_cli_id)

            if not video_obj["has_video"]:
                iframes = video_obj["iframes"]
                title = strip_win_title(win["title"])

                if len(iframes) == 0:
                    raise Exception(f'No stream found in window with title "{title}"')

                let_user_choose_iframe(title, iframes, chrome_cli_id)

    def fullscreen_window(self, windows: list[dict], window_id: int) -> None:
        """If in tile view, call without specifying window_id to fullscreen focused window
        (and fullscreen all other windows behind it). If all windows are fullscreened, specify
        window_id of window to bring to front. This will also unmute it and mute previous
        front window.
        """
        for window in windows:
            if window["id"] != self.cover_id:
                if not window["fullscreen"]:
                    run_shell(
                        f"yabai -m window {window['id']} --toggle zoom-fullscreen"
                    )
                if window["id"] == window_id:
                    with self.lock:
                        self.focused_id = window_id
                    run_shell(f"yabai -m window {window['id']} --focus")
                control_stream_audio(
                    self.id_dict[window["id"]], mute=(window["id"] != window_id)
                )

    def win_is_commercial(
        self, win_id: int, double_check: bool = True, force: bool | None = None
    ) -> bool:
        if force is not None:
            is_commercial = force
        else:
            is_commercial = self.classifier.classify(win_id, double_check)

        with self.lock:
            self.was_commercial[win_id] = is_commercial

        return is_commercial

    def switch_away_from_main(self) -> None:
        print("switching away from main stream")
        # find non-main window that isn't showing a commercial
        new_id = None
        windows = get_windows(self.space)
        # windows are either all fullscreen or all tiled, so can just check first one
        fullscreen = windows[0]["fullscreen"]
        for win in windows:
            if win["id"] != self.main_id and win["id"] != self.cover_id:
                if not self.win_is_commercial(win["id"], False):
                    new_id = win["id"]
                    self.focused_id = new_id
                    break

        if fullscreen:
            if new_id is not None:
                print("fs other stream")
                # fullscreen stream showing game
                self.fullscreen_window(windows, new_id)
            else:
                if self.cover_id is not None:
                    cover_window(self.main_id, self.cover_id)
                control_stream_audio(self.id_dict[self.main_id], mute=True)
        else:
            print("muting")
            if self.cover_id is not None:
                cover_window(self.main_id, self.cover_id)
            control_stream_audio(self.id_dict[self.main_id], mute=True)
            if new_id is not None:
                # switch to stream showing game
                print("switching to other frame")
                control_stream_audio(self.id_dict[new_id], mute=False)

    def return_to_main(self) -> None:
        print("returning to main stream")
        windows = get_windows(self.space)
        fullscreen = windows[0]["fullscreen"]

        if fullscreen:
            print("Covering window")
            self.fullscreen_window(windows, self.main_id)
        else:
            run_shell(f"yabai -m window {self.main_id} --focus")
            if self.focused_id not in [self.main_id, self.cover_id]:
                control_stream_audio(self.id_dict[self.focused_id], mute=True)
            control_stream_audio(self.id_dict[self.main_id], mute=False)
            self.focused_id = self.main_id

    def handle_if_main_commercial(self) -> None:
        print("running handle_if_main_commercial")
        with self.lock:
            was_commercial = self.was_commercial[self.main_id]
            is_forced = self.force_windows.get(self.main_id, None)

        # only check if neither forcing commercial nor NBA
        if is_forced is None:
            print("checking if commercial")
            is_commercial = self.win_is_commercial(
                self.main_id, double_check=not was_commercial
            )
            if not was_commercial and is_commercial:
                self.switch_away_from_main()
            elif was_commercial and not is_commercial:
                self.return_to_main()

    def mainloop(self) -> None:
        try:
            while True:
                time.sleep(self.update_rate)
                self.handle_if_main_commercial()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")
            # destructor doesn't run when SIGINT received? So call it explicitly
            self.__del__()
