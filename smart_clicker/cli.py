import argparse

from .player import ScenarioPlayer
from .recorder import ScenarioRecorder


def build_parser():
    parser = argparse.ArgumentParser(prog="smart-clicker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    play_parser = subparsers.add_parser("play", help="Play scenario YAML")
    play_parser.add_argument("scenario")
    play_parser.add_argument("--run", dest="run_id")
    play_parser.add_argument("--backend", default="uia")

    record_parser = subparsers.add_parser("record", help="Record scenario YAML")
    record_parser.add_argument("--out", required=True)
    record_parser.add_argument("--name", default="scenario_name")
    record_parser.add_argument("--backend", default="uia")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.command == "play":
        ScenarioPlayer(backend=args.backend).play_file(args.scenario, run_id=args.run_id)
        return
    if args.command == "record":
        ScenarioRecorder(out_path=args.out, name=args.name, backend=args.backend).record()


if __name__ == "__main__":
    main()
