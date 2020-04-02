from .search_types import *

# User methods
GET_USER_DATA = "deezer.getUserData"

# Song info
SONG_GET_DATA = "song.getData"
PAGE_TRACK = "deezer.pageTrack"
SONG_GET_LIST_DATA = "song.getListData"
SONG_LYRICS = "song.getLyrics"

# Album info
ALBUM_GET_DATA = "album.getData"
ALBUM_TRACKS = "song.getListByAlbum"

# Artist info
PAGE_ARTIST = "deezer.pageArtist"
ARTIST_DISCOGRAPHY = "album.getDiscography"
ARTIST_TOP_TRACKS = "artist.getTopTrack"

# Playlist info
PAGE_PLAYLIST = "deezer.pagePlaylist"
PLAYLIST_TRACKS = "playlist.getSongs"

# Search Methods
GET_SUGGESTED_QUERIES = "search_getSuggestedQueries"
SEARCH_TRACK = f"search/{TRACK}"
SEARCH_PLAYLIST = f"search/{PLAYLIST}"
SEARCH_PLAYLIST = f"search/{PLAYLIST}"
SEARCH_ALBUM = f"search/{ALBUM}"
SEARCH_ARTIST = f"search/{ARTIST}"
