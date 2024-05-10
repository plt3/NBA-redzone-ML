import logging
import subprocess
import sys
import time
from threading import Lock, Thread

import flask.cli
from flask import Flask, render_template, request

from classifier import Classifier
from take_screenshots import ScreenshotTaker
from utils import (choose_main_window_id, choose_space, control_stream_audio,
                   get_chrome_cli_ids, get_window_video_elements, get_windows,
                   let_user_choose_iframe, run_shell, strip_win_title)

FORCE_COMMERCIAL = None
MODEL_FILE_PATH = "ml_models/part3_cropped.keras"
# when making request to start halftime, stop classification for 14 minutes
HALFTIME_DURATION = 14 * 60


class StreamManager:
    start_delay = 5

    def __init__(self, space=None, server_port=80, gather_data=False):
        self.classifier = Classifier(MODEL_FILE_PATH)
        # keys: window IDs, values: True to force that window as showing a commercial,
        # False to force it as showing NBA
        self.force_windows = {}
        self.lock = Lock()

        if space is None:
            self.space = choose_space()
        else:
            self.space = int(space)

        windows = get_windows(self.space, title=True)
        self.id_dict = get_chrome_cli_ids(windows)
        self.was_commercial = {}
        # initialize all windows as not showing commercials
        for win_id in self.id_dict:
            self.was_commercial[win_id] = False

        self.main_id, title = choose_main_window_id(windows)
        print(f'Selected main window with title "{title}" in space {self.space}.')

        self.handle_iframes(windows)

        # run skhd_process in background for hotkeys to work
        self.skhd_process = subprocess.Popen(["skhd", "-c", "./skhdrc"])
        print("skhd process started.")

        self._start_flask_server(server_port)

        # save screenshots for training classifier later
        if gather_data:
            # TODO: should stop taking screenshots when overlay is on
            self.sc_taker = ScreenshotTaker(self.space)
            Thread(target=self.sc_taker.take_screenshots, daemon=True).start()

        print(
            "\nSetup done. Make sure space with streams is visible,"
            " or software will not work.\n"
        )

        # TODO: update this with keybinds too (threading)
        self.focused_id = self.main_id

    def __del__(self):
        self.classifier.__del__()
        self.skhd_process.terminate()
        print("skhd process terminated.")

    def _start_flask_server(self, port):
        # suppress Flask output
        flask.cli.show_server_banner = lambda *_: None
        log = logging.getLogger("werkzeug")
        log.setLevel(logging.ERROR)

        self.app = Flask(__name__)
        self.app.route("/")(self.flask_main_route)
        self.app.route("/timed-break", methods=["POST"])(
            self.handle_timed_break_request
        )
        self.app.route("/untimed-break", methods=["POST"])(
            self.handle_untimed_break_request
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

    def flask_main_route(self):
        # TODO: routes (and so buttons on main screen) for:
        # starting halftime (15 mins until game starts again)
        # forcing game/commercial (for next 30 seconds?)
        # switching focus
        return render_template("index.html")

    def handle_timed_break_request(self):
        """Start/stop timed commercial break in main window"""
        print(request.json)
        if request.json is None:
            return {"message": "must include POST data"}, 400

        with self.lock:
            if self.is_on_break:
                return {"message": "already on break"}, 400

        if request.json["halftime"]:
            duration = HALFTIME_DURATION
        else:
            duration = request.json["duration"]

        Thread(target=self.avoid_main_commercial, daemon=True).start()

        return {"timeout": duration}

    def handle_untimed_break_request(self):
        """Start/stop untimed commercial break in main window"""
        with self.lock:
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
            return {"next_action": "Stop untimed break"}
        else:
            self.return_to_main()
            return {"next_action": "Start untimed break"}

    def handle_iframes(self, windows):
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

    def fullscreen_window(self, windows, window_id):
        """If in tile view, call without specifying window_id to fullscreen focused window
        (and fullscreen all other windows behind it). If all windows are fullscreened, specify
        window_id of window to bring to front. This will also unmute it and mute previous
        front window.
        """
        for window in windows:
            if not window["fullscreen"]:
                run_shell(f"yabai -m window {window['id']} --toggle zoom-fullscreen")
            if window["id"] == window_id:
                run_shell(f"yabai -m window {window['id']} --focus")
                self.focused_id = window_id
            control_stream_audio(
                self.id_dict[window["id"]], mute=(window["id"] != window_id)
            )

    def win_is_commercial(self, win_id, double_check=True, force=None):
        if force is not None:
            is_commercial = force
        else:
            is_commercial = self.classifier.classify(win_id, double_check)

        with self.lock:
            self.was_commercial[win_id] = is_commercial

        return is_commercial

    def switch_away_from_main(self):
        print("switching away from main stream")
        # find non-main window that isn't showing a commercial
        new_id = None
        windows = get_windows(self.space)
        # windows are either all fullscreen or all tiled, so can just check first one
        fullscreen = windows[0]["fullscreen"]
        for win in windows:
            if win["id"] != self.main_id:
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
                control_stream_audio(self.id_dict[self.main_id], mute=True)
        else:
            print("muting")
            control_stream_audio(self.id_dict[self.main_id], mute=True)
            if new_id is not None:
                # switch to stream showing game
                print("switching to other frame")
                control_stream_audio(self.id_dict[new_id], mute=False)

    def return_to_main(self):
        print("returning to main stream")
        windows = get_windows(self.space)
        fullscreen = windows[0]["fullscreen"]

        if fullscreen:
            self.fullscreen_window(windows, self.main_id)
        else:
            control_stream_audio(self.id_dict[self.focused_id], mute=True)
            control_stream_audio(self.id_dict[self.main_id], mute=False)
            self.focused_id = self.main_id

    # def avoid_main_commercial(self):
    #     """Switch to other stream for the duration of commercial in main
    #     stream, then switch back to main stream.
    #     """
    #     self.switch_away_from_main()
    #
    #     # TODO: could do away with this whole waiting? And instead just set
    #     # self.is_commercial and have the mainloop check that to switch away/back
    #     not_end = True
    #     while not_end:
    #         time.sleep(5)
    #         with self.lock:
    #             if self.force_windows.get(self.main_id, False):
    #                 print("Stopping commercial checks due to forced break.")
    #                 return
    #         not_end = self.win_is_commercial(self.main_id, False)
    #
    #     self.return_to_main()

    def handle_if_main_commercial(self):
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

    def mainloop(self):
        try:
            while True:
                time.sleep(5)
                self.handle_if_main_commercial()
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt received, shutting down.")
            # destructor doesn't run when SIGINT received? So call it explicitly
            self.__del__()


def main():
    if len(sys.argv) >= 3:
        manager = StreamManager(sys.argv[1], gather_data=sys.argv[2].lower() == "true")
    elif len(sys.argv) == 2:
        manager = StreamManager(sys.argv[1])
    else:
        manager = StreamManager()

    manager.mainloop()


if __name__ == "__main__":
    main()
