from datetime import datetime
import json
from operator import itemgetter
import os
import sys

RESULTS_TO_SHOW = 20


def bold(s):
    return f"\033[1m{s}\033[0m"


def analyze(data: dict):
    artist_playcounts = {}
    track_playcounts = {}
    platforms = {}

    start = datetime.fromtimestamp(data[0]["timestamp"])
    end = datetime.fromtimestamp(data[-1]["timestamp"])

    for scrobble in data:
        try:
            artist_playcounts[scrobble["artist"]] += 1
        except KeyError:
            artist_playcounts[scrobble["artist"]] = 1

        try:
            track_playcounts[scrobble["artist"] + " - " + scrobble["track"]] += 1
        except KeyError:
            track_playcounts[scrobble["artist"] + " - " + scrobble["track"]] = 1

        try:
            platforms[scrobble["platform"]] += 1
        except KeyError:
            platforms[scrobble["platform"]] = 1

    print(
        "Analyzing",
        bold(len(data)),
        "Scrobbles between",
        bold(start),
        "and",
        bold(end),
    )
    print()
    print(bold("------ Top artists -------"))
    for i, (item, value) in enumerate(
        sorted(artist_playcounts.items(), key=itemgetter(1), reverse=True)[:RESULTS_TO_SHOW],
        start=1,
    ):
        print(f"#{i:>3} \t {value} plays \t {item}")
    print()
    print(bold("------ Top  tracks -------"))
    for i, (item, value) in enumerate(
        sorted(track_playcounts.items(), key=itemgetter(1), reverse=True)[:RESULTS_TO_SHOW],
        start=1,
    ):
        print(f"#{i:>3} \t {value} plays \t {item}")

    print()
    print(bold("------ Top platforms -------"))
    for i, (item, value) in enumerate(
        sorted(platforms.items(), key=itemgetter(1), reverse=True)[:RESULTS_TO_SHOW], start=1
    ):
        print(f"#{i:>3} \t {value} plays \t {item}")


def main(args):
    if args[1] in ["-A", "--all"]:
        folder = args[2]
        files = sorted(
            [
                f"{folder}/{file}"
                for file in filter(lambda f: f.endswith(".json"), os.listdir(folder))
            ]
        )
        all_data = []
        for file in files:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                all_data += data

        analyze(all_data)
    else:
        with open(args[1], "r", encoding="utf-8") as f:
            data = json.load(f)
            analyze(data)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Analyze a converted json file generated by convert.py")
        print()
        print("Usage:")
        print("\tpython analyze.py [path/to/json]")
        print("\tpython analyze.py -A [path/to/folder]")
        quit(1)
    main(sys.argv)
