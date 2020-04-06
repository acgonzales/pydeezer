# PyDeezer

A package to search and download musics on [Deezer](https://www.deezer.com/en/).

## Installation

```bash
pip install py-deezer
```

## Usage

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

You can get the your ```arl``` by manually logging into [Deezer](https://www.deezer.com/) using and check the ```cookies``` and look for the value of ```arl```.

#### Searching

```python
# Some login code here

# Search tracks
track_search_results = deezer.search_tracks("IM DOPE")
# Search albums
album_search_results = deezer.search_albums("DAMN", limit=10)
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

album_id = "39949511"
album = deezer.get_album(album_id) # returns a dict containing data about the album

playlist_id = "1370794195"
playlist = deezer.get_playlist(playlist_id) # returns a dict containing data about the playlist
```



## Disclaimer

I will and should not be held responsible for the usage of this package.

Don't use this package illegaly and against Deezer's [Terms Of Use](https://www.deezer.com/legal/cgu).

This is licensed under [GNU GPL v3](https://choosealicense.com/licenses/gpl-3.0/#).

