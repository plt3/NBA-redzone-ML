import argparse

from constants import DATA_DIRECTORY, DEFAULT_PORT, MODEL_FILE_PATH
from utils import choose_space


def setup_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Automatically mute/switch NBA streams during commercials."
        " Either specify stream URLs to open as command-line arguments, or program"
        " will use streams open in selected space if no URLs provided."
    )
    parser.add_argument(
        "-s", "--space", type=int, help="Desktop space to display streams in"
    )
    parser.add_argument(
        "-c",
        "--classifier-path",
        default=MODEL_FILE_PATH,
        help="Path to classifier .keras file",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="Port on which to run server for remote control",
    )
    parser.add_argument(
        "-n",
        "--no-cover",
        action="store_true",
        help="Don't cover commercials with iTerm2 window",
    )
    parser.add_argument(
        "-t",
        "--take-screenshots",
        action="store_true",
        help=f"Save screenshots to {DATA_DIRECTORY} directory"
        " every minute for classifier training",
    )
    parser.add_argument(
        "URLs",
        nargs=argparse.REMAINDER,
        help="Stream(s) to open in given space."
        " Do not specify any to make program use all tabs open in selected space.",
    )

    return parser


def main() -> None:
    try:
        parser = setup_parser()
        args = parser.parse_args()

        if args.space is None:
            args.space = choose_space()

        from manage_streams import StreamManager

        manager = StreamManager(
            args.space,
            args.URLs,
            classifier_path=args.classifier_path,
            server_port=args.port,
            gather_data=args.take_screenshots,
            cover_commercials=not args.no_cover,
        )
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received, aborting.")
    else:
        manager.mainloop()


if __name__ == "__main__":
    main()
