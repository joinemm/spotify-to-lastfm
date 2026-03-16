from datetime import datetime
from itertools import islice
import json
import math
import os
from pathlib import Path
import re
import sys
from dotenv import load_dotenv

UNTIL_TIMESTAMP = None
DEST_FOLDER = "results"
SONG_MIN_DURATION_MS = 30000
SUPPORTED_DATASET_PATTERNS = (
    re.compile(r"^Streaming_History_Audio_.*\.json$"),
    re.compile(r"^StreamingHistory\d+\.json$"),
)
UNSUPPORTED_DATASET_PATTERNS = (
    re.compile(r"^StreamingHistory_music_\d+\.json$"),
    re.compile(r"^StreamingHistory_podcast_\d+\.json$"),
)


def convert_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    songs = []
    too_short = []
    after_lfm = []
    non_music_entries = []
    kept_skipped = []
    if UNTIL_TIMESTAMP:
        cutoff_time = datetime.strptime(
            UNTIL_TIMESTAMP, "%Y-%m-%dT%H:%M:%SZ"
        ).timestamp()
    else:
        cutoff_time = datetime.now().timestamp()

    for song in dataset:
        endtime = datetime.strptime(song["ts"], "%Y-%m-%dT%H:%M:%SZ").timestamp()
        artistname = song["master_metadata_album_artist_name"]
        trackname = song["master_metadata_track_name"]
        albumname = song["master_metadata_album_album_name"]
        msplayed = song["ms_played"]
        was_skipped = song["skipped"]

        new_format = {
            "timestamp": endtime,
            "artist": artistname,
            "track": trackname,
            "album": albumname,
            "ms_played": msplayed,
            "platform": song["platform"],
        }
        if msplayed < SONG_MIN_DURATION_MS:
            too_short.append(new_format)
        elif endtime > cutoff_time:
            after_lfm.append(new_format)
        elif not artistname or not trackname or not albumname:
            non_music_entries.append(new_format)
        else:
            if was_skipped:
                kept_skipped.append(new_format)
            songs.append(new_format)

    print(
        filename,
        len(songs),
        "valid,",
        len(too_short),
        "too short,",
        len(kept_skipped),
        "skipped but kept,",
        len(non_music_entries),
        "non-music entries,",
        len(after_lfm),
        "after",
        cutoff_time,
    )
    return songs


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def find_dataset_files(folder):
    dataset_root = Path(folder)
    json_files = list(dataset_root.rglob("*.json"))
    files = sorted(
        str(path)
        for path in json_files
        if any(pattern.match(path.name) for pattern in SUPPORTED_DATASET_PATTERNS)
    )
    unsupported_files = sorted(
        str(path)
        for path in json_files
        if any(pattern.match(path.name) for pattern in UNSUPPORTED_DATASET_PATTERNS)
    )

    if not files:
        if unsupported_files:
            raise FileNotFoundError(
                "Found non-extended Spotify streaming history files "
                f"(for example {unsupported_files[0]}). This tool only supports "
                "Spotify Extended Streaming History exports. Request the "
                "'Extended streaming history' package from Spotify and use the "
                "folder containing 'Streaming_History_Audio_*.json' files."
            )
        raise FileNotFoundError(
            f"No supported Spotify music history files found under {dataset_root}"
        )

    return files


def convert_all(files, per_day):
    all_songs = []
    for filename in files:
        new_songs = convert_file(filename)
        all_songs += new_songs

    print("--------------------------------------------------------------------")
    print(f"found total of {len(all_songs)} valid scrobbles")
    print(
        f"At {per_day} scrobbles/day, it would take {math.ceil(len(all_songs) / per_day)} days to scrobble"
    )

    first_chunk = 0
    all_songs = sorted(all_songs, key=lambda x: x["timestamp"])

    try:
        os.makedirs(DEST_FOLDER)
    except FileExistsError:
        pass

    for i, song_chunk in enumerate(
        list(chunk(all_songs[first_chunk:], per_day)),
        start=1,
    ):
        filename = f"{DEST_FOLDER}/{i}.json"
        with open(filename, "w") as f:
            songs = list(song_chunk)
            f.write(json.dumps(songs, indent=2))
            start = datetime.fromtimestamp(songs[0]["timestamp"])
            end = datetime.fromtimestamp(songs[-1]["timestamp"])
            print(
                f"Wrote {len(song_chunk)} scrobbles from {start} to {end} > {filename}"
            )


def main(folder, per_day):
    load_dotenv("credentials.env")
    global UNTIL_TIMESTAMP
    UNTIL_TIMESTAMP = os.environ.get("UNTIL_TIMESTAMP")
    files = find_dataset_files(folder)
    convert_all(files, per_day)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Convert a spotify dataset into scrobbleable json.")
        print(
            "Dataset folder is path to the directory where spotify json files are located"
        )
        print(
            "Lastfm has a limit of ~2800 scrobbles per day so keep the daily limit under that. Default value is 2600"
        )
        print()
        print("Usage:")
        print("\tpython convert.py [dataset folder] [scrobbles per day]")
        quit(1)

    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2600)
