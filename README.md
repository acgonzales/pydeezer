# PyDeezer

A package to search and download musics on [Deezer](https://www.deezer.com/en/).

## Installation

### Install from release

```bash
pip install py-deezer
```

### Install from repository

```bash
git clone https://github.com/Chr1st-oo/pydeezer.git
cd pydeezer
pip install .
```

## Usage as a CLI

```bash
Usage: pydeezer [OPTIONS] COMMAND [ARGS]...

  PyDeezer CLI

Options:
  --help  Show this message and exit.

Commands:
  download  Download tracks
```

#### Commands

```bash
Usage: pydeezer download [OPTIONS]

  Download tracks

Options:
  -a, --arl TEXT                  Used to be able to login to Deezer. Check
                                  the docs on how to get one.

  --media-type [Track|Album|Playlist|Artist]
                                  Sets the media type and how it searches the
                                  api.

  -d, --download-dir DIRECTORY    Sets the directory on where the tracks are
                                  to be saved.

  -q, --quality [MP3_128|MP3_256|MP3_320|FLAC]
                                  Sets the quality of the tracks. if the
                                  provided quality is not supported, the
                                  default quality of the track will be used.

  --help                          Show this message and exit.
```

## Usage as a package

#### Logging In

```python
from pydeezer import Deezer

arl = "edit_this"
deezer = Deezer(arl=arl)
user_info = deezer.user
# or
# deezer = Deezer()
# user_info = deezer.login_via_arl(arl)
```

You can get the your `arl` by manually logging into [Deezer](https://www.deezer.com/) using your browser and check the `cookies` and look for the value of `arl`.

#### Searching

```python
# Some login code here

# Search tracks
track_search_results = deezer.search_tracks("IM DOPE")
# Search albums
album_search_results = deezer.search_albums("DAMN", limit=10)
# Search artists
artist_search_results = deezer.search_artists("J. Cole", limit=5)
# Search playlists
playlist_search_results = deezer.search_playlists("top", index=2)
```

#### Getting Information and Downloading

```python
# Some login code here

# Some download stuffs
from pydeezer.constants import track_formats

download_dir = "~/Downloads/"

track_id = "547653622"
track = deezer.get_track(track_id)
# track is now a dict with a key of info, download, tags, and get_tag
# info and tags are dict
track_info = track["info"]
tags_separated_by_comma = track["tags"]
# download and get_tag are partial functions
track["download"](download_dir, quality=track_formats.MP3_320) # this will download the file, default file name is Filename.[mp3 or flac]
tags_separated_by_semicolon = track["get_tag"](separator="; ") # this will return a dictionary similar to track["tags"] but this will override the default separator

artist_id = "53859305"
artist = deezer.get_artist(artist_id)

album_id = "39949511"
album = deezer.get_album(album_id) # returns a dict containing data about the album

playlist_id = "1370794195"
playlist = deezer.get_playlist(playlist_id) # returns a dict containing data about the playlist
```

### Custom ProgressHandler

This example uses the amazing [rich](https://github.com/willmcgugan/rich) package.

#### Code

```python
from pydeezer import Deezer
from pydeezer.ProgressHandler import BaseProgressHandler
import rich
from rich.progress import (
    BarColumn,
    DownloadColumn,
    TextColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    Progress
)

# Extend BaseProgressHandler and override its update and close methods accordingly

class RichProgressHandler(BaseProgressHandler):
    def __init__(self, *args):
        super().__init__(*args)

        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[title]}", justify="right"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            DownloadColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
        )
        self.download_task = self.progress.add_task(
            self.track_title, title=self.track_title, total=self.total_size)
        self.progress.start()

    def update(self):
        self.progress.update(self.download_task,
                             advance=self.current_chunk_size)

    def close(self):
        self.progress.stop()

# When starting a download, pass your ProgressHandler in progress_handler keyword argument.

print("DefaultProgressHandler")
track["download"](download_dir, quality=track_formats.MP3_320)

print()

print("RichProgressHandler")
track["download"](download_dir, quality=track_formats.MP3_320,
                  progress_handler=RichProgressHandler)

```

#### Output

![progresshandlergif](https://media.giphy.com/media/hxxU4CWki3jCICMigm/giphy.gif)

## TODO

- [ ] More CLI features, save used Arls for convenience.
- [ ] Multithreaded downloader (1 song / 1 thread)
- [ ] Binary file
- [ ] GUI

## Disclaimer

I will and should not be held responsible for the usage of this package.

Don't use this package illegaly and against Deezer's [Terms Of Use](https://www.deezer.com/legal/cgu).

This is licensed under [GNU GPL v3](https://choosealicense.com/licenses/gpl-3.0/#).
