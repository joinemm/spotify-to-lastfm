# HOW TO USE

## Step 1. Get your spotify data package

Navigate your favourite browser to https://www.spotify.com/us/account/privacy/

At the bottom you will find this ![spotify image](docs/spotify_data_package.png)

Select `extended streaming history` and wait for you data package to arrive with the enthusiasm of a child waiting for their christmas present.

## Step 2. Parse, filter and convert spotify json into scrobbleable json

First move your spotify streaming data into a comfortable folder.

Convert your data. For example with data in `/dataset` and splitting into 2600 scrobbles per day:
```
$ python convert.py dataset 2600
```

The resulting files will be spit into `/results/[n].json` 

## Optional step: Analyze

At this point you could do some light analysis of your listening by using `analyze.py` with a given json split.

```
$ python analyze.py results/1.json
```

## Step 3. Scrobble tracks to lastfm

Ready to import all your long lost plays of deadmau5 from 2012?

Get lastfm api credentials https://www.last.fm/api/account/create

Fill your key, secret, username and password into the `credentials.env` file.

Select a file to scrobble and watch the results. Scrobbling will happen in blocks of 50 tracks and every track will have it's timestamp shifted by a minute from another, starting from 2 weeks ago. Lastfm has a hard limit of ~2800 scrobbles per day so keep that in mind. Running this more than once per day with max scrobbles **will** get you rate limited.

```
$ python scrobble.py results/1.json [-v]
```

Optional `-v` parameter will list every track.