import argparse

from manage_streams import StreamManager
from take_screenshots import DATA_DIRECTORY
from utils import choose_space


def setup_parser():
    parser = argparse.ArgumentParser(
        description="Automatically mute/switch NBA streams during commercials"
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
        "URLs", nargs=argparse.REMAINDER, help="stream(s) to open in given space"
    )

    return parser


def main():
    parser = setup_parser()
    args = parser.parse_args()

    if args.space is None:
        args.space = choose_space()

    manager = StreamManager(args.space, args.URLs, gather_data=args.take_screenshots)
    manager.mainloop()


if __name__ == "__main__":
    main()
