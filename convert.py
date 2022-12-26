from datetime import datetime
from itertools import islice
import json
import math
import os
import sys
from dotenv import load_dotenv

load_dotenv("credentials.env")

UNTIL_TIMESTAMP = os.environ.get("UNTIL_TIMESTAMP")
DEST_FOLDER = "results"
SONG_MIN_DURATION_MS = 30000


def convert_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    songs = []
    skipped_songs = []
    too_short = []
    after_lfm = []
    nulls = []
    if UNTIL_TIMESTAMP:
        cutoff_time = datetime.strptime(UNTIL_TIMESTAMP, "%Y-%m-%dT%H:%M:%SZ").timestamp()
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
        if was_skipped:
            skipped_songs.append(new_format)
        elif msplayed < SONG_MIN_DURATION_MS:
            too_short.append(new_format)
        elif endtime > cutoff_time:
            after_lfm.append(new_format)
        elif not artistname or not trackname or not albumname:
            nulls.append(new_format)
        else:
            songs.append(new_format)

    print(
        filename,
        len(songs),
        "valid,",
        len(skipped_songs),
        "skipped,",
        len(too_short),
        "too short,",
        len(nulls),
        "broken,",
        len(after_lfm),
        "after",
        cutoff_time,
    )
    return songs


def chunk(it, size):
    it = iter(it)
    return iter(lambda: tuple(islice(it, size)), ())


def convert_all(files, per_day):
    all_songs = []
    for filename in files:
        new_songs = convert_file(filename)
        all_songs += new_songs

    print("--------------------------------------------------------------------")
    print(f"found total of {len(all_songs)} valid unskipped scrobbles")
    print(
        f"At {per_day} scrobbles/day, it would take {math.ceil(len(all_songs)/per_day)} days to scrobble"
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
            print(f"Wrote {len(song_chunk)} scrobbles from {start} to {end} > {filename}")


def main(folder, per_day):
    files = sorted(
        [
            f"{folder}/{file}"
            for file in filter(lambda f: f.startswith("endsong"), os.listdir(folder))
        ]
    )
    convert_all(files, per_day)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ["-h", "--help"]:
        print("Convert a spotify dataset into scrobbleable json.")
        print("Dataset folder is path to the directory where endsong_n.json files are located")
        print(
            "Lastfm has a limit of ~2800 scrobbles per day so keep the daily limit under that. Default value is 2600"
        )
        print()
        print("Usage:")
        print("\tpython convert.py [dataset folder] [scrobbles per day]")
        quit(1)

    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2600)
