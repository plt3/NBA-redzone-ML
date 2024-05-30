import argparse

from take_screenshots import DATA_DIRECTORY
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
            args.space, args.URLs, gather_data=args.take_screenshots
        )
    except KeyboardInterrupt:
        print("\nKeyboardInterrupt received, aborting.")
    else:
        manager.mainloop()


if __name__ == "__main__":
    main()
