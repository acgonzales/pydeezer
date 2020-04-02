# API Urls
DEEZER_URL = "https://www.deezer.com"
API_URL = "https://www.deezer.com/ajax/gw-light.php"
MOBILE_API_URL = "https://api.deezer.com/1.0/gateway.php"
LEGACY_API_URL = "https://api.deezer.com"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36",
    "Content-Language": "en-US",
    "Cache-Control": "max-age=0",
    "Accept": "*/*",
    "Accept-Charset": "utf-8,ISO-8859-1;q=0.7,*;q=0.3",
    "Accept-Language": "en-US,en;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": 'keep-alive'
}

# Image Host
ALBUM_HOST = "https://e-cdns-images.dzcdn.net/images/cover/"
ARTIST_HOST = "https://e-cdns-images.dzcdn.net/images/artist/"

# Search Types
TRACK = "track"
PLAYLIST = "playlist"
ALBUM = "album"
ARTIST = "artist"

# API Methods
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

# Track Formats
FLAC = "flac"
MP3_128 = "mp3-128"
MP3_256 = "mp3-256"
MP3_320 = "mp3-320"
MP4_RA1 = "mp4-ra1"
MP4_RA2 = "mp4-ra2"
MP4_RA3 = "mp4-ra3"

TRACK_FORMAT_MAP = {
    FLAC: {
        "code": 9,
        "ext": ".flac"
    },
    MP3_128: {
        "code": 1,
        "ext": ".mp3"
    },
    MP3_256: {
        "code": 5,
        "ext": ".mp3"
    },
    MP3_320: {
        "code": 3,
        "ext": ".mp3"
    },
    MP4_RA1: {
        "code": 13,
        "ext": ".mp4"
    },
    MP4_RA2: {
        "code": 14,
        "ext": ".mp4"
    },
    MP4_RA3: {
        "code": 15,
        "ext": ".mp3"
    }
}
